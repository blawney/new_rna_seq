import logging
import os
from custom_exceptions import *
import imp
import re
import glob

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
		raise MultipleFileFoundException("Multiple configuration files found.  Cannot determine which to use.")
	else:
		logging.error("Could not locate any config files (*.cfg) in %s.", directory)
		raise ConfigFileNotFoundException("Could not locate any configuration files.")



def find_file(root_dir, pattern):
	matching_files = []
	for root, dirs, files in os.walk(root_dir):
		for f in files:
			m = re.match(pattern, f)
			if m:
				filename = m.group()
				filepath = os.path.join(root, f)
				matching_files.append(filepath)
	if len(matching_files) == 1:
		return matching_files[0]
	elif len(matching_files) == 0:
		raise MissingFileException('Could not locate a file that matched the regex %s underneath %s' % (pattern, root_dir))
	elif len(matching_files) > 1:
		raise MultipleFileFoundException('Found multiple files matchin the regex %s underneath %s' % (pattern, root_dir))



def check_for_component_directory(directory):
	if not os.path.isdir(directory):
		raise MissingComponentDirectoryException('Missing a necessary pipeline component: ' + str(directory))



def check_for_file(filepath):
	if not os.path.isfile(filepath):
		raise MissingFileException('Missing a file: ' + str(filepath))



def component_structure_valid(path, main_script, entry_method):
	# have to add the .py extension to match the filename
	main_script = str(main_script) + '.py'
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
	"""
	This method parses a two-column annotation file (sample annotation or contrast annotations) and returns a list of tuples
	"""
	pairings = []
	try:
		with open(annotation_filepath, 'r') as annotation_file:
			for line in annotation_file:
				pair = line.strip().split('\t')
				if len(pair) != 2:
					raise AnnotationFileParseException("Line (%s) did not contain an annotation pair." % repr(line))
				else:
					pairings.append(tuple(pair))
		return set(pairings)
	except Exception as ex:
		logging.error("An exception occurred while attempting to parse the annotation file at %s", annotation_filepath)
		raise AnnotationFileParseException(ex)		



def create_directory(path):
	"""
	Creates a directory.  If it cannot (due to write permissions, etc).  Issues a message and kills the pipeline
	"""
	# to avoid overwriting data in an existing directory, only work in a new directory 
	if os.path.isdir(path):
		raise CannotMakeOutputDirectoryException("The path ("+ path +") is an existing directory. To avoid overwriting data, please supply a path to a new directory")
	elif os.access(os.path.dirname(path), os.W_OK):
		try:
			os.makedirs(path, 0774)
		except Exception as ex:
			raise CannotMakeOutputDirectoryException("Could not create the output directory at: (" + str(path) + "). Check write-permissions, etc.")
			
	else:
		raise CannotMakeOutputDirectoryException("Could not create the output directory at: (" + str(path) + "). Check write-permissions, etc.")
		


def case_insensitive_glob(pattern):

	def either_case(c):
		return '[%s%s]' % (c.lower(), c.upper()) if c.isalpha() else c

	return glob.glob(''.join(map(either_case, pattern)))



