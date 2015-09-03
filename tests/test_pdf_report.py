import logging
logging.disable(logging.CRITICAL)

import unittest
import mock
import sys
import os
import glob
import shutil
import imp
import numpy as np

from os import path
root =  path.dirname( path.dirname( path.abspath(__file__) ) ) 
sys.path.append(root)

import utils.util_methods as util_methods
import utils.config_parser as cp

from utils.project import Project
from utils.sample import Sample
from utils.util_classes import Params

from component_tester import ComponentTester

test_output_dir = 'test_output'


def mock_log_data_structure(project, extra_params):

	fileobj, filename, description = imp.find_module('star_methods', [os.path.join(root, 'components/pdf_report')])
	test_module = imp.load_module('star_methods', fileobj, filename, description)

	test_module.glob = mock.Mock()
	test_logs = glob.glob( os.path.join(os.path.abspath(os.path.dirname(__file__)), 'test_data', '*Log.final.out' ) )
	test_module.glob.glob.return_value = test_logs
	data = test_module.process_star_logs(project, extra_params)

	return data



def mock_bam_counts(sample_ids):
	low = 9e6
	high = 1e7
	n = len(sample_ids)
	d = {}
	bamtypes = ['sort', 'sort.primary', 'sort.primary.dedup']
	for i,t in enumerate(bamtypes):
		d[t] = 	dict(zip(sample_ids, (1-0.3*i)*np.random.randint(low, high, n)))
	return d


class TestPdfReportGenerator(unittest.TestCase, ComponentTester):
	def setUp(self):
		ComponentTester.loader(self, 'components/pdf_report')
		if os.path.isdir(test_output_dir):
			shutil.rmtree(test_output_dir)
		os.mkdir(test_output_dir)


	def test_generate_figures(self):
		"""
		This is not a unit test in the conventional sense-- this is a full-scale mockup which will
		create an output pdf and everything.
		"""
		
		project = Project()
		parameters = {'aligner':'star', 'skip_align':False, 'sample_dir_prefix': 'Sample_', 'alignment_dir': 'aln', 'project_directory': 'foo', 'chromosomes':['chr1', 'chr2', 'chrM']}
		project.parameters = parameters
		
		component_params = cp.read_config(os.path.join(root, 'components', 'pdf_report', 'report.cfg'), 'COMPONENT_SPECIFIC')
		extra_params = cp.read_config(os.path.join(root, 'components', 'pdf_report', 'report.cfg'), 'STAR')

		mock_sample_ids = [os.path.basename(x).split('.')[0] for x in glob.glob(os.path.join('test_data', '*' + component_params.get('coverage_file_suffix')))]		
		project.samples = [Sample(x, 'X') for x in mock_sample_ids ]		

		component_params['report_output_dir'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), test_output_dir, component_params.get('report_output_dir'))
		if not os.path.isdir(component_params['report_output_dir']):
			os.mkdir(component_params['report_output_dir'])

		# link the test files so they 'appear' in the correct location:
		mock_sample_ids = [os.symlink(os.path.abspath(x), os.path.join(component_params['report_output_dir'], os.path.basename(x))) for x in glob.glob(os.path.join('test_data', '*' + component_params.get('coverage_file_suffix')))]		
		

		mock_log_data = mock_log_data_structure(project, extra_params)
		self.module.star_methods.process_star_logs = mock.Mock()
		self.module.star_methods.process_star_logs.return_value = mock_log_data
		
		self.module.get_bam_counts = mock.Mock()
		self.module.get_bam_counts.return_value = mock_bam_counts(mock_log_data.keys())
		self.module.calculate_coverage_data = mock.Mock()
		self.module.calculate_coverage_data.return_value = None
		self.module.generate_figures(project, component_params, extra_params)

		
