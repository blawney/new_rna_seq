import logging
import sys
import os
import imp
import subprocess
import pandas as pd
from collections import defaultdict

sys.path.append( os.path.dirname( os.path.dirname( os.path.abspath(__file__) ) ) )

import component_utils


class AmbiguousGseaOutputException(Exception):
	pass


class NormalizedCountFileNotFoundException(Exception):
	pass


def run(name, project):
	logging.info('Beginning GSEA component.')

	# get the location of the utils directory:
	utils_dir = project.parameters.get('utils_dir')

	# load the parser and the util_methods modules:
	util_methods = component_utils.load_remote_module('util_methods', utils_dir)

	# parse this module's config file
	this_dir = os.path.dirname(os.path.realpath(__file__))
	project.parameters.add(component_utils.parse_config_file(project, this_dir))
	component_params = component_utils.parse_config_file(project, this_dir, 'COMPONENT_SPECIFIC')

	# create a full path to the output directory for GSEA's output:
	output_dir = os.path.join(project.parameters.get('output_location'), component_params.get('gsea_output_dir'))
	component_params.reset_param('gsea_output_dir', output_dir)	


	# create the final output directory, if possible
	util_methods.create_directory(output_dir)

	# create the cls and gct files for input to GSEA:
	create_input_files(project, component_params)

	# run it:
	output = run_gsea(project, component_params, util_methods)

	return [component_utils.ComponentOutput(output, component_params.get('tab_title'), component_params.get('header_msg'), component_params.get('display_format')),]



def create_input_files(project, component_params):
	'''
	Create the .cls and .gct files necessary for input to GSEA
	'''

	# first create the cls file
	cls_filepath = os.path.join(component_params.get('gsea_output_dir'), component_params.get('cls_file'))
	
	# create a dictionary mapping the condition to the corresponding samples:
	condition_to_sample_map = defaultdict(list)
	for sample in project.samples:
		condition_to_sample_map[sample.condition].append(sample.sample_name)

	# a sorted list of the conditions featured in this experiment
	conditions = sorted(condition_to_sample_map.keys())
	
	# build a string for the file contents and write it to the CLS file
	cls_contents = ""
	cls_contents += "\t".join([str(len(project.samples)), len(conditions), '1']) + "\n"
	cls_contents += "\t".join(["#"] + conditions) + "\n"
	cls_contents += "\t".join(["\t".join([k]*len(condition_to_sample_map[k])) for k in conditions])
	with open(cls_filepath, 'w') as cls:
		cls.write(cls_contents)

	
	# read in the normalized expression matrix
	exp_mtx = [p for p in project.normalized_count_matrices if p.endswith(component_params.get('normalized_count_target'))]
	if len(exp_mtx) == 1:
		expression_data = pd.read_table(exp_mtx[0], sep = '\t')
		
		# do not want to assume if the first column (the gene symbols) has any particular naming convention.  Simply rename it here
		gene_col_name = 'gene'
		expression_data.rename(columns = {expression_data.columns[0]:gene_col_name}, inplace = True)
		
		# add the Description column for the gct format:
		desc_col = 'Description'
		expression_data[desc_col] = 'NA'
		
		# order the columns of the matrix to match the cls file and add the new first column at the beginning:
		ordered_cols = reduce(lambda x,y: x+y, [d[c] for c in conditions])
		ordered_cols.insert(0, gene_col_name)
		ordered_cols.insert(1, desc_col)
		
		# now use this list to re-order the columns of the exp matrix:
		expression_data = expression_data[ordered_cols]

		with open(component_params.get('gct_file')) as gct_out:
			intro_lines = '#1.2\n'
			intro_lines += str(expression_data.shape[0]) + '\t' + str(expression_data.shape[1]-2) + '\n'
			gct_out.write(intro_lines)
			expression_data.to_csv(gct_out, sep='\t', index = False)
	else:
		raise NormalizedCountFileNotFoundException('Could not find the normalized count file to use, or found more than 1, so ambiguous')


def run_gsea(project, component_params, util_methods):
	
	output_reports = {}

	# construct the base command:
	base_cmd = 'java -cp ' + component_params.get('gsea_jar') + ' -Xmx1024m'
	base_cmd += ' ' + component_params.get('gsea_analysis')
	base_cmd += ' -res ' + component_params.get('gct_file')
	base_cmd += ' -gmx ' + component_params.get('default_gmx_file')
	base_cmd += ' -chip ' + component_params.get('default_chip_file')
	base_cmd += ' -nperm ' + component_params.get('permutation_count')
	base_cmd += ' -out ' + component_params.get('gsea_output_dir')
	base_cmd += ' -collapse false'
	base_cmd += ' -mode Max_probe'
	base_cmd += ' -norm meandiv'
	base_cmd += ' -permute gene_set'
	base_cmd += ' -rnd_type no_balance'
	base_cmd += ' -scoring_scheme weighted'
	base_cmd += ' -metric Signal2Noise'
	base_cmd += ' -sort real'
	base_cmd += ' -order descending'
	base_cmd += ' -include_only_symbols true'
	base_cmd += ' -make_sets true'
	base_cmd += ' -median false'
	base_cmd += ' -num 100'
	base_cmd += ' -plot_top_x 20'
	base_cmd += ' -rnd_seed timestamp'
	base_cmd += ' -save_rnd_lists false'
	base_cmd += ' -set_max 50000'
	base_cmd += ' -set_min 15'
	base_cmd += ' -zip_report false'
	base_cmd += ' -gui false'

	for contrast_pair in project.contrasts:
		ctrl_condition = contrast_pair[0]
		exp_condition = contrast_pair[1]

		contrast_string = ctrl_condition + '_versus_' + exp_condition
		report_label = ctrl_condition + component_params.get('gsea_contrast_flag') + exp_condition

		cmd = base_cmd 
		cmd += ' -cls ' + component_params.get('cls_file') + '#' + contrast_string
		cmd += ' -rpt_label ' + report_label
		
		logging.info('Calling GSEA with: ')
		logging.info(cmd)
		process = subprocess.Popen(cmd, shell = True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)

		stdout, stderr = process.communicate()
		logging.info('STDOUT from GSEA: ')
		logging.info(stdout)
		logging.info('STDERR from GSEA: ')
		logging.info(stderr)
	
		if process.returncode != 0:			
			logging.error('There was an error encountered during execution of rna-SeQC for sample %s ' % sample.sample_name)
			raise Exception('Error during GSEA module.')
		else:
			report_path_pattern = os.path.join(component_params.get('gsea_output_dir'), report_label + '*', component_params.get('gsea_default_html'))
			report_path = glob.glob(report_path_pattern)
			if len(report_path) == 1:
				output_reports[contrast_string] = report_path[0]
			else:
				raise AmbiguousGseaOutputException('Could not find or uniquely identify a GSEA output for the following contrast: %s' % contrast_string)
	return output_reports
