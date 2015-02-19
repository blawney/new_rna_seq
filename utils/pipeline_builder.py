import cmd_line_parser as cl_parser
import config_parser as cfg_parser
import util_methods
import datetime
import logging
import os
import os_utils
from pipeline import Pipeline
from project import Project
from component import Component
from custom_exceptions import *


class PipelineBuilder(object):

	def __init__(self, pipeline_home_dir):
		self.pipeline_home_dir = pipeline_home_dir
		self.pipeline = None
		self.project = None

	def setup(self):

		cl_args = self.__parse_commandline_args()

		# create the output directory (if possible) from the commandline args
		output_dir = cl_args['output_location']
		self.__create_output_dir(output_dir)

		# instantiate a logfile in the output directory
		self.__create_logger(output_dir)


	def create_pipeline(self):
		# create the pipeline object:
		self.pipeline = Pipeline(self.pipeline_home_dir)
		self.pipeline.setup()


	def create_project(self):
		# create a project:
		self.project = Project(cl_args)
		self.project.prepare(self.pipeline.get_params())



	def verify_args(self):
		# verify commandline args are OK given the pipeline's available modules, genomes, etc:
		self.__check_aligner_valid()
		self.__check_genome_valid() 


	def register_components(self):

		# a dict of component names mapped to component locations
		components_dict = self.pipeline.get_available_components()
		self.registered_components = [Component(name, dir_name, self.project.get_params()) for name,dir_name in components_dict.items()]
		



	def __check_genome_valid(self):
		"""
		Ensure that the desired genome is acceptable.  If not, throw an exception
		"""
		available_genomes = self.pipeline.get_params().get('available_genomes')
		
		if self.project.get_params().get('genome') not in available_genomes:
			logging.error('Incorrect genome: %s', self.project.get_params().get('genome'))
			logging.error('Available genomes: %s', available_genomes)
			raise IncorrectGenomeException("Incorrect or unconfigured genome specified.  Check log and correct as necessary.")	


	def __check_aligner_valid(self):
		"""
		If aligner was specified in input args, check that it is valid and fill in the appropriate parameter
		If aligner arg not correct, throw an exception
		"""
		
		available_aligners = self.pipeline.get_params().get('available_aligners')
		default_aligner = self.pipeline.get_params().get('default_aligner')

		# if no aligner specified in commandline:
		if not self.project.get_params().get('aligner'):
			self.project.get_params().reset_param('aligner', default_aligner)
		elif self.project.get_params().get('aligner') not in available_aligners:
			logging.error('Incorrect aligner: %s', self.project.get_params().get('aligner'))
			logging.error('Available aligners: %s', available_aligners)
			raise IncorrectAlignerException("Unavailable aligner specified.  Check log and correct as necessary.")



	def __parse_commandline_args(self):
		return cl_parser.read()


	def __create_output_dir(self, output_dir):
		os_utils.create_directory(output_dir)


	def __create_logger(self, log_dir):
		"""
		Create a logfile in the log_dir directory
		"""
		timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
		logfile = os.path.join(log_dir, str(timestamp)+".rnaseq.log")
		logging.basicConfig(filename=logfile, level=logging.INFO, format="%(asctime)s:%(levelname)s:%(message)s")


