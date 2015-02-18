import logging
from util_classes import Params
import util_methods
import config_parser as cfg_parser
from custom_exceptions import *
import os 

DEFAULT_CONTRAST = 'contrasts.txt'

class Project(object):

	def __init__(self, cl_args):
		self.project_params = Params()
		self.project_params.add(cl_args)


	def get_params(self):
		return self.project_params


	def prepare(self, pipeline_params):
		"""
		Using the commandline arg and the pipeline parameters, complete some of the necessary paths, check that the args are valid, etc.
		"""
		self.__read_project_config(pipeline_params.get('project_configurations_dir'))
		self.__check_samples_file()
		self.__check_contrast_file()

		logging.info('After reading project parameters:')
		logging.info(self.project_params)
		logging.info(pipeline_params)


	def __check_samples_file(self):
		"""
		This only checks that such a file exists-- not that it is correctly formatted.
		"""
		util_methods.check_for_file(self.project_params.get('sample_annotation_file'))	


	def __check_contrast_file(self):
		"""
		This only checks that such a file exists-- not that it is correctly formatted.
		Does not check whether the file is even necessary or consistent with input parameters.
		For example, if the user wishes to skip the analysis, then we do not need a contrast file...if one is given, we do not care that it makes no sense in that context.
		"""
		if self.project_params.get('contrast_file'):
			util_methods.check_for_file(self.project_params.get('contrast_file'))



	def __read_project_config(self, directory):
		"""
		Reads the project configuration file (default or user-supplied via commandline)
		"""
		# if a custom configuration file was not given in cmd line args, use default:
		if not self.project_params.get('project_configuration_file'):
			self.project_params.reset_param('project_configuration_file', util_methods.locate_config(directory) )

		config_filepath = self.project_params.get('project_configuration_file')
		logging.info("Project configuration file is: %s", config_filepath)

		self.project_params.add(cfg_parser.read_config(config_filepath))

		
