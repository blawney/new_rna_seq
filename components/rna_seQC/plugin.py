import logging
import sys
import os
import imp
import subprocess

sys.path.append( os.path.dirname( os.path.dirname( os.path.abspath(__file__) ) ) )

import component_utils


class MissingBamFileException(Exception):
	pass


def run(project):
	logging.info('Beginning rnaSeQC component of pipeline.')

	# get the location of the utils directory:
	utils_dir = project.parameters.get('utils_dir')

	# load the parser and the util_methods modules:
	util_methods = component_utils.load_remote_module('util_methods', utils_dir)

	# parse this module's config file
	component_utils.parse_config_file(project, os.path.dirname(os.path.realpath(__file__)))

	# create a full path to the output directory for rnaseQC's output and reset the parameter in the project parameters:
	output_dir = os.path.join(project.parameters.get('output_location'), project.parameters.get('rnaseqc_output_dir'))
	project.parameters.reset_param('rnaseqc_output_dir', output_dir)

	# create the final output directory, if possible
	util_methods.create_directory(output_dir)

	# run the QC processes:
	run_qc(project)


def run_qc(project, util_methods):

	base_command = 'java -jar ' + project.parameters.get('rnaseqc_jar') 
	base_command +=' -r ' + project.parameters.get('genome_fasta')
	base_command +=' -t ' + project.parameters.get('rnaseqc_gtf')

	for sample in project.samples:
		# only use the most 'raw' bamfile at this point.
		bamfile = get_earliest_version_of_file(sample.bamfiles)
		if os.path.isfile(bamfile):

			# make output directory for this BAM file's QC:
			name = util_methods.case_insensitive_rstrip(os.path.basename(bamfile), 'bam')
			output_dir = os.path.join(project.parameters.get('rnaseqc_output_dir'), name)
			util_methods.create_directory(output_dir)

			arg = '"' + sample.sample_name + '|' + bamfile + '|-"'

			command = base_command + ' -o ' + output_dir + ' -s ' + arg

			logging.info('Calling rnaSeQC with: ')
			logging.info(command)
			process = subprocess.Popen(command, shell = True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

			stdout, stderr = process.communicate()
			logging.info('STDOUT from rna-SeQC: ')
			logging.info(stdout)
			logging.info('STDERR from rna-SeQC: ')
			logging.info(stderr)
	
			if process.returncode != 0:			
				logging.error('There was an error encountered during execution of rna-SeQC for sample %s ' % sample.sample_name)
				raise Exception('Error during rna-SeQC module.')

		else:
			logging.error('The bamfile (%s) is not actually a file.' % bamfile)
			raise MissingBamFileException('Missing BAM file: %s' % bamfile)



def get_earliest_version_of_file(file_list):
	"""
	Takes a list of file paths.  Returns the path with the earliest modification date
	"""

	times = [ os.path.getmtime(x) for x in file_list ]
	earliest_time = times[0]
	earliest_index = 0
	for i,t in enumerate(times):
		if t < earliest_time:
			earliest_time = t
			earliest_index = i
	return file_list[earliest_index]
	

