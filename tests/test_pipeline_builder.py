import logging
logging.disable(logging.CRITICAL)


import unittest
import mock
import sys
import os

# for finding modules in the sibling directories
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

from utils.pipeline_builder import PipelineBuilder
from utils.util_classes import Params
from utils.custom_exceptions import *


class TestPipelineBuilder(unittest.TestCase):

	@mock.patch('utils.util_methods.os')
	def test_bad_genome_parameter_raises_exception(self, mock_os):
		"""
		Pass a genome parameter that is not in the genomes directory
		"""

		p = PipelineBuilder('/path/to/dir')
		mock_pipeline_params = Params()
		mock_pipeline_params.add(genomes_dir = 'genome_info', genome = 'XYZ')
		p.builder_params = mock_pipeline_params

		mock_os.listdir.return_value = ['hg19.cfg', 'mm10.cfg']			

		with self.assertRaises(IncorrectGenomeException):
			p._PipelineBuilder__check_genome_valid()


	def test_bad_aligner_parameter_raises_exception(self):
		"""
		Pass a aligner parameter that is not specified in the aligners config file
		"""

		available_aligners = ('star', 'snapr')
		default_aligner = 'star'

		# create a PipelineBuilder and add mocked pipeline/project objects as patches
		p = PipelineBuilder('/path/to/dir')
		mock_pipeline_params = Params()
		mock_pipeline_params.add(available_aligners = available_aligners, 
					default_aligner = default_aligner,
					aligner='junk')
		p.builder_params = mock_pipeline_params
		p._PipelineBuilder__get_aligner_info = mock.Mock()
		
		with self.assertRaises(IncorrectAlignerException):
			p._PipelineBuilder__check_aligner_valid()

	@mock.patch('utils.util_methods.os')
	def test_default_aligner_used_when_not_specified(self, mock_os):
		"""
		If no commandline arg given for aligner, check that it resorts to the default
		"""
	
		available_aligners = ('star', 'snapr')
		default_aligner = 'star'

		# create a PipelineBuilder and add mocked pipeline/project objects as patches
		p = PipelineBuilder('/path/to/dir')
		mock_pipeline_params = Params()
		mock_pipeline_params.add(available_aligners = available_aligners, 
					default_aligner = default_aligner,
					aligner=None,
					aligners_dir = '/path/to/dir',
					genome = 'hg19')
		p.builder_params = mock_pipeline_params
		p._PipelineBuilder__get_aligner_info = mock.Mock()

		mock_os.listdir.return_value = ['hg19.cfg', 'mm10.cfg']
		
		p._PipelineBuilder__check_aligner_valid()
		self.assertEqual(p.builder_params.get('aligner'), default_aligner)



	@mock.patch('utils.util_methods.os')
	def test_missing_aligner_config_file_raises_exception(self, mock_os):

	
		available_aligners = ('star', 'snapr')
		default_aligner = 'star'

		# create a PipelineBuilder and add mocked pipeline/project objects as patches
		p = PipelineBuilder('/path/to/dir')
		mock_pipeline_params = Params()
		mock_pipeline_params.add(available_aligners = available_aligners, 
					default_aligner = default_aligner,
					aligner=None,
					aligners_dir = '/path/to/dir',
					genome = 'mm9')
		p.builder_params = mock_pipeline_params
		p._PipelineBuilder__get_aligner_info = mock.Mock()

		mock_os.listdir.return_value = ['hg19.cfg', 'mm10.cfg']
		
		with self.assertRaises(ConfigFileNotFoundException):
			p._PipelineBuilder__check_aligner_valid()



	@mock.patch('utils.util_methods.os')
	def test_missing_default_project_config_file_with_no_alternative_given(self, mock_os):
		"""
		No config file passed via commandline and none found in the project_configuration directory
		"""
		
		p = PipelineBuilder('/path/to/dir')
		mock_pipeline_params = Params()
		mock_pipeline_params.add(project_configuration_file = None,
					project_configurations_dir = '/path/to/dir')
		p.builder_params = mock_pipeline_params

		# mock the missing config file: 
		mock_os.listdir.return_value = ['something.cfg'] # anything here, just not 'default.cfg'

		with self.assertRaises(ConfigFileNotFoundException):
			p._PipelineBuilder__check_project_config()


	@mock.patch('utils.util_methods.os')
	def test_missing_pipeline_config_file(self, mock_os):
		"""
		The pipeline configuration file is missing (not likely, but possible!)
		"""
		
		p = PipelineBuilder('')
		mock_pipeline_params = Params()
		mock_pipeline_params.add(pipeline_home = '/path/to/dir')
		p.builder_params = mock_pipeline_params

		# mock the missing config file: 
		mock_os.listdir.return_value = []

		with self.assertRaises(ConfigFileNotFoundException):
			p._PipelineBuilder__read_pipeline_config()


	@mock.patch('utils.util_methods.os')
	def test_raises_exception_if_missing_pipeline_components(self, mock_os):
		"""
		This covers where the genome or component directories could be missing (or the path to them is just wrong)
		"""
		
		mock_element_dict = {'genomes_dir': 'genomes_dir', 'utils_dir': 'utils_dir'}
		p = PipelineBuilder('/path/to/pipeline_home')
		mock_os.path.isdir.return_value = False

		with self.assertRaises(MissingComponentDirectoryException):
			p._PipelineBuilder__verify_elements(mock_element_dict)
		


if __name__ == "__main__":
	unittest.main()
