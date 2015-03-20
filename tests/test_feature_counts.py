import logging
logging.disable(logging.CRITICAL)

import unittest
import mock
import sys
import os
import re
import __builtin__
from StringIO import StringIO

from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

import utils.util_methods as util_methods

from utils.project import Project
from utils.sample import Sample
from utils.util_classes import Params

from component_tester import ComponentTester


def create_mock_open(fileobj):

	mock_obj = mock.MagicMock(spec = file)
	mock_obj.__enter__.return_value = fileobj
	mock_obj.return_value = mock_obj
	return mock_obj


class TestFeatureCounts(unittest.TestCase, ComponentTester):
	
	def setUp(self):		
		ComponentTester.loader(self, 'components/feature_counts')


	def test_system_calls_paired_experiment(self):
		self.module.subprocess = mock.Mock()

		p = Params()
		p.add(gtf = '/path/to/GTF/mock.gtf')
		p.add(feature_counts = '/path/to/bin/featureCounts')
		p.add(feature_counts_file_extension = 'counts')
		p.add(feature_counts_output_dir = '/path/to/final/featureCounts')
		p.add(paired_alignment = True)
		
		s1 = Sample('A', 'X')
		s1.bamfiles = ['/path/to/bamdir/A.bam', '/path/to/bamdir/A.primary.bam', '/path/to/bamdir/A.primary.dedup.bam']

		project = Project()
		project.add_parameters(p)
		project.add_samples([s1])

		m = mock.MagicMock(side_effect = [True, True, True])
		path = self.module.os.path
		with mock.patch.object(path, 'isfile', m):
			self.module.execute_counting(project, util_methods)

			calls = [mock.call('/path/to/bin/featureCounts -a /path/to/GTF/mock.gtf -t exon -g gene_name -p -o /path/to/final/featureCounts/A.counts /path/to/bamdir/A.bam', shell=True),
				mock.call('/path/to/bin/featureCounts -a /path/to/GTF/mock.gtf -t exon -g gene_name -p -o /path/to/final/featureCounts/A.primary.counts /path/to/bamdir/A.primary.bam', shell=True),
				mock.call('/path/to/bin/featureCounts -a /path/to/GTF/mock.gtf -t exon -g gene_name -p -o /path/to/final/featureCounts/A.primary.dedup.counts /path/to/bamdir/A.primary.dedup.bam', shell=True)]
			self.module.subprocess.check_call.assert_has_calls(calls)

		# check that the sample contains paths to the new count files in the correct locations:
		expected_files = [os.path.join('/path/to/final/featureCounts', re.sub('bam', 'counts', os.path.basename(f))) for f in s1.bamfiles]
		actual_files = s1.countfiles
		self.assertEqual(actual_files, expected_files)
		

	def test_system_calls_single_end_experiment(self):
		self.module.subprocess = mock.Mock()
		
		p = Params()
		p.add(gtf = '/path/to/GTF/mock.gtf')
		p.add(feature_counts = '/path/to/bin/featureCounts')
		p.add(feature_counts_file_extension = 'counts')
		p.add(feature_counts_output_dir = '/path/to/final/featureCounts')
		p.add(paired_alignment = False)
		
		s1 = Sample('A', 'X')
		s1.bamfiles = ['/path/to/bamdir/A.bam', '/path/to/bamdir/A.primary.bam', '/path/to/bamdir/A.primary.dedup.bam']

		project = Project()
		project.add_parameters(p)
		project.add_samples([s1])

		m = mock.MagicMock(side_effect = [True, True, True])
		path = self.module.os.path
		with mock.patch.object(path, 'isfile', m):
			self.module.execute_counting(project, util_methods)

			calls = [mock.call('/path/to/bin/featureCounts -a /path/to/GTF/mock.gtf -t exon -g gene_name -o /path/to/final/featureCounts/A.counts /path/to/bamdir/A.bam', shell=True),
				mock.call('/path/to/bin/featureCounts -a /path/to/GTF/mock.gtf -t exon -g gene_name -o /path/to/final/featureCounts/A.primary.counts /path/to/bamdir/A.primary.bam', shell=True),
				mock.call('/path/to/bin/featureCounts -a /path/to/GTF/mock.gtf -t exon -g gene_name -o /path/to/final/featureCounts/A.primary.dedup.counts /path/to/bamdir/A.primary.dedup.bam', shell=True)]
			self.module.subprocess.check_call.assert_has_calls(calls)

			# check that the sample contains paths to the new count files in the correct locations:
			expected_files = [os.path.join('/path/to/final/featureCounts', re.sub('bam', 'counts', os.path.basename(f))) for f in s1.bamfiles]
			actual_files = s1.countfiles
			self.assertEqual(actual_files, expected_files)


	def test_group_countfiles(self):
		"""
		Test the method that aggregates all the countfiles generated from each 'type' of bam file.  That is, we may have multiple bam files for each sample (e.g. primary alignments, deduplicated, etc).
		We will be generating a countfile for each one of those.  When we assemble into a count matrix, we obviously group the files of a particular 'type' (e.g. those coming from deduplicated BAM files).
		This tests that the the glob methods are called with the correct parameters given the sample annotations prescribed.
		"""
		mock_util_methods = mock.Mock()
		mock_util_methods.case_insensitive_glob = mock.Mock()
		mock_case_insensitive_glob = mock.Mock()

		p = Params()
		p.add(feature_counts_output_dir = '/path/to/final/featureCounts')

		s1 = Sample('A', 'X')
		s1.countfiles = ['/path/to/final/featureCounts/A.counts', '/path/to/final/featureCounts/A.primary.counts', '/path/to/final/featureCounts/A.primary.dedup.counts']
		s2 = Sample('B', 'Y')
		s2.countfiles = ['/path/to/final/featureCounts/B.counts', '/path/to/final/featureCounts/B.primary.counts', '/path/to/final/featureCounts/B.primary.dedup.counts']
		s3 = Sample('C', 'Z')
		s3.countfiles = ['/path/to/final/featureCounts/C.counts', '/path/to/final/featureCounts/C.primary.counts', '/path/to/final/featureCounts/C.primary.dedup.counts']

		project = Project()
		project.add_parameters(p)
		project.add_samples([s1, s2, s3])

		mock_case_insensitive_glob.side_effect = [ ['/path/to/final/featureCounts/A.counts', '/path/to/final/featureCounts/B.counts', '/path/to/final/featureCounts/C.counts'],
									['/path/to/final/featureCounts/A.primary.counts', '/path/to/final/featureCounts/B.primary.counts', '/path/to/final/featureCounts/C.primary.counts'],
									['/path/to/final/featureCounts/A.primary.dedup.counts', '/path/to/final/featureCounts/B.primary.dedup.counts', '/path/to/final/featureCounts/C.primary.dedup.counts']] 
		

		result = self.module.get_countfile_groupings(project, mock_case_insensitive_glob)
		
		calls = [mock.call('/path/to/final/featureCounts/*.counts'), mock.call('/path/to/final/featureCounts/*.primary.counts'), mock.call('/path/to/final/featureCounts/*.primary.dedup.counts')]
		mock_case_insensitive_glob.assert_has_calls(calls)


	def test_group_countfiles_raises_exception_if_missing_type(self):
		"""
		Test the method that aggregates all the countfiles generated from each 'type' of bam file.  That is, we may have multiple bam files for each sample (e.g. primary alignments, deduplicated, etc).
		We will be generating a countfile for each one of those.  When we assemble into a count matrix, we obviously group the files of a particular 'type' (e.g. those coming from deduplicated BAM files).
		This tests that the the glob methods are called with the correct parameters given the sample annotations prescribed.

		This one tests that an exception is raised if one of the countfile 'types' is missing.  Here, sample B is missing a countfile corresponding to the primary.counts- based BAM files
		"""

		p = Params()
		p.add(feature_counts_output_dir = '/path/to/final/featureCounts')

		s1 = Sample('A', 'X')
		s1.countfiles = ['/path/to/final/featureCounts/A.counts', '/path/to/final/featureCounts/A.primary.counts', '/path/to/final/featureCounts/A.primary.dedup.counts']
		s2 = Sample('B', 'Y')
		s2.countfiles = ['/path/to/final/featureCounts/B.counts', '/path/to/final/featureCounts/B.primary.dedup.counts']
		s3 = Sample('C', 'Z')
		s3.countfiles = ['/path/to/final/featureCounts/C.counts', '/path/to/final/featureCounts/C.primary.counts', '/path/to/final/featureCounts/C.primary.dedup.counts']

		project = Project()
		project.add_parameters(p)
		project.add_samples([s1, s2, s3])

		mock_util_methods = mock.Mock()
		mock_case_insensitive_glob = mock.Mock()
		mock_case_insensitive_glob.side_effect = [ ['/path/to/final/featureCounts/A.counts', '/path/to/final/featureCounts/B.counts', '/path/to/final/featureCounts/C.counts'],
									['/path/to/final/featureCounts/A.primary.counts', '/path/to/final/featureCounts/C.primary.counts'],
									['/path/to/final/featureCounts/A.primary.dedup.counts', '/path/to/final/featureCounts/B.primary.dedup.counts', '/path/to/final/featureCounts/C.primary.dedup.counts']] 
		with self.assertRaises(self.module.CountfileQuantityException):
			result = self.module.get_countfile_groupings(project, mock_case_insensitive_glob)



	def test_countfiles_merged_correctly(self):
		"""
		This tests that multiple 'files' are merged into a single data structure in the correct way
		"""
		matrix = []
		mock_data_1 = '#header1\nheader2\ngeneA\tx\tx\tx\tx\tx\t0\ngeneB\tx\tx\tx\tx\tx\t1\ngeneC\tx\tx\tx\tx\tx\t2'
		mock_data_2 = '#header1\nheader2\ngeneA\tx\tx\tx\tx\tx\t100\ngeneB\tx\tx\tx\tx\tx\t101\ngeneC\tx\tx\tx\tx\tx\t102'
		mock_data_3 = '#header1\nheader2\ngeneA\tx\tx\tx\tx\tx\t200\ngeneB\tx\tx\tx\tx\tx\t201\ngeneC\tx\tx\tx\tx\tx\t202'
		expected_result = [['geneA', '0','100','200'],['geneB', '1','101','201'],['geneC', '2','102','202']]

		mock_data_1 = StringIO(mock_data_1)
		mock_open_1 = create_mock_open(mock_data_1)
		with mock.patch.object(__builtin__, 'open', mock_open_1) as mo:
			self.module.read(matrix, '/path/to/dummy')

		mock_data_2 = StringIO(mock_data_2)
		mock_open_2 = create_mock_open(mock_data_2)
		with mock.patch.object(__builtin__, 'open', mock_open_2) as mo:
			self.module.read(matrix, '/path/to/dummy')

		mock_data_3 = StringIO(mock_data_3)
		mock_open_3 = create_mock_open(mock_data_3)
		with mock.patch.object(__builtin__, 'open', mock_open_3) as mo:
			self.module.read(matrix, '/path/to/dummy')

		self.assertEqual(matrix, expected_result)



	def test_countfile_merging(self):
		"""
		This tests that the correct files are used to merge.  The result (a data structure) of the merging is mocked out.
		Tests that the expected data is written to the file and tests that the file ends up in the correct location
		"""

		# a dummy method to mock the reading/concatenating of the data in the individual files
		def mock_read(matrix, f):
			dummy = [['geneA', '0','100','200'],['geneB', '1','101','201'],['geneC', '2','102','202']]
			if len(matrix) == 0:
				for k in range(len(dummy)):
					matrix.append([])
	
			for i,l in enumerate(dummy):
				matrix[i] = l


		# mock out the actual implementations
		self.module.get_countfile_groupings = mock.Mock()

		self.module.get_countfile_groupings.return_value = [ ['/path/to/final/featureCounts/A.counts', '/path/to/final/featureCounts/C.counts', '/path/to/final/featureCounts/B.counts'],
									['/path/to/final/featureCounts/A.primary.counts', '/path/to/final/featureCounts/C.primary.counts'],
									['/path/to/final/featureCounts/A.primary.dedup.counts', '/path/to/final/featureCounts/B.primary.dedup.counts', '/path/to/final/featureCounts/C.primary.dedup.counts']] 
	

		self.module.read = mock_read

		p = Params()
		p.add(raw_count_matrix_file_prefix = 'merged_counts')

		s1 = Sample('A', 'X')
		s1.countfiles = ['/path/to/final/featureCounts/A.primary.counts', '/path/to/final/featureCounts/A.counts', '/path/to/final/featureCounts/A.primary.dedup.counts']
		s2 = Sample('B', 'Y')
		s2.countfiles = ['/path/to/final/featureCounts/B.counts', '/path/to/final/featureCounts/B.primary.dedup.counts', '/path/to/final/featureCounts/B.primary.counts']
		s3 = Sample('C', 'Z')
		s3.countfiles = ['/path/to/final/featureCounts/C.counts', '/path/to/final/featureCounts/C.primary.counts', '/path/to/final/featureCounts/C.primary.dedup.counts']

		project = Project()
		project.add_parameters(p)
		project.add_samples([s1, s3, s2])
		
		m = mock.mock_open()
		with mock.patch.object(__builtin__, 'open', m):
			self.module.create_count_matrices(project, mock.Mock())
			m.assert_any_call('/path/to/final/featureCounts/merged_counts.counts', 'w')
			m.assert_any_call('/path/to/final/featureCounts/merged_counts.primary.counts', 'w')
			m.assert_any_call('/path/to/final/featureCounts/merged_counts.primary.dedup.counts', 'w')
			handle = m()
			calls = [mock.call('Gene\tA\tB\tC\n'), mock.call('geneA\t0\t100\t200\n'), mock.call('geneB\t1\t101\t201\n'), mock.call('geneC\t2\t102\t202\n')] * 3
			handle.write.assert_has_calls(calls)
			

	
	def test_bad_bamfile_path_raises_exception(self):

		self.module.subprocess = mock.Mock()

		p = Params()
		p.add(gtf = '/path/to/GTF/mock.gtf')
		p.add(feature_counts = '/path/to/bin/featureCounts')
		p.add(feature_counts_file_extension = 'counts')
		p.add(feature_counts_output_dir = '/path/to/final/featureCounts')
		p.add(paired_alignment = False)
		
		s1 = Sample('A', 'X')
		s1.bamfiles = ['/path/to/bamdir/A.bam', '/path/to/bamdir/A.primary.bam', '/path/to/bamdir/A.primary.dedup.bam']
		s2 = Sample('B', 'X')
		s2.bamfiles = ['/path/to/bamdir/B.bam', '/bad/path/B.sort.bam']

		project = Project()
		project.add_parameters(p)
		project.add_samples([s1, s2])

		m = mock.MagicMock(side_effect = [True, True, True, True, False])
		path = self.module.os.path
		with mock.patch.object(path, 'isfile', m):
			with self.assertRaises(self.module.MissingBamFileException):
				self.module.execute_counting(project, util_methods)



if __name__ == "__main__":
	unittest.main()




