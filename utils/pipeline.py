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
		self.__read_pipeline_config()

		# ensure that the necessary pipeline directories/structure is there:
		[self.__verify_addons(addon) for addon in self.params.get_param_dict().keys()]

		self.__get_available_genomes()
		self.__get_available_aligners()
		logging.info("After reading pipeline configuration: ")
		logging.info(self.params)



	def __get_available_genomes(self):
		genome_cfg = util_methods.locate_config(self.params.get('genomes_dir'))
		self.params.add(cfg_parser.read_config(genome_cfg))		


	def __get_available_aligners(self):
		aligner_cfg = util_methods.locate_config(self.params.get('aligners_dir'))
		self.params.add(cfg_parser.read_config(aligner_cfg))	


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


	def add_project(self, project):
		self.project = project

	def prepare_project(self):
		self.project.prepare(self.params)




