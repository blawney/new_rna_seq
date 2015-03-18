import logging
logging.disable(logging.CRITICAL)

import unittest
import mock
import sys
import os
import re

from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

import utils.util_methods as util_methods

from utils.project import Project
from utils.sample import Sample
from utils.util_classes import Params

from component_tester import ComponentTester

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
		s1.bamfiles = ['A.bam', 'A.primary.bam', 'A.primary.dedup.bam']

		project = Project()
		project.add_parameters(p)
		project.add_samples([s1])

		self.module.execute_counting(project, util_methods)

		calls = [mock.call('/path/to/bin/featureCounts -a /path/to/GTF/mock.gtf -t exon -g gene_name -p -o /path/to/final/featureCounts/A.counts A.bam', shell=True),
			mock.call('/path/to/bin/featureCounts -a /path/to/GTF/mock.gtf -t exon -g gene_name -p -o /path/to/final/featureCounts/A.primary.counts A.primary.bam', shell=True),
			mock.call('/path/to/bin/featureCounts -a /path/to/GTF/mock.gtf -t exon -g gene_name -p -o /path/to/final/featureCounts/A.primary.dedup.counts A.primary.dedup.bam', shell=True)]
		self.module.subprocess.check_call.assert_has_calls(calls)

		# check that the sample contains paths to the new count files in the correct locations:
		expected_files = [os.path.join('/path/to/final/featureCounts', re.sub('bam', 'counts', f)) for f in s1.bamfiles]
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
		s1.bamfiles = ['A.bam', 'A.primary.bam', 'A.primary.dedup.bam']

		project = Project()
		project.add_parameters(p)
		project.add_samples([s1])

		self.module.execute_counting(project, util_methods)

		calls = [mock.call('/path/to/bin/featureCounts -a /path/to/GTF/mock.gtf -t exon -g gene_name -o /path/to/final/featureCounts/A.counts A.bam', shell=True),
			mock.call('/path/to/bin/featureCounts -a /path/to/GTF/mock.gtf -t exon -g gene_name -o /path/to/final/featureCounts/A.primary.counts A.primary.bam', shell=True),
			mock.call('/path/to/bin/featureCounts -a /path/to/GTF/mock.gtf -t exon -g gene_name -o /path/to/final/featureCounts/A.primary.dedup.counts A.primary.dedup.bam', shell=True)]
		self.module.subprocess.check_call.assert_has_calls(calls)

		# check that the sample contains paths to the new count files in the correct locations:
		expected_files = [os.path.join('/path/to/final/featureCounts', re.sub('bam', 'counts', f)) for f in s1.bamfiles]
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
		s1.countfiles = ['A.counts', 'A.primary.counts', 'A.primary.dedup.counts']
		s2 = Sample('B', 'Y')
		s2.countfiles = ['B.counts', 'B.primary.counts', 'B.primary.dedup.counts']
		s3 = Sample('C', 'Z')
		s3.countfiles = ['C.counts', 'C.primary.counts', 'C.primary.dedup.counts']

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
		s1.countfiles = ['A.counts', 'A.primary.counts', 'A.primary.dedup.counts']
		s2 = Sample('B', 'Y')
		s2.countfiles = ['B.counts', 'B.primary.dedup.counts']
		s3 = Sample('C', 'Z')
		s3.countfiles = ['C.counts', 'C.primary.counts', 'C.primary.dedup.counts']

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


if __name__ == "__main__":
	unittest.main()




