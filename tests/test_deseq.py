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


class TestDeseqComponent(unittest.TestCase, ComponentTester):

	def setUp(self):		
		ComponentTester.loader(self, 'components/deseq')


	def test_missing_count_matrix_files_raises_exception(self):
		project = Project()
		cp = Params()
		with self.assertRaises(self.module.NoCountMatricesException):
			self.module.call_deseq(project, cp)


	def test_correct_calls_are_made(self):
		"""
		Tests that the correct arguments are passed to the method which calls the DESeq script.
		Mostly tests the path renaming, etc.
		"""
		self.module.call_script = mock.Mock()
		project = Project()
		project.raw_count_matrices = ['/path/to/raw_counts/raw_count_matrix.primary.counts',
					'/path/to/raw_counts/raw_count_matrix.primary.dedup.counts']
		project_params = Params()
		component_params = Params()
		project_params.add(raw_count_matrix_file_prefix = 'raw_count_matrix')
		project_params.add(feature_counts_file_extension = 'counts')
		component_params.add(deseq_output_dir = '/path/to/final/deseq_dir')
		component_params.add(deseq_script = 'deseq_original.R')
		project_params.add(sample_annotation_file = '/path/to/samples.txt')
		component_params.add( deseq_output_tag ='deseq')
		component_params.add(deseq_contrast_flag = '_vs_')
		component_params.add(number_of_genes_for_heatmap = '30')
		component_params.add(heatmap_file_tag = 'heatmap.png')

		project.add_parameters(project_params)
		project.contrasts = [('X', 'Y'),('X', 'Z')]

		# construct the expected call strings:
		call_1 ='/path/to/raw_counts/raw_count_matrix.primary.counts /path/to/samples.txt X Y /path/to/final/deseq_dir/Y_vs_X.primary.deseq /path/to/final/deseq_dir/Y_vs_X.primary.heatmap.png 30'
		call_2 ='/path/to/raw_counts/raw_count_matrix.primary.counts /path/to/samples.txt X Z /path/to/final/deseq_dir/Z_vs_X.primary.deseq /path/to/final/deseq_dir/Z_vs_X.primary.heatmap.png 30'
		call_3 ='/path/to/raw_counts/raw_count_matrix.primary.dedup.counts /path/to/samples.txt X Y /path/to/final/deseq_dir/Y_vs_X.primary.dedup.deseq /path/to/final/deseq_dir/Y_vs_X.primary.dedup.heatmap.png 30'
		call_4 ='/path/to/raw_counts/raw_count_matrix.primary.dedup.counts /path/to/samples.txt X Z /path/to/final/deseq_dir/Z_vs_X.primary.dedup.deseq /path/to/final/deseq_dir/Z_vs_X.primary.dedup.heatmap.png 30'

		m = mock.MagicMock(side_effect = [True, True])
		path = self.module.os.path
		with mock.patch.object(path, 'isfile', m):
			self.module.call_deseq(project, component_params)
			calls = [mock.call('deseq_original.R', call_1), mock.call('deseq_original.R', call_2), mock.call('deseq_original.R', call_3), mock.call('deseq_original.R', call_4)]
			self.module.call_script.assert_has_calls(calls)


	def test_missing_countfile_raises_exception(self):
		"""
		Test one of the files is ok (the first), but the second is not found (for whatever reason).  Test that we throw an exception, 
		and that the one successful call was indeed made correctly.
		"""
		self.module.call_script = mock.Mock()
		project = Project()
		project.raw_count_matrices = ['/path/to/raw_counts/raw_count_matrix.primary.counts',
					'/path/to/raw_counts/raw_count_matrix.primary.dedup.counts']

		project_params = Params()
		component_params = Params()
		project_params.add(raw_count_matrix_file_prefix = 'raw_count_matrix')
		project_params.add(feature_counts_file_extension = 'counts')
		component_params.add(deseq_output_dir = '/path/to/final/deseq_dir')
		component_params.add(deseq_script = 'deseq_original.R')
		project_params.add(sample_annotation_file = '/path/to/samples.txt')
		component_params.add( deseq_output_tag ='deseq')
		component_params.add(deseq_contrast_flag = '_vs_')
		component_params.add(number_of_genes_for_heatmap = '30')
		component_params.add(heatmap_file_tag = 'heatmap.png')

		project.add_parameters(project_params)
		project.contrasts = [('X', 'Y'),('X', 'Z')]

		# construct the expected call strings:
		call_1 ='/path/to/raw_counts/raw_count_matrix.primary.counts /path/to/samples.txt X Y /path/to/final/deseq_dir/Y_vs_X.primary.deseq /path/to/final/deseq_dir/Y_vs_X.primary.heatmap.png 30'
		call_2 ='/path/to/raw_counts/raw_count_matrix.primary.counts /path/to/samples.txt X Z /path/to/final/deseq_dir/Z_vs_X.primary.deseq /path/to/final/deseq_dir/Z_vs_X.primary.heatmap.png 30'

		m = mock.MagicMock(side_effect = [True, False])
		path = self.module.os.path
		with mock.patch.object(path, 'isfile', m):
			with self.assertRaises(self.module.MissingCountMatrixFileException):
				self.module.call_deseq(project, component_params)
			calls = [mock.call('deseq_original.R', call_1), mock.call('deseq_original.R', call_2)]
			self.module.call_script.assert_has_calls(calls)


	def test_system_call_to_Rscript(self):
		self.module.subprocess = mock.Mock()
		mock_process = mock.Mock()
		mock_process.communicate.return_value = (('abc', 'def'))
		mock_process.returncode = 0
		self.module.subprocess.Popen.return_value = mock_process
		self.module.subprocess.STDOUT = 'abc'
		self.module.subprocess.STDERR = 'def'
		self.module.call_script('deseq_original.R', '/path/to/raw_counts/raw_count_matrix.primary.counts /path/to/samples.txt X Y /path/to/final/deseq_dir/X_vs_Y.primary.deseq /path/to/final/deseq_dir/X_vs_Y.primary.heatmap.png 30')
		full_script_path = os.path.join(os.path.dirname(os.path.abspath(self.module.__file__)), 'deseq_original.R')
		expected_call = 'Rscript ' + full_script_path + ' /path/to/raw_counts/raw_count_matrix.primary.counts /path/to/samples.txt X Y /path/to/final/deseq_dir/X_vs_Y.primary.deseq /path/to/final/deseq_dir/X_vs_Y.primary.heatmap.png 30'
		self.module.subprocess.Popen.assert_called_once_with(expected_call, shell = True, stderr=self.module.subprocess.STDOUT, stdout=self.module.subprocess.PIPE)


		

if __name__ == "__main__":
	unittest.main()
