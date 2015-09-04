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
import jinja2
import __builtin__

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
		[os.symlink(os.path.abspath(x), os.path.join(component_params['report_output_dir'], os.path.basename(x))) for x in glob.glob(os.path.join('test_data', '*' + component_params.get('coverage_file_suffix')))]		
		

		mock_log_data = mock_log_data_structure(project, extra_params)
		self.module.star_methods.process_star_logs = mock.Mock()
		self.module.star_methods.process_star_logs.return_value = mock_log_data
		
		self.module.get_bam_counts = mock.Mock()
		self.module.get_bam_counts.return_value = mock_bam_counts(mock_log_data.keys())
		self.module.calculate_coverage_data = mock.Mock()
		self.module.calculate_coverage_data.return_value = None
		self.module.generate_figures(project, component_params, extra_params)


	def test_fill_template(self):
		
		project = Project()
		parameters = {'bam_filter_level':'sort.primary', 'project_directory': 'abc/foo/AB_12345', 
				'genome': 'hg19', 
				'genome_source_link':'ftp://ftp.ensembl.org/pub/release-75/fasta/homo_sapiens/dna/', 
				'skip_align':False, 
				'skip_analysis':False}

		project.parameters = parameters
		
		component_params = cp.read_config(os.path.join(root, 'components', 'pdf_report', 'report.cfg'), 'COMPONENT_SPECIFIC')
		extra_params = cp.read_config(os.path.join(root, 'components', 'pdf_report', 'report.cfg'), 'STAR')

		mock_sample_ids = [os.path.basename(x).split('.')[0] for x in glob.glob(os.path.join('test_data', '*' + component_params.get('coverage_file_suffix')))]		
		project.samples = [Sample(x, 'X') for x in mock_sample_ids ]
		project.contrasts = [('X','Y'),('X','Z'),('Y','Z')]		

		component_params['report_output_dir'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), test_output_dir, component_params.get('report_output_dir'))
		if not os.path.isdir(component_params['report_output_dir']):
			os.mkdir(component_params['report_output_dir'])

		# link figures so they appear where they should be.
		figure_list = glob.glob(os.path.join(os.path.dirname(__file__), 'test_data', '*' + component_params.get('coverage_plot_suffix')))
		figure_list += [os.path.join(os.path.dirname(__file__), 'test_data', 'bamfile_reads.pdf'), 
				os.path.join(os.path.dirname(__file__), 'test_data', 'mapping_composition.pdf'), 
				os.path.join(os.path.dirname(__file__), 'test_data', 'total_reads.pdf'),
				os.path.join('components', 'pdf_report', 'igv_typical.png'),
				os.path.join('components', 'pdf_report', 'igv_duplicates.png')]
		[os.symlink(os.path.join(root, f),  os.path.join(component_params['report_output_dir'], os.path.basename(f))) for f in figure_list]
	
		self.module.get_diff_exp_gene_summary  = mock.Mock()
		self.module.get_diff_exp_gene_summary.return_value = [['X','Y', 100,200],['Y_1','Z_2', 400, 300],['X_2','Z_3', 150,300]]

		env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(root, 'components', 'pdf_report')))
		template = env.get_template(component_params.get('report_template'))

		self.module.fill_template(template, project, component_params)
		self.module.compile_report(project, component_params)


	def test_system_call_to_bedtools(self):

		project = Project()
		parameters = {'bam_filter_level':'sort.primary', 'project_directory': 'abc/foo/AB_12345', 
				'genome': 'hg19', 
				'genome_source_link':'ftp://ftp.ensembl.org/pub/release-75/fasta/homo_sapiens/dna/', 
				'skip_align':False, 
				'skip_analysis':False}

		project.parameters = parameters

		mock_dir = '/abc/def/'
		mock_sample_names = ['AAA','BBB','CCC']
		levels = ['sort.bam','sort.primary.bam','sort.primary.dedup.bam']

		all_samples = []
		for sn in mock_sample_names:
			bamfiles = map(lambda x: os.path.join(mock_dir, sn + '.' + x), levels)
			s = Sample(sn, 'X', bamfiles = bamfiles)
			all_samples.append(s)

		project.samples = all_samples

		component_params = cp.read_config(os.path.join(root, 'components', 'pdf_report', 'report.cfg'), 'COMPONENT_SPECIFIC')	

		self.module.subprocess.Popen = mock.Mock()
		
		mock_process = mock.Mock()
		mock_process.communicate.return_value = (('abc', 'def'))
		mock_process.returncode = 0
		self.module.subprocess.Popen.return_value = mock_process
		self.module.subprocess.STDOUT = 'abc'
		self.module.subprocess.STDERR = 'def'
		

		m = mock.mock_open()
		with mock.patch.object(__builtin__, 'open', m) as x:
			expected_calls = [
				mock.call([ component_params.get('bedtools_path'), component_params.get('bedtools_cmd'), '-ibam', '/abc/def/AAA.sort.primary.bam', '-bga'],  stderr='abc', stdout=m()),
				mock.call().communicate(),
				mock.call([ component_params.get('bedtools_path'), component_params.get('bedtools_cmd'), '-ibam', '/abc/def/BBB.sort.primary.bam', '-bga'], stderr='abc', stdout=m()),
				mock.call().communicate(),
				mock.call([ component_params.get('bedtools_path'), component_params.get('bedtools_cmd'), '-ibam', '/abc/def/CCC.sort.primary.bam', '-bga'], stderr='abc', stdout=m()),
				mock.call().communicate()]
			self.module.calculate_coverage_data(project, component_params)

		self.module.subprocess.Popen.assert_has_calls(expected_calls) 
		










