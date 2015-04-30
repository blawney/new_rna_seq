import logging
import sys
import os
import imp
import subprocess

sys.path.append( os.path.dirname( os.path.dirname( os.path.abspath(__file__) ) ) )

import component_utils

class NoCountMatricesException(Exception):
	pass

class MissingCountMatrixFileException(Exception):
	pass


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
		# there is one count matrix per 'type' of BAM file (e.g. counts for deduped, deduped+primary filtered, etc.)
		for count_matrix_filepath in project.count_matrices:
			if os.path.isfile(count_matrix_filepath):
				logging.info('Located raw count matrix at %s ' % count_matrix_filepath)
				base = os.path.basename(count_matrix_filepath)

				# a raw count file might have a name like 'raw_count_matrix.sorted.primary.dedup.counts'
				# these operations trim the ends so we are left with '.sorted.primary.dedup.' (note the leading and trailing dots)
				base = base.lstrip(project.parameters.get('raw_count_matrix_file_prefix'))
				base = base.rstrip(project.parameters.get('feature_counts_file_extension'))

				for contrast_pair in project.contrasts:
					ctrl_condition = contrast_pair[0]
					exp_condition = contrast_pair[1]

					# construct the full path to the output deseq file and heatmap file
					contrast_prefix = exp_condition + project.parameters.get('deseq_contrast_flag') + ctrl_condition 
					output_deseq_file = os.path.join(project.parameters.get('deseq_output_dir'), contrast_prefix + base + project.parameters.get('deseq_output_tag'))
					output_deseq_heatmap = os.path.join(project.parameters.get('deseq_output_dir'), contrast_prefix + base + project.parameters.get('heatmap_file_tag'))

					args = [count_matrix_filepath, 
							project.parameters.get('sample_annotation_file'), 
							ctrl_condition, 
							exp_condition, 
							output_deseq_file, 
							output_deseq_heatmap, 
							project.parameters.get('number_of_genes_for_heatmap')]
					arg_string = ' '.join(args)

					call_script(project.parameters.get('deseq_script'), arg_string)
			else:
				logging.error('Error in finding the count matrices.  There is no file located at %s' % count_matrix_filepath)
				raise MissingCountMatrixFileException('No file at %s' % count_matrix_filepath)
	except AttributeError:
		logging.error('The project does not have any count matrices that can be located.')
		raise NoCountMatricesException()



def call_script(script, arg_string):
	"""
	Receives the name of the script to call and the cmd line args to call the script with.
	The command line args are expected to already be formatted-- e.g. properly spaced/separated, etc.
	"""

	# full path to the script
	script = os.path.join(os.path.dirname(os.path.realpath(__file__)), script)

	command = 'Rscript ' + script + ' ' + arg_string

	logging.info('Calling DESeq script: ')
	logging.info(command)
	process = subprocess.Popen(command, shell = True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
	stdout, stderr = process.communicate()

	logging.info('STDOUT from DESeq script: ')
	logging.info(stdout)
	logging.info('STDERR from DESeq script: ')
	logging.info(stderr)
		
	if process.returncode != 0:			
		logging.error('There was an error while calling the R script for DESeq.  Check the logs.')
		raise Exception('Error during normalization module.')

