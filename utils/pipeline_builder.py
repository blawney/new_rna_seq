import cmd_line_parser as cl_parser
import config_parser as cfg_parser
from util_classes import Params
import util_methods
from printers import pretty_print
import datetime
import logging
import os
import os_utils
from pipeline import Pipeline
from component import Component
from custom_exceptions import *


class PipelineBuilder(object):

	def __init__(self, pipeline_home_dir):
		self.builder_params = Params()
		self.builder_params.add(pipeline_home = pipeline_home_dir)

	def setup(self):

		self.builder_params.add(cl_parser.read())

		# create the output directory (if possible) from the commandline args
		output_dir = self.builder_params.get('output_location')
		self.__create_output_dir(output_dir)

		# instantiate a logfile in the output directory
		self.__create_logger(output_dir)


	def configure(self):

		# read the config file and ensure that the necessary pipeline directories/structure is there:
		pipeline_elements_dict = self.__read_pipeline_config()
		self.__verify_elements(pipeline_elements_dict)

		# check parameters passed via commandline
		self.__check_project_config()
		self.__check_genome_valid() 
		self.__check_aligner_valid()
		self.__check_samples_file()
		self.__check_contrast_file()
		self.__get_available_components()

		logging.info("After reading pipeline configuration: ")
		logging.info(self.builder_params)


	def build(self):
		pipeline = Pipeline(self.builder_params)
		pipeline.register_components(self.determine_components())
		return pipeline


	def determine_components(self):
		"""
		This method contains the logic for which components to use, etc. in the pipeline 
		"""
		# a dict of component names mapped to component locations
		components_dict = self.available_components
	
		components = [(name, components_dict[name]) for name in self.standard_components]

		if not self.builder_params.get('skip_analysis'):
			components.extend([(name, components_dict[name]) for name in self.analysis_components])
		else:
			logging.info('Skipping analysis per the input args')

		logging.info('Final pipeline components to use:')
		for comp in components:
			logging.info(comp)

		return components


	def __get_available_components(self):
				
		components_dir = self.builder_params.get('components_dir')
		config_filepath = util_methods.locate_config(components_dir)

		# get the plugin parameters-- i.e. each component needs to have a script and entry method to call.
		plugin_parameters = cfg_parser.read_config(config_filepath, 'plugin_params')
		self.builder_params.add(plugin_parameters)
		entry_module = plugin_parameters['entry_module'] #the script filename
		entry_method = plugin_parameters['entry_method']

		logging.info("Search for available components with configuration file at: %s", config_filepath)
		available_components = cfg_parser.read_config(config_filepath, 'plugins')

		# the paths in the dictionary above are relative to the components_dir-- prepend that directory name for the full path
		available_components = {k:os.path.join(components_dir, available_components[k]) for k in available_components.keys()}

		# check that the plugin components have the required structure
		self.available_components = {}
		for k in available_components.keys():
			if util_methods.component_structure_valid(available_components[k], entry_module, entry_method):
				self.available_components[k] = available_components[k]

		logging.info('Available components: ')
		logging.info(pretty_print(self.available_components))

		# get the specifications for the standard components and the analysis components
		self.standard_components = [c for c in cfg_parser.read_config(config_filepath, 'standard_plugins').values()[0] if c in self.available_components.keys()]
		self.analysis_components = [c for c in cfg_parser.read_config(config_filepath, 'analysis_plugins').values()[0] if c in self.available_components.keys()]
		logging.info('Standard components: %s', self.standard_components)
		logging.info('Analysis components: %s', self.analysis_components)


	def __check_samples_file(self):
		"""
		This only checks that such a file exists-- not that it is correctly formatted.
		"""
		util_methods.check_for_file(self.builder_params.get('sample_annotation_file'))	


	def __check_contrast_file(self):
		"""
		This only checks that such a file exists-- not that it is correctly formatted.
		Does not check whether the file is even necessary or consistent with input parameters.
		For example, if the user wishes to skip the analysis, then we do not need a contrast file...if one is given, we do not care that it makes no sense in that context.
		"""
		if self.builder_params.get('contrast_file'):
			util_methods.check_for_file(self.builder_params.get('contrast_file'))


	def __check_genome_valid(self):
		"""
		Ensure that the desired genome is acceptable.  If not, throw an exception
		"""
		genomes_dir = self.builder_params.get('genomes_dir')
		selected_genome = self.builder_params.get('genome')		
		try:
			config_filepath = util_methods.locate_config(genomes_dir)
			self.builder_params.add(cfg_parser.read_config(config_filepath), selected_genome)

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
		self.__get_aligner_info()
		available_aligners = self.builder_params.get('available_aligners')
		default_aligner = self.builder_params.get('default_aligner')

		# if no aligner specified in commandline:
		if not self.builder_params.get('aligner'):
			logging.info('Setting aligner to default: %s', default_aligner)
			self.builder_params.reset_param('aligner', default_aligner)
		elif self.builder_params.get('aligner') not in available_aligners:
			logging.error('Incorrect aligner: %s', self.builder_params.get('aligner'))
			logging.error('Available aligners: %s', available_aligners)
			raise IncorrectAlignerException("Unavailable aligner specified.  Check log and correct as necessary.")
		
		# now check that the combination of genome and aligner is ok:
		chosen_genome = self.builder_params.get('genome')
		aligner = self.builder_params.get('aligner')
		aligner_specific_dir = os.path.join( self.builder_params.get('aligners_dir'), aligner)
		logging.info('Searching for aligner-specific configuration file in %s', aligner_specific_dir)
		util_methods.locate_config(aligner_specific_dir, chosen_genome)


	def __get_aligner_info(self):
		aligner_cfg = util_methods.locate_config(self.builder_params.get('aligners_dir'))
		self.builder_params.add(cfg_parser.read_config(aligner_cfg))	


	def __read_pipeline_config(self):

		# Read the pipeline-level config file
		config_filepath = util_methods.locate_config(self.builder_params.get('pipeline_home'))
		logging.info("Default pipeline configuration file is: %s", config_filepath)
		return cfg_parser.read_config(config_filepath)
		

	def __check_project_config(self):
		# Read the project-level config file
		if not self.builder_params.get('project_configuration_file'):
			default_filepath = util_methods.locate_config(self.builder_params.get('project_configurations_dir'), 'default')
			self.builder_params.reset_param('project_configuration_file', default_filepath)
			
		config_filepath = self.builder_params.get('project_configuration_file')
		logging.info("Project configuration file is: %s", config_filepath)
		self.builder_params.add(cfg_parser.read_config(config_filepath))


	def __verify_elements(self, element_dict):
		"""
		For components, genomes, etc. complete the path to those directories (now that we know the pipeline_home dir)
		Verify that they exist- otherwise we cannot initiate the pipeline 

		"""
		#prepend the pipeline_home location to the elements:
		element_dict = {k:os.path.join(self.builder_params.get('pipeline_home'), element_dict[k]) for k in element_dict.keys()}

		[util_methods.check_for_component_directory(path) for path in element_dict.values()]

		self.builder_params.add(element_dict)


	def __create_output_dir(self, output_dir):
		os_utils.create_directory(output_dir)


	def __create_logger(self, log_dir):
		"""
		Create a logfile in the log_dir directory
		"""
		timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
		logfile = os.path.join(log_dir, str(timestamp)+".rnaseq.log")
		logging.basicConfig(filename=logfile, level=logging.INFO, format="%(asctime)s:%(levelname)s:%(message)s")




