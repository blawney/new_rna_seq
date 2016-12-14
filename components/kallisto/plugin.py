import logging
import sys
import os
import imp
import subprocess
import pandas as pd

sys.path.append( os.path.dirname( os.path.dirname( os.path.abspath(__file__) ) ) )

import component_utils


class MissingBamFileException(Exception):
	pass


def run(name, project):
	logging.info('Beginning Kallisto/Sleuth.')

	# get the location of the utils directory:
	utils_dir = project.parameters.get('utils_dir')

	# load the parser and the util_methods modules:
	util_methods = component_utils.load_remote_module('util_methods', utils_dir)

	# parse this module's config file
	this_dir = os.path.dirname(os.path.realpath(__file__))
	project.parameters.add(component_utils.parse_config_file(project, this_dir))
	component_params = component_utils.parse_config_file(project, this_dir, 'COMPONENT_SPECIFIC')
	component_params.update( component_utils.parse_config_file(project, this_dir, project.parameters.get('genome')))

	# create a full path to the output directory for kallisto's output, and reassign the variable:
	output_dir = os.path.join(project.parameters.get('output_location'), component_params.get('kallisto_output_dir'))
	logging.info('Will output kallisto files to %s' % output_dir)
	component_params['kallisto_output_dir'] = output_dir

	# create the final output directory, if possible
	util_methods.create_directory(output_dir, overwrite = True)

	# run kallisto:
	abundance_files = run_kallisto(project, component_params, util_methods)

	# run Sleuth:
	sleuth_files = run_sleuth(project, component_params, util_methods)

	all_output_files = abundance_files
	all_output_files.update(sleuth_files)

	return [component_utils.ComponentOutput(all_output_files, component_params.get('tab_title'), component_params.get('header_msg'), component_params.get('display_format')),]





def run_kallisto(project, component_params, util_methods):
	"""
	./kallisto quant -i Mus_musculus.GRCm38.rel79.cdna.all.idx -o SH1_1_output --single -l 350 -s 100 -t 16 -b 100 /cccbstore-rc/projects/cccb/projects/2016/6/SH_06062016_1098/Sample_SH1_1/SH1_1_R1_.final.fastq.gz	
	"""
	output_file_dict = {}

	single_protocol_base_command = '%s quant -i %s -o %s -t %s -b %d --single -l %s -s %s'
	paired_protocol_base_command = '%s quant -i %s -o %s -t %s -b %d '

	index = component_params.get('kallisto_idx')
	kallisto_path = component_params.get('kallisto_path')
	threads = component_params.get('threads')
	bootstraps = component_params.get('bootstraps')
	base_command = '%s quant -i %s -t %s -b %d ' % (kallisto_path, index, threads, int(bootstraps))

	strand_flag = component_params.get('strand_flag')
	if strand_flag:
		base_command += '%s ' % strand_flag 

	if project.parameters.get('paired_alignment'):
		paired = True
	else:
		paired = False
		fragment_length = int(component_params.get('fragment_length'))
		fragment_stdev = int(component_params.get('fragment_stdev'))
		base_cmd = base_command + '--single -l %s -s %s ' % (fragment_length, fragment_stdev)

	for sample in project.samples:
		sample_name = sample.sample_name
		outfile_dir = os.path.join(component_params.get('kallisto_output_dir'), sample_name)
		cmd = '%s -o %s ' % (base_cmd, outfile_dir)
		if paired:
			cmd += '%s %s' % (sample.read_1_fastq, sample.read_2_fastq)
		else:
			cmd += '%s' % sample.read_1_fastq			
		logging.info('Calling Kallisto with: ')
		logging.info(cmd)
		process = subprocess.Popen(cmd, shell = True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
		stdout, stderr = process.communicate()
		logging.info('STDOUT from Kallisto: ')
		logging.info(stdout)
		logging.info('STDERR from Kallisto: ')
		logging.info(stderr)
		if process.returncode != 0:			
			logging.error('There was an error encountered during execution of Kallisto for sample %s ' % sample.sample_name)
			raise Exception('Error during Kallisto module.')
		report_path = os.path.join(outfile_dir, component_params.get('kallisto_result_filename'))
		output_file_dict[sample_name] = report_path
	return output_file_dict


def run_sleuth(project, component_params, util_methods):

	# need to make a design file with 3 columns.  
	# condition, path to kallisto results, and sample ID
	# there needs to be a column named 'condition'
	conditions = [s.condition for s in project.samples]
	names = [s.sample_name for s in project.samples]
	paths = [os.path.join(component_params.get('kallisto_output_dir'), s.sample_name) for s in project.samples]
	design = pd.DataFrame({'condition': conditions, 'path': paths, 'sample': names})
	design_filepath = os.path.join(component_params.get('kallisto_output_dir'), component_params.get('sleuth_design_filename'))
	design.to_csv(design_filepath, sep='\t', index=False)


	# full path to the script
	script = os.path.join(os.path.dirname(os.path.realpath(__file__)), component_params.get('sleuth_script'))
	sleuth_result_file = os.path.join(component_params.get('kallisto_output_dir'), component_params['sleuth_result_filename'])

	arg_string = ' '.join([design_filepath,
				component_params.get('mapping_dataset'),
				component_params.get('mapping_version'),
				sleuth_result_file])

	#command = 'Rscript ' + script + ' ' + arg_string
	command = ' '.join([component_params.get('rscript_path'), script, arg_string])

	logging.info('Calling sleuth script: ')
	logging.info(command)
	process = subprocess.Popen(command, shell = True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
	stdout, stderr = process.communicate()

	logging.info('STDOUT from sleuth script: ')
	logging.info(stdout)
	logging.info('STDERR from sleuth script: ')
	logging.info(stderr)
		
	if process.returncode != 0:			
		logging.error('There was an error while calling the R script for Sleuth.  Check the logs.')
		raise Exception('Error during Kallisto/Sleuth module.')


	return {component_params.get('sleuth_result_filename'): sleuth_result_file}
