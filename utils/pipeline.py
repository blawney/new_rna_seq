import logging
from util_classes import Params
import config_parser as cfg_parser
from printers import pretty_print
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
		self.__read_pipeline_config()

		# ensure that the necessary pipeline directories/structure is there:
		[self.__verify_addons(addon) for addon in self.params.get_param_dict().keys()]

		self.__get_available_aligners()
		self.__get_available_components()

		logging.info("After reading pipeline configuration: ")
		logging.info(self.params)


	def get_params(self):
		return self.params


	def get_available_components(self):
		return self.available_components

	def get_standard_components(self):
		return self.standard_components

	def get_analysis_components(self):
		return self.analysis_components


	def __get_available_aligners(self):
		aligner_cfg = util_methods.locate_config(self.params.get('aligners_dir'))
		self.params.add(cfg_parser.read_config(aligner_cfg))	


	def __get_available_components(self):
				
		components_dir = self.params.get('components_dir')
		config_filepath = util_methods.locate_config(components_dir)
		logging.info("Search for available components with configuration file at: %s", config_filepath)
		available_components = cfg_parser.read_config(config_filepath, 'plugins')

		# the paths in the dictionary above are relative to the components_dir-- prepend that directory name for the full path
		available_components = {k:os.path.join(components_dir, available_components[k]) for k in available_components.keys()}

		# check that the plugin components have the required structure
		self.available_components = {k:available_components[k] for k in available_components.keys() if util_methods.component_structure_valid(available_components[k])}
		logging.info('Available components: ')
		logging.info(pretty_print(self.available_components))

		# get the specs for the standard components and the analysis components
		self.standard_components = [c for c in cfg_parser.read_config(config_filepath, 'standard_plugins').values()[0] if c in self.available_components.keys()]
		self.analysis_components = [c for c in cfg_parser.read_config(config_filepath, 'analysis_plugins').values()[0] if c in self.available_components.keys()]
		logging.info('Standard components: %s', self.standard_components)
		logging.info('Analysis components: %s', self.analysis_components)


	def __verify_addons(self, addon):
		"""
		For components, genomes, etc. complete the path to those directories (now that we know the pipeline_home dir)
		Verify that they exist- otherwise we cannot initiate the pipeline 
		"""
		self.params.reset_param(addon, os.path.join(self.params.get('pipeline_home'), self.params.get(addon)))
		util_methods.check_for_component_directory(self.params.get(addon))
		


	def __read_pipeline_config(self):

		# Read the pipeline-level config file
		config_filepath = util_methods.locate_config(self.params.get('pipeline_home'))
		logging.info("Default pipeline configuration file is: %s", config_filepath)
		self.params.add(cfg_parser.read_config(config_filepath))





