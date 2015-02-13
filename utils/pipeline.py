import logging
from util_classes import Params
import config_parser as cfg_parser
import os
import sys
from custom_exceptions import *
import util_methods


class Pipeline(object):

	def __init__(self, pipeline_home):

		# initialize a Params object to hold the pipeline parameters/constants
		self.params = Params()
		self.params.add(pipeline_home = pipeline_home)


	def setup(self):

		self.project = None
		self.__read_pipeline_config__()

		# ensure that the necessary pipeline directories/structure is there:
		necessary_components = ('genomes_dir', 'components_dir', 'utils_dir', 'project_configurations_dir')
		[self.__verify_addons__(addon) for addon in necessary_components]

		logging.info("After reading pipeline configuration: ")
		logging.info(self.params)
		

	def __verify_addons__(self, addon):
		"""
		For components, genomes, etc. complete the path to those directories (now that we know the pipeline_home dir)
		Verify that they exist- otherwise we cannot initiate the pipeline 
		"""
		self.params.reset_param(addon, os.path.join(self.params.get('pipeline_home'), self.params.get(addon)))
		util_methods.check_for_component_directory(self.params.get(addon))
		


	def __read_pipeline_config__(self):

		# Read the pipeline-level config file
		config_filepath = util_methods.locate_config(self.params.get('pipeline_home'))
		logging.info("Default pipeline configuration file is: %s", config_filepath)
		try:
			with open(config_filepath, 'r') as cfg_fileobj:
				self.params.add(cfg_parser.read(cfg_fileobj))
		except IOError:
			logging.error("Could not find configuration file at: %s", config_filepath)
			raise ConfigFileNotFoundException("Configuration file was not found.")
		except Exception as ex:
			raise ex


	def add_project(self, project):
		self.project = project

	def prepare_project(self):
		self.project.prepare(self.params)




