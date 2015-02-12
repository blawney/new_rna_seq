import logging
from util_classes import Params
import config_parser as cfg_parser
import os
import sys
from custom_exceptions import *


class Pipeline(object):

	def __init__(self, pipeline_home, cl_args):

		# initialize a Params object to hold the pipeline parameters/constants
		self.params = Params()
		self.params.add(pipeline_home = pipeline_home)
		self.params.add(cl_args)

		# setup some other features of the Pipeline object
		self.__setup__()



	def __setup__(self):

		self.experiment = None
		self.__read_pipeline_config__()



	def __read_pipeline_config__(self):

		home_dir = self.params.get('pipeline_home')

		# if a custom configuration file was not given in cmd line args, use default:
		if not self.params.get('configuration_file'):
			# search in the pipeline home directory for a proper config file:
			cfg_files = [os.path.join(home_dir, f) for f in os.listdir(home_dir) if f.endswith('cfg')]
			if len(cfg_files) == 1:
				default_config = cfg_files[0]
				logging.info("Located default configuration file: %s", default_config)
				self.params.add( configuration_file = default_config )
			elif len(cfg_files) > 1:
				logging.error("Located multiple config files (*.cfg) in %s.  Cannot determine which one to use. ", home_dir)
				logging.error("Config files: %s", cfg_files)
				raise MultipleConfigFileFoundException("Multiple configuration files found.  Cannot determine which to use.")
			else:
				logging.error("Could not locate any config files (*.cfg) in %s.", home_dir)
				raise ConfigFileNotFoundException("Could not locate any configuration files.")

		# Read the pipeline-level config file
		config_filepath = self.params.get('configuration_file')
		logging.info("Final specification for the configuration file is: %s", config_filepath)
		try:
			with open(config_filepath, 'r') as cfg_fileobj:
				self.params.add(cfg_parser.read(cfg_fileobj))
		except IOError:
			logging.error("Could not find configuration file at: %s", config_filepath)
			raise ConfigFileNotFoundException("Configuration file was not found.")
		except Exception as ex:
			raise ex

		logging.info("After reading configuration and commandline args: ")
		logging.info(self.params)





