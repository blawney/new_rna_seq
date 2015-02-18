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



def mock_param(param):
	if param == 'available_aligners':
		return ('star', 'snapr')
	if param == 'default_aligner':
		return 'star'


class TestPipelineBuilder(unittest.TestCase):


	def test_bad_genome_parameter_raises_exception(self):
		"""
		Pass a genome parameter that is not specified in the genome config file
		"""

		available_genomes = ('hg19', 'mm10')

		p = PipelineBuilder('/path/to/dir')
		p.pipeline = mock.MagicMock()
		p.project = mock.MagicMock()
		p.pipeline.get_params.get.return_value = ('hg19', 'mm10')
		p.project.get_params.get.return_value = ('XYZ')
		with self.assertRaises(IncorrectGenomeException):
			p._PipelineBuilder__check_genome_valid()


	@mock.patch('utils.pipeline_builder.Project')
	@mock.patch('utils.pipeline_builder.Pipeline')
	def test_bad_aligner_parameter_raises_exception(self, mock_pipeline, mock_project):
		"""
		Pass a aligner parameter that is not specified in the aligners config file
		"""

		available_aligners = ('star', 'snapr')
		default_aligner = 'star'

		# create a PipelineBuilder and add mocked pipeline/project objects as patches
		p = PipelineBuilder('/path/to/dir')
		p.pipeline = mock_pipeline.return_value
		p.project = mock_project.return_value

		mock_pipeline_params = Params()
		mock_pipeline_params.add(available_aligners = available_aligners)
		mock_pipeline_params.add(default_aligner = default_aligner)
		p.pipeline.get_params.return_value = mock_pipeline_params

		mock_project_params = Params()
		mock_project_params.add(aligner = 'junk')
		p.project.get_params.return_value = mock_project_params
		
		with self.assertRaises(IncorrectAlignerException):
			p._PipelineBuilder__check_aligner_valid()


	@mock.patch('utils.pipeline_builder.Project')
	@mock.patch('utils.pipeline_builder.Pipeline')
	def test_default_aligner_used_when_not_specified(self, mock_pipeline, mock_project):
		"""
		If no commandline arg given for aligner, check that it resorts to the default
		"""
	
		available_aligners = ('star', 'snapr')
		default_aligner = 'star'

		# create a PipelineBuilder and add mocked pipeline/project objects as patches
		p = PipelineBuilder('/path/to/dir')
		p.pipeline = mock_pipeline.return_value
		p.project = mock_project.return_value

		mock_pipeline_params = Params()
		mock_pipeline_params.add(available_aligners = available_aligners)
		mock_pipeline_params.add(default_aligner = default_aligner)
		p.pipeline.get_params.return_value = mock_pipeline_params

		mock_project_params = Params()
		mock_project_params.add(aligner = None)
		p.project.get_params.return_value = mock_project_params
		
		p._PipelineBuilder__check_aligner_valid()
		self.assertEqual(p.project.get_params().get('aligner'), default_aligner)


if __name__ == "__main__":
	unittest.main()
