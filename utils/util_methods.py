import logging
import os
from custom_exceptions import *
import imp

CONFIG_SUFFIX = "cfg"

def locate_config(directory, prefix=''):
	# search in the directory for a proper config file:
	cfg_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(CONFIG_SUFFIX) and f.startswith(prefix)]
	if len(cfg_files) == 1:
		logging.info("Located configuration file: %s", cfg_files[0])
		return cfg_files[0]
	elif len(cfg_files) > 1:
		logging.error("Located multiple config files (*.cfg) in %s.  Cannot determine which one to use. ", directory)
		logging.error("Config files: %s", cfg_files)
		raise MultipleConfigFileFoundException("Multiple configuration files found.  Cannot determine which to use.")
	else:
		logging.error("Could not locate any config files (*.cfg) in %s.", directory)
		raise ConfigFileNotFoundException("Could not locate any configuration files.")


def check_for_component_directory(directory):
	if not os.path.isdir(directory):
		raise MissingComponentDirectoryException('Missing a necessary pipeline component: ' + str(directory))


def check_for_file(filepath):
	if not os.path.isfile(filepath):
		raise MissingFileException('Missing a file: ' + str(filepath))


def component_structure_valid(path, main_script, entry_method):
	if main_script in os.listdir(path):
		module = imp.load_source('main', os.path.join(path, main_script))
		if hasattr(module, entry_method):
			return True
		else:
			logging.warning("The component at %s is not configured correctly.  The script is present, but there is no entry method named: '%s'", path, entry_method)
			return False	
	else:
		logging.warning("The component at %s is not configured correctly.  Does not have the main script named: '%s'", path, main_script)
		return False
		


def parse_annotation_file(annotation_filepath):
	pairings = []
	try:
		with open(annotation_filepath, 'r') as annotation_file:
			for line in annotation_file:
				pair = line.strip().split('\t')
				if len(pair) != 2:
					raise AnnotationFileParseException("Line (%s) did not contain a sample-to-condition pair." % repr(line))
				else:
					pairings.append(tuple(pair))
		return pairings
	except Exception as ex:
		logging.error("An exception occurred while attempting to parse the annotation file at %s", annotation_filepath)
		raise AnnotationFileParseException(ex.message)		


		
