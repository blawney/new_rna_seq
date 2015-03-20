import logging
logging.disable(logging.CRITICAL)

import unittest
import mock
import sys
import os

from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

import utils.util_methods as util_methods

from utils.project import Project
from utils.sample import Sample
from utils.util_classes import Params

from component_tester import ComponentTester


class TestNormalizationComponent(unittest.TestCase, ComponentTester):

	def setUp(self):		
		ComponentTester.loader(self, 'components/deseq_normalize')


	def test_missing_count_matrix_files_raises_exception(self):
		project = Project()
		with self.assertRaises(self.module.NoCountMatricesException):
			self.module.normalize(project)


	def test_correct_calls_are_made(self):
		"""
		Tests that the correct arguments are passed to the method which calls the normalization script.
		Mostly tests the path renaming, etc.
		"""
		self.module.call_script = mock.Mock()
		project = Project()
		project.count_matrices = ['/path/to/raw_counts/raw_count_matrix.primary.counts',
					'/path/to/raw_counts/raw_count_matrix.primary.dedup.counts']
		params = Params()
		params.add(raw_count_matrix_file_prefix = 'raw_count_matrix')
		params.add(normalized_counts_file_prefix = 'normalized_count_matrix')
		params.add(normalized_counts_output_dir = '/path/to/final/norm_counts_dir')
		params.add(normalization_script = 'normalize.R')
		params.add(sample_annotation_file = '/path/to/samples.txt')
		project.add_parameters(params)

		m = mock.MagicMock(side_effect = [True, True])
		path = self.module.os.path
		with mock.patch.object(path, 'isfile', m):
			self.module.normalize(project)
			calls = [mock.call('normalize.R', '/path/to/raw_counts/raw_count_matrix.primary.counts', 
					'/path/to/final/norm_counts_dir/normalized_count_matrix.primary.counts', '/path/to/samples.txt' ), 
				mock.call('normalize.R', '/path/to/raw_counts/raw_count_matrix.primary.dedup.counts', 
					'/path/to/final/norm_counts_dir/normalized_count_matrix.primary.dedup.counts', '/path/to/samples.txt' )]
			self.module.call_script.assert_has_calls(calls)

	def test_missing_countfile_raises_exception(self):
		"""
		Test one of the files is ok (the first), but the second is not found (for whatever reason).  Test that we throw an exception, 
		and that the one successful call was indeed made correctly.
		"""
		self.module.call_script = mock.Mock()
		project = Project()
		project.count_matrices = ['/path/to/raw_counts/raw_count_matrix.primary.counts',
					'/path/to/raw_counts/raw_count_matrix.primary.dedup.counts']
		params = Params()
		params.add(raw_count_matrix_file_prefix = 'raw_count_matrix')
		params.add(normalized_counts_file_prefix = 'normalized_count_matrix')
		params.add(normalized_counts_output_dir = '/path/to/final/norm_counts_dir')
		params.add(normalization_script = 'normalize.R')
		params.add(sample_annotation_file = '/path/to/samples.txt')
		project.add_parameters(params)

		m = mock.MagicMock(side_effect = [True, False])
		path = self.module.os.path
		with mock.patch.object(path, 'isfile', m):
			with self.assertRaises(self.module.MissingCountMatrixFileException):
				self.module.normalize(project)
			calls = [mock.call('normalize.R', '/path/to/raw_counts/raw_count_matrix.primary.counts', 
					'/path/to/final/norm_counts_dir/normalized_count_matrix.primary.counts', '/path/to/samples.txt' )]
			self.module.call_script.assert_has_calls(calls)


	def test_system_call_to_Rscript(self):
		self.module.subprocess = mock.Mock()
		self.module.call_script('normalize.R', '/path/to/input/raw.counts', '/path/to/output/norm.counts', '/path/to/samples.txt')
		full_script_path = os.path.join(os.path.dirname(os.path.abspath(self.module.__file__)), 'normalize.R')
		expected_call = 'Rscript ' + full_script_path + ' /path/to/input/raw.counts /path/to/output/norm.counts /path/to/samples.txt'
		self.module.subprocess.check_call.assert_called_once_with(expected_call, shell=True)		
		

if __name__ == "__main__":
	unittest.main()
