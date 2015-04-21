import logging
import sys
import os
import imp
import subprocess

sys.path.append( os.path.dirname( os.path.dirname( os.path.abspath(__file__) ) ) )

import component_utils

def run(project):

	# get the location of the utils directory:
	utils_dir = project.parameters.get('utils_dir')

	# load the util_methods module:
	util_methods = component_utils.load_remote_module('util_methods', utils_dir)

	# parse this module's config file
	component_utils.parse_config_file(project, os.path.dirname(os.path.realpath(__file__)))

	# create a full path to the output directory for the output and reset the parameter in the project parameters:
	output_dir = os.path.join(project.parameters.get('output_location'), project.parameters.get('deseq_output_dir'))
	project.parameters.reset_param('deseq_output_dir', output_dir)

	# create the final output directory, if possible
	util_methods.create_directory(output_dir)

	call_deseq(project)


def call_deseq(project):
	"""
	Creates the calls and executes the system calls for running the DGE analysis
	"""
	try:
		for count_matrix_filepath in project.count_matrices:
			if os.path.isfile(count_matrix_filepath):
				logging.info('Located raw count matrix at %s ' % count_matrix_filepath)
				base = os.path.basename(count_matrix_filepath)

				# a raw count file might have a name like 'raw_count_matrix.sorted.primary.dedup.counts'
				# these operations trim the ends so we are left with '.sorted.primary.dedup.' (note the dots)
				base = base.lstrip(project.parameters.get('raw_count_matrix_file_prefix'))
				base = base.rstrip(project.parameters.get('feature_counts_file_extension'))

				# TODO: write this call-->
				call_script(project.parameters.get('deseq_script'), 
					count_matrix_filepath, 
					normalized_filepath, 
					project.parameters.get('sample_annotation_file'))
			else:
				logging.error('Error in finding the count matrices.  There is no file located at %s' % count_matrix_filepath)
				raise MissingCountMatrixFileException('No file at %s' % count_matrix_filepath)
	except AttributeError:
		logging.error('The project does not have any count matrices that can be located.')
		raise NoCountMatricesException()



# TODO: write this~!!
def call_script(script, inputfile, outputfile, annotation_file):

	# full path to the script
	script = os.path.join(os.path.dirname(os.path.realpath(__file__)), script)
	command = 'Rscript ' + script + ' ' + inputfile + ' ' + outputfile + ' ' + annotation_file

	logging.info('Calling DESeq script: ')
	logging.info(command)
	process = subprocess.Popen(command, shell = True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
	stdout, stderr = process.communicate()

	logging.info('STDOUT from normalization script: ')
	logging.info(stdout)
	logging.info('STDERR from normalization script: ')
	logging.info(stderr)
		
	if process.returncode != 0:			
		logging.error('There was an error while calling the R script for normalization.  Check the logs.')
		raise Exception('Error during normalization module.')
