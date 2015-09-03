import logging
import sys
import os
import imp
import subprocess
import numpy as np
import pandas as pd

sys.path.append( os.path.dirname( os.path.dirname( os.path.abspath(__file__) ) ) )

import component_utils

class NoCountMatricesException(Exception):
	pass

class MissingCountMatrixFileException(Exception):
	pass


def run(name, project):
	logging.info('Beginning DESeq differential expression analysis...')

	# get the location of the utils directory:
	utils_dir = project.parameters.get('utils_dir')

	# load the util_methods module:
	util_methods = component_utils.load_remote_module('util_methods', utils_dir)

	# parse this module's config file
	this_dir = os.path.dirname(os.path.realpath(__file__))
	project.parameters.add(component_utils.parse_config_file(project, this_dir))
	component_params = component_utils.parse_config_file(project, this_dir, 'COMPONENT_SPECIFIC')

	# create a full path to the output directory for the output:
	output_dir = os.path.join(project.parameters.get('output_location'), component_params.get('deseq_output_dir'))
	component_params['deseq_output_dir']  = output_dir 

	# create the final output directory, if possible
	util_methods.create_directory(output_dir, overwrite = True)

	deseq_output_files, heatmap_files = call_deseq(project, component_params)

	# write a summary of the number of differentially expressed genes
	create_diff_exp_summary(deseq_output_files)

	# change permissions:
	[os.chmod(f,0775) for f in deseq_output_files.values()]
	[os.chmod(f,0775) for f in heatmap_files.values()]

	# create the ComponentOutput object and return it
	c1 = component_utils.ComponentOutput(deseq_output_files, component_params.get('deseq_tab_title'), component_params.get('deseq_header_msg'), component_params.get('deseq_display_format'))
	c2 = component_utils.ComponentOutput(heatmap_files, component_params.get('heatmap_tab_title'), component_params.get('heatmap_header_msg'), component_params.get('heatmap_display_format'))
	return [ c1, c2 ]


def create_diff_exp_summary(deseq_files, project, component_params):
	summary_filepath = os.path.join(component_params.get('deseq_output_dir'), component_params.get('summary_file'))
	project.diff_exp_summary_filepath = summary_filepath
	with open(summary_filepath, 'w') as outfile:
		for f in deseq_files.values():
			exp_condition, ctrl_condition = os.path.basename(f).split('.')[0].split(component_params.get('deseq_contrast_flag'))

			# load the data and count
			data = pd.read_table(f, sep=',')
			downreg_count = np.sum((data['padj']<=0.05) & (data['log2FoldChange'] < 0))
			upreg_count = np.sum((data['padj']<=0.05) & (data['log2FoldChange'] > 0))
			outfile.write('\t'.join([ctrl_condition, exp_condition, str(upreg_count), str(downreg_count)]) + '\n')


def call_deseq(project, component_params):
	"""
	Creates the calls and executes the system calls for running the DGE analysis
	"""
	deseq_output_files = {}
	heatmap_files = {}
	try:
		# there is one count matrix per 'type' of BAM file (e.g. counts for deduped, deduped+primary filtered, etc.)
		for count_matrix_filepath in project.raw_count_matrices:
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
					contrast_prefix = exp_condition + component_params.get('deseq_contrast_flag') + ctrl_condition
					contrast_base =  contrast_prefix + base
					output_deseq_file = os.path.join(component_params.get('deseq_output_dir'), contrast_base + component_params.get('deseq_output_tag'))
					output_deseq_heatmap = os.path.join(component_params.get('deseq_output_dir'), contrast_base + component_params.get('heatmap_file_tag'))

					args = [count_matrix_filepath, 
							project.parameters.get('sample_annotation_file'), 
							ctrl_condition, 
							exp_condition, 
							output_deseq_file, 
							output_deseq_heatmap, 
							component_params.get('number_of_genes_for_heatmap')]
					arg_string = ' '.join(args)

					call_script(component_params.get('deseq_script'), arg_string)
					deseq_output_files[contrast_base[:-1]] = output_deseq_file # [:-1] removes the trailing dot '.'
					heatmap_files[contrast_base[:-1]] = output_deseq_heatmap # [:-1] removes the trailing dot '.'
			else:
				logging.error('Error in finding the count matrices.  There is no file located at %s' % count_matrix_filepath)
				raise MissingCountMatrixFileException('No file at %s' % count_matrix_filepath)
		return (deseq_output_files, heatmap_files)
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

