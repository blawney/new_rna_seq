import logging
import sys
import os
import imp
import subprocess
import re

# to import from the parent directory, append to sys.path
sys.path.append( os.path.dirname( os.path.dirname( os.path.abspath(__file__) ) ) )
import component_utils

class NoCountMatricesException(Exception):
	pass

class MissingCountMatrixFileException(Exception):
	pass

def run(name, project):

	# get the location of the utils directory:
	utils_dir = project.parameters.get('utils_dir')

	# load the util_methods module:
	util_methods = component_utils.load_remote_module('util_methods', utils_dir)

	# parse this module's config file
	this_dir = os.path.dirname(os.path.realpath(__file__))
	project.parameters.add(component_utils.parse_config_file(project, this_dir))
	component_params = component_utils.parse_config_file(project, this_dir, 'COMPONENT_SPECIFIC')

	# create a full path to the output directory for the output and reset the parameter in the project parameters:
	output_dir = os.path.join(project.parameters.get('output_location'), component_params.get('normalized_counts_output_dir'))
	component_params['normalized_counts_output_dir'] = output_dir

	# create the final output directory, if possible
	util_methods.create_directory(output_dir, overwrite = True)

	# perform the actual normalization:
	output_files = normalize(project, component_params)
	
	# create the ComponentOutput object and return it
	return [component_utils.ComponentOutput(output_files, component_params.get('tab_title'), component_params.get('header_msg'), component_params.get('display_format')),]



def normalize(project, component_params):
	"""
	Creates the calls and executes the system calls for running the normalization
	"""
	output_files = {}
	normalized_count_files = []
	try:
		for count_matrix_filepath in project.raw_count_matrices:
			if os.path.isfile(count_matrix_filepath):
				logging.info('Located raw count matrix at %s ' % count_matrix_filepath)
				base = os.path.basename(count_matrix_filepath)
				normalized_filename = re.sub(project.parameters.get('raw_count_matrix_file_prefix'), 
							component_params.get('normalized_counts_file_prefix'), base)
				normalized_filepath = os.path.join(component_params.get('normalized_counts_output_dir'), normalized_filename)
				call_script(component_params.get('normalization_script'), 
					count_matrix_filepath, 
					normalized_filepath, 
					project.parameters.get('sample_annotation_file'))
				output_files[normalized_filename] = normalized_filepath
				normalized_count_files.append(normalized_filepath)
			else:
				logging.error('Error in finding the count matrices.  There is no file located at %s' % count_matrix_filepath)
				raise MissingCountMatrixFileException('No file at %s' % count_matrix_filepath)
		project.normalized_count_matrices = normalized_count_files
		return output_files
	except AttributeError:
		logging.error('The project does not have any count matrices that can be located.')
		raise NoCountMatricesException()	


def call_script(script, inputfile, outputfile, annotation_file):

	# full path to the script
	script = os.path.join(os.path.dirname(os.path.realpath(__file__)), script)
	command = 'Rscript ' + script + ' ' + inputfile + ' ' + outputfile + ' ' + annotation_file

	logging.info('Calling normalization script: ')
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



