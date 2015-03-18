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

	# load the parser and the util_methods modules:
	config_parser = component_utils.load_remote_module('config_parser', utils_dir)
	util_methods = component_utils.load_remote_module('util_methods', utils_dir)

	# parse this module's config file
	component_utils.parse_config_file(project, util_methods, config_parser, os.path.dirname(os.path.realpath(__file__)))

	# create a full path to the output directory for the output and reset the parameter in the project parameters:
	output_dir = os.path.join(project.parameters.get('output_location'), project.parameters.get('normalized_counts_output_dir'))
	project.parameters.reset_param('normalized_counts_output_dir', output_dir)

	# create the final output directory, if possible
	util_methods.create_directory(output_dir)
