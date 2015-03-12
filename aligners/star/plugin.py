import logging
import sys
import os
import imp
import re
import subprocess

# define a custom, descriptive exception:
class IncorrectParameterSubstitutionException(Exception):
	pass

# if anything goes wrong during the alignment process:
class AlignmentScriptErrorException(Exception):
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
		logging.info
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

	execute_alignments(alignment_script_paths)



def execute_alignments(alignment_script_paths):
	"""
	This method starts and monitors the alignment subprocesses.  
	Since STAR is RAM-intensive, jobs are run sequentially instead of in parallel.
	"""
	for script_path in alignment_script_paths:
		os.chmod(script_path, 0774)
		try:
			logging.info('Executing alignment script at: %s' % script_path)
			#subprocess.check_call(script_path, shell = True)
		except subprocess.CalledProcessError:
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
	except:
		logging.error('There was an issue reading the template script.')


def inject_parameter(flag, parameter, template):
	"""
	Ensures that target flag can be substituted into the template.  If it cannot, an exception is raised.
	"""
	# check that the flag is in the template string:
	if len(re.findall(flag, template)) > 0:
		return re.sub(flag, parameter, template)
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
	fileobj, filename, description = imp.find_module(module_name, [location])
	module = imp.load_module(module_name, fileobj, filename, description)
	return module
