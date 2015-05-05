import config_parser as cfg_parser
from util_classes import Params
import util_methods
from printers import pretty_print
import datetime
import logging
import os
import glob
from pipeline import Pipeline
from component import Component
from custom_exceptions import *
from sample import Sample
from project import Project
import itertools


class PipelineBuilder(object):

	def __init__(self, pipeline_home_dir):
		self.builder_params = Params()
		self.builder_params.add(pipeline_home = pipeline_home_dir)

	def setup(self, cl_params):
		"""
		Parses commandline input, creates the output directory, instantiates a log file
		"""
		self.builder_params.add(cl_params)

		# create the output directory (if possible) from the commandline args
		output_dir = self.builder_params.get('output_location')
		self.__create_output_dir(output_dir)


	def configure(self):
		"""
		Reads the configuration file, checks the commandline args against the available/configured components
		"""

		# read the config file and ensure that the necessary pipeline directories/structure is there:
		pipeline_elements_dict = self.__read_pipeline_config()
		self.__verify_elements(pipeline_elements_dict)

		# create an empty list that will hold Component objects
		self.all_components = []

		# check parameters passed via commandline
		self.__check_project_config()

		# add samples
		self.all_samples = [] 
		self.__check_and_create_samples()

		# check the contrasts (if applicable)
		self.__check_contrast_file()

		self.__check_genome_valid()

		if not self.builder_params.get('skip_align'):
			self.__check_aligner_valid()

		self.determine_components()


	def build(self):
		pipeline = Pipeline()
		pipeline.register_components(self.all_components)

		project = Project()
		project.add_parameters(self.builder_params)
		project.add_samples(self.all_samples)
		project.add_contrasts(self.contrasts)

		pipeline.add_project(project)

		pipeline.print_summary()

		return pipeline


	def determine_components(self):
		"""
		This method contains the logic for which components to use, etc. in the pipeline 
		"""
		# call a method that inspects the components and ensures they are correctly configured
		self.__get_available_components()

		# a dict of component names mapped to component locations
		components_dict = self.available_components

		# create the components that are always invoked:
		for name in self.standard_components:
			logging.info('Creating component: %s' % name)
			self.all_components.append(Component(name, components_dict[name]))

		if not self.builder_params.get('skip_analysis'):
			for name in self.analysis_components:
				logging.info('Creating component: %s' % name)
				self.all_components.append(Component(name, components_dict[name]))
		else:
			logging.info('Skipping analysis per the input args')



	def __get_available_components(self):
		"""
		
		"""
		components_dir = self.builder_params.get('components_dir')
		config_filepath = util_methods.locate_config(components_dir)

		# get the plugin parameters-- i.e. each component needs to have a script and entry method to call.
		plugin_parameters = cfg_parser.read_config(config_filepath, 'plugin_params')
		self.builder_params.add(plugin_parameters)
		entry_module = plugin_parameters['entry_module'] #the script filename (minus the .py extension) 
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


	def __check_and_create_samples(self):
		"""
		This method reads the samples in the sample annotation file and determines if:
		1) if performing alignment, the directory structure is correct and the necessary files are there
		2) if alignment is skipped (i.e. have BAM files), the necessary BAM files are there
		"""
		logging.info('Checking sample annotation file against project directory.')

		# the name of the sample and the condition, as a list of tuples:
		name_and_condition_pairings = util_methods.parse_annotation_file(self.builder_params.get('sample_annotation_file'))
		logging.info('The following sample to group pairings were found in the sample annotation file: ')
		logging.info(name_and_condition_pairings)
	
		paired_status = None
		for sample_name, condition in name_and_condition_pairings:
			logging.info('Checking sample %s' % sample_name)
			# if aligning
			if not self.builder_params.get('skip_align'):
				directory_name = self.builder_params.get('sample_dir_prefix') + sample_name
				expected_directory = os.path.join(self.builder_params.get('project_directory'), directory_name)
				if os.path.isdir(expected_directory):

					# get a list of the fastq files matching the appropriate pattern:
					read_1_files = glob.glob(os.path.join(expected_directory, '*' + self.builder_params.get('read_1_fastq_tag')))
					read_2_files = glob.glob(os.path.join(expected_directory, '*' + self.builder_params.get('read_2_fastq_tag')))

					if len(read_1_files) != 1:
						logging.error('Problem finding read 1 fastq files for sample %s inside %s' % (sample_name, expected_directory))
						if len(read_1_files) == 0:
							raise MissingFileException('There were no R1 fastq files found.')
						else:
							raise MultipleFileFoundException('There was more than 1 fastq file marked with the suffix %s inside %s' % (self.builder_params.get('read_1_fastq_tag'),expected_directory))

					if len(read_2_files) == 1:
						logging.info('Read 2 fastq files found for sample %s' % sample_name)
						if paired_status is not None and paired_status != True:
							raise InconsistentPairingStatusException('Inconsistent paired-alignment status')
						else:
							paired_status = True
							new_sample = Sample(sample_name, condition, read_1_fastq = read_1_files[0], read_2_fastq = read_2_files[0])
					elif len(read_2_files) == 0:
						logging.info('Only read 1 fastq files were found for sample %s' % sample_name)
						if paired_status is not None and paired_status != False:
							raise InconsistentPairingStatusException('Inconsistent paired-alignment status')
						else:
							paired_status = False
							new_sample = Sample(sample_name, condition, read_1_fastq = read_1_files[0])
					elif len(read_2_files) > 1:
						raise MultipleFileFoundException('There was more than 1 fastq file marked with the suffix %s inside %s' % (self.builder_params.get('read_2_fastq_tag'),expected_directory))


					# try to find fastQC files:
					read_1_fastqc = glob.glob(os.path.join(expected_directory, '*' + self.builder_params.get('read_1_fastQC_tag'), self.builder_params.get('fastqc_report_file')))
					read_2_fastqc = glob.glob(os.path.join(expected_directory, '*' + self.builder_params.get('read_2_fastQC_tag'), self.builder_params.get('fastqc_report_file')))
					if len(read_1_fastqc) == 1:
						new_sample.read_1_fastqc_report = read_1_fastqc
					else:
						new_sample.read_1_fastqc_report = None

					if len(read_2_fastqc) == 1:
						new_sample.read_2_fastqc_report = read_2_fastqc
					else:
						new_sample.read_2_fastqc_report = Noneqc

					logging.info('Adding new sample:\n %s' % new_sample)
					self.all_samples.append(new_sample)

					
				else:
					logging.error('%s was not, in fact, a directory or the name scheme was incorrect.' % expected_directory)
					raise ProjectStructureException('The sample directory %s does not exist' % expected_directory)
			else: # if skipping alignment:
				search_pattern = sample_name + '.*?' + self.builder_params.get('target_bam')
				bam_files = util_methods.find_files(self.builder_params.get('project_directory'), search_pattern)
				new_sample = Sample(sample_name, condition, bamfiles = bam_files)
				logging.info('Adding new sample:\n %s' % new_sample)
				self.all_samples.append(new_sample)


		# set the paired boolean.
		# if skipping align, try to set the variable.  If exception is thrown, then it has already been set via the input args.  Check 
		# that the passed arg and the paired_status variable are consistent.  If not, kill the pipeline by throwing exception
		if not self.builder_params.get('skip_align'):
			try:
				self.builder_params.add(paired_alignment = paired_status)
			except ParameterOverwriteException:
				if self.builder_params.get('paired_alignment') != paired_status:
					raise InconsistentPairingStatusException('Arg passed via commandline specified paired_alignment=%s and this is not consistent with the fastq files found.' % self.builder_params.get('paired_alignment'))
		else: # if skipping alignment, need to know paired status of BAM files...can't guess, and need it for downstream steps
			try:
				self.builder_params.get('paired_alignment')
			except ParameterNotFoundException:
				raise ParameterNotFoundException('Need to specify whether BAM files are based on paired or unpaired if not aligning.')


	def __check_contrast_file(self):
		"""
		Logic for the experimental contrasts if downstream analysis is desired.
		"""
		if not self.builder_params.get('skip_analysis'):

			# from the samples we had earlier, get all the possible conditions
			conditions = set([sample.condition for sample in self.all_samples])
			logging.info('All conditions represented in the samples: %s' % conditions)

			# if contrast file path was given in command line:
			if self.builder_params.get('contrast_file'):
				contrast_pairings = util_methods.parse_annotation_file(self.builder_params.get('contrast_file'))	
			else:
				# if no contrast file was given, get all pairwise contrasts:
				contrast_pairings = set(itertools.combinations(conditions, 2))

			logging.info('Contrast pairings before checking against sample annotations: %s' % contrast_pairings)
			# check that the condition specifications make sense given the samples (if we specify a contrast against condition A, but no samples are annotated as condition A, then issue an error)
			for condition_a, condition_b in contrast_pairings:
				if not condition_a in conditions or not condition_b in conditions:
					raise ContrastSpecificationException('Either condition %s or %s is not represented by any samples' % (condition_a, condition_b))
			self.contrasts = contrast_pairings
		else:
			self.contrasts =  None

		logging.info('Final contrast pairings: %s' % self.contrasts)



	def __check_genome_valid(self):
		"""
		Ensure that the desired genome is acceptable.  If not, throw an exception
		If the appropriate genome is found, read-in the genome parameters (e.g. path to GTF file, etc)
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
		
		# now check that this aligner has a config file.  Does not check that the aligner+genome is OK.  
		# That is done when the aligner is invoked.
		chosen_genome = self.builder_params.get('genome')
		aligner = self.builder_params.get('aligner')
		aligner_specific_dir = os.path.join( self.builder_params.get('aligners_dir'), aligner)
		logging.info('Searching (but not parsing) for aligner configuration file in: %s', aligner_specific_dir)
		util_methods.locate_config(aligner_specific_dir)

		# create a component for the aligner:
		self.all_components.append(Component(aligner, aligner_specific_dir))


	def __get_aligner_info(self):
		"""
		Finds and parses the aligner configuration file-- this only indicates which aligners
		are available and which are default.  Nothing specific to a particular aligner.
		"""
		aligner_cfg = util_methods.locate_config(self.builder_params.get('aligners_dir'))
		self.builder_params.add(cfg_parser.read_config(aligner_cfg))	


	def __read_pipeline_config(self):

		# Read the pipeline-level config file
		config_filepath = util_methods.locate_config(self.builder_params.get('pipeline_home'))
		logging.info("Default pipeline configuration file is: %s", config_filepath)
		return cfg_parser.read_config(config_filepath)
		

	def __check_project_config(self):
		"""
		Reads a project configuration file-- this configuration file lays out how a typical project is arranged in terms of file hierarchy,
		naming of fastq files, etc.  Parameters are added to the builder_params object
		"""
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
		util_methods.create_directory(output_dir)




