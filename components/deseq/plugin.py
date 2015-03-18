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

