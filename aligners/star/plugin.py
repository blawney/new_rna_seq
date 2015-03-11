import logging
import sys
import os
import imp

def run(project):

	# parse the configuration file
	parse_config_file(project)

	logging.info('After parsing STAR configuration file: ')
	logging.info(project.parameters)


def parse_config_file(project):

	# get the location of the utils directory:
	utils_dir = project.parameters.get('utils_dir')

	# load the parser and the util_methods modules:
	config_parser = load_remote_module('config_parser', utils_dir)

	util_methods = load_remote_module('util_methods', utils_dir)

	this_directory = os.path.dirname(os.path.realpath(__file__))
	config_filepath = util_methods.locate_config(this_directory)

	# parse out the genome-specific info
	project.parameters.add(config_parser.read_config(config_filepath, section = project.parameters.get('genome')))


def load_remote_module(module_name, location):
	sys.path.append(location)
	fileobj, filename, description = imp.find_module(module_name, [location])
	module = imp.load_module(module_name, fileobj, filename, description)
	return module
