from ConfigParser import SafeConfigParser
import os
import logging
import sys
from printers import pretty_print
from custom_exceptions import ConfigFileNotFoundException


def create_dict(parser):
	"""
	Creates and returns a dictionary of the key-value parameters in a configuration file
	"""
	d = {}
	for section in parser.sections():
		for opt in parser.options(section):
			value = parser.get(section, opt)
			value = tuple([v.strip() for v in value.split(',') if len(v.strip()) > 0])
			d[opt] = value[0] if len(value)==1 else value
	return d


def read_config(config_filepath):
	try:
		with open(config_filepath, 'r') as cfg_fileobj:
			return parse(cfg_fileobj)
	except IOError:
		logging.error("Could not find configuration file at: %s", config_filepath)
		raise ConfigFileNotFoundException("Configuration file was not found.")
	except Exception as ex:
		raise ex


def parse(config_fileobj):
	"""
	Takes in a file-like object
	"""
	logging.info("Attempting to parse configuration file")
	parser = SafeConfigParser()
	parser.readfp(config_fileobj)
	cfg = create_dict(parser)
	logging.info("Completed parsing.")
	logging.info(pretty_print(cfg))
	return cfg
	
