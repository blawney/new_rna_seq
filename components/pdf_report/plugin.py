import logging
import sys
import os
import imp
import subprocess

sys.path.append( os.path.dirname( os.path.dirname( os.path.abspath(__file__) ) ) )

import component_utils

def run(name, project):
	logging.info('Beginning creation of custom latex report')

	# get the location of the utils directory:
	utils_dir = project.parameters.get('utils_dir')

	# load the util_methods module:
	util_methods = component_utils.load_remote_module('util_methods', utils_dir)

	# parse this module's config file
	this_dir = os.path.dirname(os.path.realpath(__file__))
	project.parameters.add(component_utils.parse_config_file(project, this_dir))
	component_params = component_utils.parse_config_file(project, this_dir, 'COMPONENT_SPECIFIC')

	# create a full path to the output directory for the output:
	output_dir = os.path.join(project.parameters.get('output_location'), component_params.get('report_output_dir'))
	component_params['report_output_dir']  = output_dir 

	# create the final output directory, if possible
	util_methods.create_directory(output_dir, overwrite = True)

	output_file = create_report(project, component_params)

	# change permissions:
	os.chmod(output_file, 0775)

	# create the ComponentOutput object and return it
	c1 = component_utils.ComponentOutput(output_file, component_params.get('report_tab_title'), component_params.get('report_header_msg'), component_params.get('report_display_format'))
	return [ c1 ]


def create_report(project, component_params):
	# returns a dict of file name mapping (e.g. what is displayed as the href element) to the file path

	generate_figures(project, component_params)

	compile_report(project, component_params)

	return {}


def generate_figures(project, component_params):
	if project.parameters.get('aligner') == 'star':
		process_star_logs(project, component_params)
	#TODO: else?  throw exception?


def compile_report(project, component_params):
	pass



def process_star_logs(project, component_params):
	def get_log_contents(f):
		"""
		Parses the star-created Log file to get the mapping stats
		"""
		d = {}
		for line in open(f):
			try:
				key, val = line.strip().split('|')
				d[key.strip()] = val.strip()
			except ValueError as ex:
				pass
		return d


	#TODO: get a list of the log file pahts
	d = {}
		for log in aln_log_paths:
			sample = os.path.basename(log)[:-len(suffix)]
			d[sample] = get_log_contents(log)
	return d
