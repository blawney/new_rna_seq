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

		self.cl_args = cl_parser.read()

		# create the output directory (if possible) from the commandline args
		output_dir = self.cl_args['output_location']
		self.__create_output_dir(output_dir)

		# instantiate a logfile in the output directory
		self.__create_logger(output_dir)


	def create_pipeline(self):
		# create the pipeline object:
		self.pipeline = Pipeline(self.pipeline_home_dir)
		self.pipeline.setup()


	def create_project(self):
		# create a project:
		self.project = Project(self.cl_args)
		self.project.prepare(self.pipeline.get_params())



	def verify_args(self):
		# verify commandline args are OK given the pipeline's available modules, genomes, etc:
		self.__check_genome_valid() 
		self.__check_aligner_valid()
		logging.info('After verification of aligner and genome args: ')
		logging.info(self.pipeline.get_params())
		logging.info(self.project.get_params())


	def build(self):
		"""
		This method contains the logic for which components to use, etc. in the pipeline 
		"""
		# a dict of component names mapped to component locations
		components_dict = self.pipeline.get_available_components()
		
		components = []
		if not self.project.get_params().get('skip_align'):
			aligner = self.project.get_params().get('aligner')
			aligner_specific_dir = os.path.join( self.pipeline.get_params().get('aligners_dir'), aligner)
			components.append(Component(aligner, aligner_specific_dir, self.project.get_params()))

		components.extend([Component(name, components_dict[name], self.project.get_params()) for name in self.pipeline.get_standard_components()])

		if not self.project.get_params().get('skip_analysis'):
			components.extend([Component(name, components_dict[name], self.project.get_params()) for name in self.pipeline.get_analysis_components()])

		logging.info('Final pipeline components to use:')
		for comp in components:
			logging.info(comp)

	def __check_genome_valid(self):
		"""
		Ensure that the desired genome is acceptable.  If not, throw an exception
		"""
		genomes_dir = self.pipeline.get_params().get('genomes_dir')
		selected_genome = self.project.get_params().get('genome')		
		try:
			util_methods.locate_config(genomes_dir, selected_genome)
		except Exception as ex:
			logging.error('Caught exception while looking for genome configuration file: ')
			logging.error(ex.message)
			logging.error('Incorrect genome: %s', selected_genome)
			logging.error('See available genomes in : %s', genomes_dir)
			raise IncorrectGenomeException("Incorrect or unconfigured genome specified.  Check log and correct as necessary.")	


	def __check_aligner_valid(self):
		"""
		If aligner was specified in input args, check that it is valid and fill in the appropriate parameter
		If aligner arg not correct, throw an exception

		After determining that the aligner name was valid, then check whether the particular combination of genome+aligner is OK.
		(e.g. some aligners may be valid, but not yet configured for the genome of interest)
		"""
		
		available_aligners = self.pipeline.get_params().get('available_aligners')
		default_aligner = self.pipeline.get_params().get('default_aligner')

		# if no aligner specified in commandline:
		if not self.project.get_params().get('aligner'):
			logging.info('Setting aligner to default: %s', default_aligner)
			self.project.get_params().reset_param('aligner', default_aligner)
		elif self.project.get_params().get('aligner') not in available_aligners:
			logging.error('Incorrect aligner: %s', self.project.get_params().get('aligner'))
			logging.error('Available aligners: %s', available_aligners)
			raise IncorrectAlignerException("Unavailable aligner specified.  Check log and correct as necessary.")
		
		# now check that the combination of genome and aligner is ok:
		chosen_genome = self.project.get_params().get('genome')
		aligner = self.project.get_params().get('aligner')
		aligner_specific_dir = os.path.join( self.pipeline.get_params().get('aligners_dir'), aligner)
		logging.info('Searching for aligner-specific configuration file in %s', aligner_specific_dir)
		util_methods.locate_config(aligner_specific_dir, chosen_genome)


	def __create_output_dir(self, output_dir):
		os_utils.create_directory(output_dir)


	def __create_logger(self, log_dir):
		"""
		Create a logfile in the log_dir directory
		"""
		timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
		logfile = os.path.join(log_dir, str(timestamp)+".rnaseq.log")
		logging.basicConfig(filename=logfile, level=logging.INFO, format="%(asctime)s:%(levelname)s:%(message)s")


