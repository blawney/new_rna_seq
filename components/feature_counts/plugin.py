import logging
import sys
import os
import imp
import subprocess

def run(project):
	logging.info('Beginning featureCounts component of pipeline.')

	# load the parser and the util_methods modules:
	config_parser = load_remote_module('config_parser', utils_dir)
	util_methods = load_remote_module('util_methods', utils_dir)

	# parse this module's config file
	parse_config_file(project, util_methods, config_parser)

	# create a full path to the output directory for the featureCount's output and reset the parameter in the project parameters:
	output_dir = os.path.join(project.parameters.get('output_location'), project.parameters.get('feature_counts_output_dir'))
	project.parameters.reset_param('feature_counts_output_dir', output_dir)

	# create the final output directory, if possible
	util_methods.create_directory(output_dir)

	# start the counting:
	execute_counting(project, util_methods)


def execute_counting(project, util_methods):
	"""
	Creates the calls and executes the system calls for running featureCounts
	"""

	# default options, as a list of tuples:
	default_options = [('-a', project.parameters.get('gtf')),('-t', 'exon'),('-g', 'gene_name')]
	base_command = project.parameters.get('feature_counts') + ' ' + ' '.join(map(lambda x: ' '.join(x), default_options))
	if project.parameters.get('paired_alignment'):
		base_command += ' -p'

	for sample in project.samples:
		countfiles = []
		for bamfile in sample.bamfiles:
			output_name = util_methods.case_insensitive_rstrip(os.path.basename(bamfile), 'bam') + project.parameters.get('feature_counts_file_extension')
			output_path = os.path.join(project.parameters.get('feature_counts_output_dir'), output_name)
			command = base_command + ' -o ' + output_path + ' ' + bamfile
			try:
				logging.info('Calling featureCounts with: ')
				logging.info(command)
				subprocess.check_call(command, shell = True)
				countfiles.append(output_path)
			except subprocess.CalledProcessError as ex:
				logging.error('There was an error encountered during execution of featureCounts for sample %s ' % sample.sample_name)
				raise ex
		# keep track of the count files in the sample object:
		sample.countfiles = countfiles


def parse_config_file(project, util_methods, config_parser):
	"""
	Parses this component's configuration file and adds the constants to the project parameters.
	"""
	this_directory = os.path.dirname(os.path.realpath(__file__))
	config_filepath = util_methods.locate_config(this_directory)
	project.parameters.add(config_parser.read_config(config_filepath))


def load_remote_module(module_name, location):
	"""
	Loads and returns the module given by 'module_name' that resides in the given location
	"""
	sys.path.append(location)
	try:
		fileobj, filename, description = imp.find_module(module_name, [location])
		module = imp.load_module(module_name, fileobj, filename, description)
		return module
	except ImportError as ex:
		logging.error('Could not import module %s at location %s' % (module_name, location))
		raise ex
