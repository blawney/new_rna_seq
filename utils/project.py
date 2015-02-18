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


	def prepare(self, pipeline_params):

		self.__read_project_config(pipeline_params.get('project_configurations_dir'))
		self.__check_samples_file()
		self.__check_contrast_file()
		self.__check_genome_valid(pipeline_params.get('available_genomes'))
		self.__check_aligner_valid(pipeline_params.get('available_aligners'), pipeline_params.get('default_aligner'))

		logging.info('After reading project parameters:')
		logging.info(self.project_params)
		logging.info(pipeline_params)


	def __check_samples_file(self):
		"""
		This only checks that such a file exists-- not that it is correctly formatted.
		"""
		util_methods.check_for_file(self.project_params.get('sample_annotation_file'))


	def __check_genome_valid(self, available_genomes):
		if self.project_params.get('genome') not in available_genomes:
			logging.error('Incorrect genome: %s', self.project_params.get('genome'))
			logging.error('Available genomes: %s', available_genomes)
			raise IncorrectGenomeException("Incorrect or unconfigured genome specified.  Check log and correct as necessary.")	


	def __check_contrast_file(self):
		"""
		This only checks that such a file exists-- not that it is correctly formatted.
		Does not check whether the file is even necessary or consistent with input parameters.
		For example, if the user wishes to skip the analysis, then we do not need a contrast file...if one is given, we do not care that it makes no sense in that context.
		"""
		if self.project_params.get('contrast_file'):
			util_methods.check_for_file(self.project_params.get('contrast_file'))


	def __check_aligner_valid(self, available_aligners, default_aligner):

		# if no aligner specified in commandline:
		if not self.project_params.get('aligner'):
			self.project_params.reset_param('aligner', default_aligner)
		elif self.project_params.get('aligner') not in available_aligners:
			logging.error('Incorrect aligner: %s', self.project_params.get('aligner'))
			logging.error('Available aligners: %s', available_aligners)
			raise IncorrectAlignerException("Unavailable aligner specified.  Check log and correct as necessary.")


	def __read_project_config(self, directory):

		# if a custom configuration file was not given in cmd line args, use default:
		if not self.project_params.get('project_configuration_file'):
			self.project_params.reset_param('project_configuration_file', util_methods.locate_config(directory) )

		config_filepath = self.project_params.get('project_configuration_file')
		logging.info("Project configuration file is: %s", config_filepath)

		self.project_params.add(cfg_parser.read_config(config_filepath))

		
