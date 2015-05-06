import logging
import sys
import os
import imp
import re
import subprocess
from time import sleep
import glob


# define a custom, descriptive exception:
class IncorrectParameterSubstitutionException(Exception):
	pass

# if anything goes wrong during the alignment process:
class AlignmentScriptErrorException(Exception):
	pass

# in case the script never gets a chance to run due to memory-restricted 'lockouts'
class AlignmentTimeoutException(Exception):
	pass

# in case BAM files were not found after alignment
class BAMFileNotFoundException(Exception):
	pass


def run(project):
	"""
	The main entry method for the module
	Takes in a Project object, which contains all the relevant information to perform the alignments
	"""

	# get the location of the utils directory:
	utils_dir = project.parameters.get('utils_dir')

	# load the parser and the util_methods modules:
	config_parser = load_remote_module('config_parser', utils_dir)
	util_methods = load_remote_module('util_methods', utils_dir)

	# parse the configuration file
	parse_config_file(project, util_methods, config_parser)

	logging.info('After parsing STAR configuration file, the parameters dictionary is: ')
	logging.info(project.parameters)

	# read the template into a string object:
	template_string = get_template(project.parameters.get('template_script'))

	# inject the general (non sample-specific) parameters into the template script:
	general_template_string = fill_out_general_template_portion(project, template_string)
	
	alignment_script_paths = []
	for sample in project.samples:
		# extract the path to the sample directory via the fastq file:
		sample_dir_path = os.path.dirname(sample.read_1_fastq)
		
		# define, create, and assign the path to the alignment output directory:
		align_dir_path = os.path.join(sample_dir_path, project.parameters.get('alignment_dir'))
		util_methods.create_directory(align_dir_path)
		sample.alignment_dir = align_dir_path # note assigning member attribute to this sample

		# fill out the remainder of the script template and write to the sample directory:
		align_script_string = fill_out_sample_specific_portion(sample, general_template_string)
		align_script_path = os.path.join(sample_dir_path, sample.sample_name + '.star_align.sh')
		with open(align_script_path, 'w') as outfile:
			outfile.write(align_script_string)
		alignment_script_paths.append(align_script_path)

	execute_alignments(alignment_script_paths, project.parameters)
	register_bam_files(project, util_methods.case_insensitive_glob)



def register_bam_files(project, glob_method):
	"""
	This finds all the bam files created by the alignment step and adds them to the respective Sample objects
	"""
	logging.info('Registering BAM files with their respective samples')
	for sample in project.samples:
		bam_files = glob_method(os.path.join(sample.alignment_dir, '*bam'))
		logging.info('For sample %s, found: %s' % (sample.sample_name, bam_files))
		if len(bam_files) > 0:
			sample.bamfiles = bam_files
		else:
			logging.info('Could not find any BAM files in %s. ' % sample.alignment_dir)
			raise BAMFileNotFoundException



def assert_memory_reasonable(min_mem_necessary):
	"""
	This method does a dirty check on the system memory to see that there is a reasonable amount of RAM avaialable
	"""
	try:
		# the memory is passed in GB- we need to compare to MB, so multiply by 1000:
		min_mem_necessary = float(min_mem_necessary)* 1000
		call = 'free -m -o'
		output = subprocess.Popen(call, shell=True, stdout=subprocess.PIPE)
		for line in output.stdout:
			if line.startswith('Mem:'):
				text,total,used,free,shared,buffers,cached = line.strip().split()
				break
	
		available = int(free) + int(cached)
		if available > min_mem_necessary:
			return True
		else:
			logging.info('Via parsing "free" output, it seems there is less than %s MB of RAM available.' % min_mem_necessary)
			return False
	except ValueError:
		logging.error('Could not convert the "memory" argument parsed from the STAR config file as a float.')
		raise ex
	except Exception as ex:
		logging.error('Some exception occurred while inspecting the system memory for sufficient capacity.')
		raise ex


def execute_alignments(alignment_script_paths, params):
	"""
	This method starts and monitors the alignment subprocesses.  
	Since STAR is RAM-intensive, jobs are run sequentially instead of in parallel.
	"""
	try: 
		sleeptime = 60 * float(params.get('wait_length'))
	except ValueError as ex:
		logging.error('Could not parse one of the arguments from the configuration file as the proper number:')
		logging.error(ex.message)
		raise ex 

	for script_path in alignment_script_paths:
		attempt_counter = 0
		os.chmod(script_path, 0774)
		while True: 
			if assert_memory_reasonable(params.get('min_memory')):
				logging.info('Executing alignment script at: %s' % script_path)
				process = subprocess.Popen(script_path, shell = True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
				break				
			elif attempt_counter < int(params.get('wait_cycles')):
				logging.info('Since memory was not adequate to run STAR, wait for %s minutes' % params.get('wait_length'))
				logging.info('This is attempt number %s on running the script at %s' % (attempt_counter + 1, script_path))
				attempt_counter += 1
				sleep(sleeptime)
			else:
				logging.warning('After waiting for %s periods of %s minutes each, still could not get enough reasonable memory to run STAR.')
				raise AlignmentTimeoutException('Timeout on running the script at %s' % script_path)
				
		stdout, stderr = process.communicate()
		logging.info('STDOUT from script at %s' % script_path)
		logging.info(stdout)
		logging.info('STDERR from script at %s' % script_path)
		logging.info(stderr)
		
		if process.returncode != 0:			
			logging.error('The STAR alignment process had non-zero exit status. Check the log for details.')
			raise AlignmentScriptErrorException('Error during STAR alignment')




def get_template(script_name):
	"""
	Reads the template script into a string object (if the file is available). Returns the string
	"""

	this_directory = os.path.dirname(os.path.realpath(__file__))
	template_path = os.path.join(this_directory, script_name)
	try:
		logging.info('Attempting to read template script file at %s' % template_path)
		return open(template_path).read()
	except Exception as ex:
		logging.error('There was an issue reading the template script at %s' % template_path)
		raise ex


def inject_parameter(flag, parameter, template):
	"""
	Ensures that target flag can be substituted into the template.  If it cannot, an exception is raised.
	"""
	# check that the flag is in the template string:
	if len(re.findall(flag, template)) > 0:
		return re.sub(flag, str(parameter), template)
	else:
		logging.error('Could not locate the flag "%s" in the template script.  ' % flag)
		raise IncorrectParameterSubstitutionException('Could not locate the flag "%s" in the template script.  ' % flag)



def fill_out_sample_specific_portion(sample, sample_template):
	"""
	Fills in the sample-specific portions of the template string
	"""

	sample_template = inject_parameter('%SAMPLE_NAME%', sample.sample_name, sample_template)
	sample_template = inject_parameter('%OUTDIR%', sample.alignment_dir, sample_template)
	sample_template = inject_parameter('%FCID%', sample.flowcell_id, sample_template)
	sample_template = inject_parameter('%LANE%', sample.lane, sample_template)
	sample_template = inject_parameter('%INDEX%', sample.index, sample_template)

	sample_template = inject_parameter('%FASTQFILEA%', sample.read_1_fastq, sample_template)
	if sample.read_2_fastq:
		sample_template = inject_parameter('%PAIRED%', '1', sample_template)
		sample_template = inject_parameter('%FASTQFILEB%', sample.read_2_fastq, sample_template)
	else:
		sample_template = inject_parameter('%PAIRED%', '0', sample_template)
		sample_template = inject_parameter('%FASTQFILEB%', '', sample_template)
	return sample_template



def fill_out_general_template_portion(project, template_string):
	"""
	Replaces the flags in the template script (a string) with the appropriate parameters
	"""

	#inject parameters common to alignment template scripts:
	template_string = inject_parameter('%STAR%', project.parameters.get('star_align'), template_string)
	template_string = inject_parameter('%SAMTOOLS%', project.parameters.get('samtools'), template_string)
	template_string = inject_parameter('%PICARD_DIR%', project.parameters.get('picard'), template_string)
	template_string = inject_parameter('%GTF%', project.parameters.get('gtf'), template_string)
	template_string = inject_parameter('%GENOME_INDEX%', project.parameters.get('star_genome_index'), template_string)

	return template_string



def parse_config_file(project, util_methods, config_parser):

	# parse out the genome-specific info from the config file in this directory.
	# this picks out the default parameters plus the genome-specific ones
	this_directory = os.path.dirname(os.path.realpath(__file__))
	config_filepath = util_methods.locate_config(this_directory)
	project.parameters.add(config_parser.read_config(config_filepath, section = project.parameters.get('genome')))



def load_remote_module(module_name, location):
	"""
	Loads and returns the module given by 'module_name' that resides in the given location
	"""
	sys.path.append(location)
	try:
		fileobj, filename, description = imp.find_module(module_name, [location])
		module = imp.load_module(module_name, fileobj, filename, description)
		return module
	except ImportError as ex:
		logging.error('Could not import module %s at location %s' % (module_name, location))
		raise ex
