import logging
import os
from custom_exceptions import *
import imp

CONFIG_SUFFIX = "cfg"
MAIN_SCRIPT = "main.py"
ENTRY_METHOD = "run"

def locate_config(directory):

	# search in the directory for a proper config file:
	cfg_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(CONFIG_SUFFIX)]
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


def component_structure_valid(path):
	if MAIN_SCRIPT in os.listdir(path):
		module = imp.load_source('main', path)
		if hasattr(module, ENTRY_METHOD):
			return True
		else:
			logging.warning("The component at %s is not configured correctly.  The script is present, but there is no entry method named: '%s'", path, ENTRY_METHOD)
			return False	
	else:
		logging.warning("The component at %s is not configured correctly.  Does not have the main script named: '%s'", path, MAIN_SCRIPT)
		return False
		
