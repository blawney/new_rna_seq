from ConfigParser import SafeConfigParser
import os
import logging
import sys
from printers import pretty_print


def create_dict(parser):
	"""
	Creates and returns a dictionary of the key-value parameters in a configuration file
	"""
	d = {}
	for section in parser.sections():
		for opt in parser.options(section):
			value = parser.get(section, opt)
			value = [v.strip() for v in value.split(',')]
			d[opt] = value[0] if len(value)==1 else value
	return d


def read(config_fileobj):
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
	
