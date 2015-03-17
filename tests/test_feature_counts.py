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

class TestStarAligner(unittest.TestCase, ComponentTester):
	
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


if __name__ == "__main__":
	unittest.main()




