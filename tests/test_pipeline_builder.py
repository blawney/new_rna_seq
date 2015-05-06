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
from utils.sample import Sample
from utils.custom_exceptions import *


def my_join(*args):
		return reduce(lambda x,y: os.path.join(x,y), args)


def set_of_tuples_is_equivalent(set_a, set_b):
	v = []
	for i,item in enumerate(set_a):
		if item in set_b or item[::-1] in set_b:
			v.append(True)
		else:
			v.append(False)
	return all(v)

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
		p.all_components = []
		p._PipelineBuilder__get_aligner_info = mock.Mock()

		mock_os.listdir.return_value = ['star.cfg']
		
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

		mock_os.listdir.return_value = []
		
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



	@mock.patch('utils.util_methods.parse_annotation_file')
	@mock.patch('utils.util_methods.os.path.join', side_effect = my_join)
	@mock.patch('utils.pipeline_builder.glob')
	@mock.patch('utils.pipeline_builder.os')
	def test_samples_created_correctly_for_single_end_protocol(self, mock_os, mock_glob, mock_join, mock_parse_method):
		"""
		Tests that, given alignment is desired and the correct project structure is in place, the 
		correct samples are added to the pipeline (only single-end reads)
		"""
		# list of tuples linking the sample names and conditions:
		pairings = [('A', 'X'),('B', 'X'),('C', 'Y')]
		mock_parse_method.return_value = pairings
		
		# setup all the necessary parameters that the method will look at:
		p = PipelineBuilder('')
		p.all_samples = []
		mock_pipeline_params = Params()
		mock_pipeline_params.add(project_directory = '/path/to/project_dir')
		mock_pipeline_params.add(read_1_fastq_tag = '_R1_001.fastq.gz')
		mock_pipeline_params.add(read_2_fastq_tag = '_R2_001.fastq.gz')
		mock_pipeline_params.add(read_1_fastqc_tag = '_R1_001_fastqc')
		mock_pipeline_params.add(read_2_fastqc_tag = '_R2_001_fastqc')
		mock_pipeline_params.add(fastqc_report_file = 'fastqc_report.html')
		mock_pipeline_params.add(sample_annotation_file = '/path/to/project_dir/samples.txt')
		mock_pipeline_params.add(skip_align = False)
		mock_pipeline_params.add(paired_alignment = False)
		mock_pipeline_params.add(target_bam = 'sort.bam')
		mock_pipeline_params.add(sample_dir_prefix = 'Sample_')
		p.builder_params = mock_pipeline_params

		# mock there being only R1 fastq files:
		glob_return = [['A_R1_001.fastq.gz'],[],[],[],['B_R1_001.fastq.gz'],[],[],[], ['C_R1_001.fastq.gz'],[],[],[]]
		mock_glob.glob.side_effect = glob_return

		# mock the missing config file: 
		mock_os.path.isdir.return_value = True

		p._PipelineBuilder__check_and_create_samples()
		for i,s in enumerate(p.all_samples):
			self.assertTrue(s.sample_name == pairings[i][0])
			self.assertTrue(s.read_1_fastq == glob_return[i*4][0])
			self.assertTrue(s.read_2_fastq == None)
			self.assertTrue(s.bamfiles == [])




	@mock.patch('utils.util_methods.parse_annotation_file')
	@mock.patch('utils.util_methods.os.path.join', side_effect = my_join)
	@mock.patch('utils.pipeline_builder.glob')
	@mock.patch('utils.pipeline_builder.os')
	def test_samples_created_correctly_for_paired_end_protocol(self, mock_os, mock_glob, mock_join, mock_parse_method):
		"""
		Tests that, given alignment is desired and the correct project structure is in place, the 
		correct samples are added to the pipeline (paired-end reads)
		"""
		# list of tuples linking the sample names and conditions:
		pairings = [('A', 'X'),('B', 'X'),('C', 'Y')]
		mock_parse_method.return_value = pairings
		
		# setup all the necessary parameters that the method will look at:
		p = PipelineBuilder('')
		p.all_samples = []
		mock_pipeline_params = Params()
		mock_pipeline_params.add(project_directory = '/path/to/project_dir')
		mock_pipeline_params.add(read_1_fastq_tag = '_R1_001.fastq.gz')
		mock_pipeline_params.add(read_2_fastq_tag = '_R2_001.fastq.gz')
		mock_pipeline_params.add(read_1_fastqc_tag = '_R1_001_fastqc')
		mock_pipeline_params.add(read_2_fastqc_tag = '_R2_001_fastqc')
		mock_pipeline_params.add(fastqc_report_file = 'fastqc_report.html')
		mock_pipeline_params.add(sample_annotation_file = '/path/to/project_dir/samples.txt')
		mock_pipeline_params.add(skip_align = False)
		mock_pipeline_params.add(paired_alignment = True)
		mock_pipeline_params.add(target_bam = 'sort.bam')
		mock_pipeline_params.add(sample_dir_prefix = 'Sample_')
		p.builder_params = mock_pipeline_params

		# mock unique R1 and R2 fastq files:
		glob_return = [['A_R1_001.fastq.gz'],['A_R2_001.fastq.gz'],[],[],['B_R1_001.fastq.gz'],['B_R2_001.fastq.gz'],[],[], ['C_R1_001.fastq.gz'],['C_R2_001.fastq.gz'],[],[]]
		mock_glob.glob.side_effect = glob_return

		# mock the missing config file: 
		mock_os.path.isdir.return_value = True

		p._PipelineBuilder__check_and_create_samples()
		for i,s in enumerate(p.all_samples):
			self.assertTrue(s.sample_name == pairings[i][0])
			self.assertTrue(s.read_1_fastq == glob_return[i*4][0])
			self.assertTrue(s.read_2_fastq == glob_return[i*4+1][0])
			self.assertTrue(s.bamfiles == [])


	@mock.patch('utils.util_methods.parse_annotation_file')
	@mock.patch('utils.util_methods.os.path.join', side_effect = my_join)
	@mock.patch('utils.pipeline_builder.glob')
	@mock.patch('utils.pipeline_builder.os')
	def test_exception_raised_if_missing_second_fastq_in_paired_alignment(self, mock_os, mock_glob, mock_join, mock_parse_method):
		"""
		Tests that an exception is raised if paired-end alignment is specified, but no read 2 fastq files are found
		"""
		# list of tuples linking the sample names and conditions:
		pairings = [('A', 'X'),('B', 'X'),('C', 'Y')]
		mock_parse_method.return_value = pairings
		
		# setup all the necessary parameters that the method will look at:
		p = PipelineBuilder('')
		p.all_samples = []
		mock_pipeline_params = Params()
		mock_pipeline_params.add(project_directory = '/path/to/project_dir')
		mock_pipeline_params.add(read_1_fastq_tag = '_R1_001.fastq.gz')
		mock_pipeline_params.add(read_2_fastq_tag = '_R2_001.fastq.gz')
		mock_pipeline_params.add(read_1_fastqc_tag = '_R1_001_fastqc')
		mock_pipeline_params.add(read_2_fastqc_tag = '_R2_001_fastqc')
		mock_pipeline_params.add(fastqc_report_file = 'fastqc_report.html')
		mock_pipeline_params.add(sample_annotation_file = '/path/to/project_dir/samples.txt')
		mock_pipeline_params.add(skip_align = False)
		mock_pipeline_params.add(target_bam = 'sort.bam')
		mock_pipeline_params.add(sample_dir_prefix = 'Sample_')
		p.builder_params = mock_pipeline_params

		# mock there being only R1 fastq files for one of the samples:
		glob_return = [['A_R1_001.fastq.gz'],['A_R2_001.fastq.gz'],[],[],['B_R1_001.fastq.gz'],[],[],[], ['C_R1_001.fastq.gz'],['C_R2_001.fastq.gz'],[],[]]
		mock_glob.glob.side_effect = glob_return

		# mock the missing config file: 
		mock_os.path.isdir.return_value = True

		with self.assertRaises(InconsistentPairingStatusException):
			p._PipelineBuilder__check_and_create_samples()


	@mock.patch('utils.util_methods.parse_annotation_file')
	@mock.patch('utils.util_methods.os.path.join', side_effect = my_join)
	@mock.patch('utils.pipeline_builder.glob')
	@mock.patch('utils.pipeline_builder.os')
	def test_exception_raised_if_one_of_the_samples_has_paired_read_fastq_but_others_dont(self, mock_os, mock_glob, mock_join, mock_parse_method):
		"""
		Tests that an exception is raised if paired-end alignment is specified, but no read 2 fastq files are found
		"""
		# list of tuples linking the sample names and conditions:
		pairings = [('A', 'X'),('B', 'X'),('C', 'Y')]
		mock_parse_method.return_value = pairings
		
		# setup all the necessary parameters that the method will look at:
		p = PipelineBuilder('')
		p.all_samples = []
		mock_pipeline_params = Params()
		mock_pipeline_params.add(project_directory = '/path/to/project_dir')
		mock_pipeline_params.add(read_1_fastq_tag = '_R1_001.fastq.gz')
		mock_pipeline_params.add(read_2_fastq_tag = '_R2_001.fastq.gz')
		mock_pipeline_params.add(read_1_fastqc_tag = '_R1_001_fastqc')
		mock_pipeline_params.add(read_2_fastqc_tag = '_R2_001_fastqc')
		mock_pipeline_params.add(fastqc_report_file = 'fastqc_report.html')
		mock_pipeline_params.add(sample_annotation_file = '/path/to/project_dir/samples.txt')
		mock_pipeline_params.add(skip_align = False)
		mock_pipeline_params.add(paired_alignment = True)
		mock_pipeline_params.add(target_bam = 'sort.bam')
		mock_pipeline_params.add(sample_dir_prefix = 'Sample_')
		p.builder_params = mock_pipeline_params

		# mock there being only R1 fastq files for all of the samples:
		glob_return = [['A_R1_001.fastq.gz'],['A_R2_001.fastq.gz'],[],[],['B_R1_001.fastq.gz'],[],[],[],['C_R1_001.fastq.gz'],[],[],[]]
		mock_glob.glob.side_effect = glob_return

		# mock the missing config file: 
		mock_os.path.isdir.return_value = True

		with self.assertRaises(InconsistentPairingStatusException):
			p._PipelineBuilder__check_and_create_samples()



	@mock.patch('utils.util_methods.parse_annotation_file')
	@mock.patch('utils.util_methods.os.path.join', side_effect = my_join)
	@mock.patch('utils.pipeline_builder.glob')
	@mock.patch('utils.pipeline_builder.os')
	def test_exception_raised_if_paired_alignment_specified_for_single_end(self, mock_os, mock_glob, mock_join, mock_parse_method):
		"""
		Tests that an exception is raised if paired-end alignment is specified, but no read 2 fastq files are found
		"""
		# list of tuples linking the sample names and conditions:
		pairings = [('A', 'X'),('B', 'X'),('C', 'Y')]
		mock_parse_method.return_value = pairings
		
		# setup all the necessary parameters that the method will look at:
		p = PipelineBuilder('')
		p.all_samples = []
		mock_pipeline_params = Params()
		mock_pipeline_params.add(project_directory = '/path/to/project_dir')
		mock_pipeline_params.add(read_1_fastq_tag = '_R1_001.fastq.gz')
		mock_pipeline_params.add(read_2_fastq_tag = '_R2_001.fastq.gz')
		mock_pipeline_params.add(read_1_fastqc_tag = '_R1_001_fastqc')
		mock_pipeline_params.add(read_2_fastqc_tag = '_R2_001_fastqc')
		mock_pipeline_params.add(fastqc_report_file = 'fastqc_report.html')
		mock_pipeline_params.add(sample_annotation_file = '/path/to/project_dir/samples.txt')
		mock_pipeline_params.add(skip_align = False)
		mock_pipeline_params.add(paired_alignment = True)
		mock_pipeline_params.add(target_bam = 'sort.bam')
		mock_pipeline_params.add(sample_dir_prefix = 'Sample_')
		p.builder_params = mock_pipeline_params

		# mock there being only R1 fastq files for all of the samples:
		glob_return = [['A_R1_001.fastq.gz'],[],[],[],['B_R1_001.fastq.gz'],[],[],[], ['C_R1_001.fastq.gz'],[],[],[]]
		mock_glob.glob.side_effect = glob_return

		# mock the missing config file: 
		mock_os.path.isdir.return_value = True

		with self.assertRaises(InconsistentPairingStatusException):
			p._PipelineBuilder__check_and_create_samples()


	@mock.patch('utils.util_methods.parse_annotation_file')
	@mock.patch('utils.util_methods.os.path.join', side_effect = my_join)
	@mock.patch('utils.pipeline_builder.glob')
	@mock.patch('utils.pipeline_builder.os')
	def test_exception_raised_if_single_alignment_specified_for_paired_end(self, mock_os, mock_glob, mock_join, mock_parse_method):
		"""
		Tests that an exception is raised if paired-end alignment is specified, but no read 2 fastq files are found
		"""
		# list of tuples linking the sample names and conditions:
		pairings = [('A', 'X'),('B', 'X'),('C', 'Y')]
		mock_parse_method.return_value = pairings
		
		# setup all the necessary parameters that the method will look at:
		p = PipelineBuilder('')
		p.all_samples = []
		mock_pipeline_params = Params()
		mock_pipeline_params.add(project_directory = '/path/to/project_dir')
		mock_pipeline_params.add(read_1_fastq_tag = '_R1_001.fastq.gz')
		mock_pipeline_params.add(read_2_fastq_tag = '_R2_001.fastq.gz')
		mock_pipeline_params.add(read_1_fastqc_tag = '_R1_001_fastqc')
		mock_pipeline_params.add(read_2_fastqc_tag = '_R2_001_fastqc')
		mock_pipeline_params.add(fastqc_report_file = 'fastqc_report.html')
		mock_pipeline_params.add(sample_annotation_file = '/path/to/project_dir/samples.txt')
		mock_pipeline_params.add(skip_align = False)
		mock_pipeline_params.add(paired_alignment = False)
		mock_pipeline_params.add(target_bam = 'sort.bam')
		mock_pipeline_params.add(sample_dir_prefix = 'Sample_')
		p.builder_params = mock_pipeline_params

		# mock there being both R1 and R2 fastq files for all of the samples:
		glob_return = [['A_R1_001.fastq.gz'],['A_R2_001.fastq.gz'],[],[],['B_R1_001.fastq.gz'],['B_R2_001.fastq.gz'],[],[], ['C_R1_001.fastq.gz'],['C_R2_001.fastq.gz'],[],[]]
		mock_glob.glob.side_effect = glob_return

		# mock the missing config file: 
		mock_os.path.isdir.return_value = True

		with self.assertRaises(InconsistentPairingStatusException):
			p._PipelineBuilder__check_and_create_samples()




	@mock.patch('utils.util_methods.parse_annotation_file')
	@mock.patch('utils.util_methods.os.path.join', side_effect = my_join)
	@mock.patch('utils.pipeline_builder.glob')
	@mock.patch('utils.pipeline_builder.os')
	def test_exception_raised_if_multiple_fastq_found(self, mock_os, mock_glob, mock_join, mock_parse_method):
		"""
		Tests that an exception is raised if there is more than 1 fastq file (e.g. if glob's matching
		routine matches more than one fastq file)
		"""
		# list of tuples linking the sample names and conditions:
		pairings = [('A', 'X'),('B', 'X'),('C', 'Y')]
		mock_parse_method.return_value = pairings
		
		# setup all the necessary parameters that the method will look at:
		p = PipelineBuilder('')
		p.all_samples = []
		mock_pipeline_params = Params()
		mock_pipeline_params.add(project_directory = '/path/to/project_dir')
		mock_pipeline_params.add(read_1_fastq_tag = '_R1_001.fastq.gz')
		mock_pipeline_params.add(read_2_fastq_tag = '_R2_001.fastq.gz')
		mock_pipeline_params.add(read_1_fastqc_tag = '_R1_001_fastqc')
		mock_pipeline_params.add(read_2_fastqc_tag = '_R2_001_fastqc')
		mock_pipeline_params.add(fastqc_report_file = 'fastqc_report.html')
		mock_pipeline_params.add(sample_annotation_file = '/path/to/project_dir/samples.txt')
		mock_pipeline_params.add(skip_align = False)
		mock_pipeline_params.add(target_bam = 'sort.bam')
		mock_pipeline_params.add(sample_dir_prefix = 'Sample_')
		p.builder_params = mock_pipeline_params


		# mock the missing config file: 
		mock_os.path.isdir.return_value = True

		# mock there being only R1 fastq files, and have one of the entries return >1 in the list:
		glob_return = [['A_R1_001.fastq.gz'],[],[],[],['B_R1_001.fastq.gz', 'B_AT_R1_001.fastq.gz'],[],[],[], ['C_R1_001.fastq.gz'],[],[],[]]
		mock_glob.glob.side_effect = glob_return

		with self.assertRaises(MultipleFileFoundException):
			p._PipelineBuilder__check_and_create_samples()

		# mock there being both R1 and R2 fastq files (And we want paired alignment), and have one of the R2 entries return >1 in the list:
		glob_return = [['A_R1_001.fastq.gz'],['A_R2_001.fastq.gz'],[],[],['B_R1_001.fastq.gz'],['B_R2_001.fastq.gz'],[],[], ['C_R1_001.fastq.gz'],['C_R2_001.fastq.gz', 'C_AT_R2_001.fastq.gz'],[],[]]
		mock_glob.glob.side_effect = glob_return

		with self.assertRaises(MultipleFileFoundException):
			p._PipelineBuilder__check_and_create_samples()



	@mock.patch('utils.util_methods.parse_annotation_file')
	@mock.patch('utils.util_methods.find_files')
	def test_samples_created_correctly_for_skipping_align(self, mock_find_files, mock_parse_method):
		"""
		Tests the case where we want to skip alignment and the target suffix is given for the BAM files
		In this test, the call to the find_file method is mocked out with a dummy return value
		"""
		# list of tuples linking the sample names and conditions:
		pairings = [('A', 'X'),('B', 'X'),('C', 'Y')]
		mock_parse_method.return_value = pairings
		
		# mock the find_file() method returning some paths to bam files:
		bamfiles = [['A.sort.bam'],['B.sort.bam'],['C.sort.bam']]
		mock_find_files.side_effect = bamfiles

		# setup all the necessary parameters that the method will look at:
		p = PipelineBuilder('')
		p.all_samples = []
		mock_pipeline_params = Params()
		mock_pipeline_params.add(project_directory = '/path/to/project_dir')
		mock_pipeline_params.add(sample_annotation_file = '/path/to/project_dir/samples.txt')
		mock_pipeline_params.add(skip_align = True)
		mock_pipeline_params.add(paired_alignment = True)
		mock_pipeline_params.add(target_bam = 'sort.bam')
		p.builder_params = mock_pipeline_params

		p._PipelineBuilder__check_and_create_samples()
		for i,s in enumerate(p.all_samples):
			self.assertTrue(s.sample_name == pairings[i][0])
			self.assertTrue(s.read_1_fastq == None)
			self.assertTrue(s.read_2_fastq == None)
			self.assertTrue(s.bamfiles == bamfiles[i] )


	@mock.patch('utils.util_methods.parse_annotation_file')
	@mock.patch('utils.util_methods.find_files')
	def test_raises_exception_if_skipping_align_and_pairing_not_specified(self, mock_find_files, mock_parse_method):
		"""
		Tests the case where we want to skip alignment and the user has not given whether the BAM files were created
		from paired or unpaired protocol
		"""
		# list of tuples linking the sample names and conditions:
		pairings = [('A', 'X'),('B', 'X'),('C', 'Y')]
		mock_parse_method.return_value = pairings
		
		# mock the find_file() method returning some paths to bam files:
		bamfiles = [['A.sort.bam'],['B.sort.bam'],['C.sort.bam']]
		mock_find_files.side_effect = bamfiles

		# setup all the necessary parameters that the method will look at:
		p = PipelineBuilder('')
		p.all_samples = []
		mock_pipeline_params = Params()
		mock_pipeline_params.add(project_directory = '/path/to/project_dir')
		mock_pipeline_params.add(sample_annotation_file = '/path/to/project_dir/samples.txt')
		mock_pipeline_params.add(skip_align = True)
		mock_pipeline_params.add(target_bam = 'sort.bam')
		p.builder_params = mock_pipeline_params

		with self.assertRaises(ParameterNotFoundException):
			p._PipelineBuilder__check_and_create_samples()


	def test_creates_contrasts_correctly_with_no_contrast_file_given(self):

		#make some samples:
		all_samples = [Sample('A', 'X'), Sample('B', 'Y'), Sample('C', 'Z')]
		p = PipelineBuilder('')
		mock_pipeline_params = Params()
		mock_pipeline_params.add(skip_analysis = False)
		mock_pipeline_params.add(contrast_file = None)
		p.builder_params = mock_pipeline_params
		p.all_samples = all_samples

		p._PipelineBuilder__check_contrast_file()
		expected_result = set([('X','Y'),('X','Z'),('Y','Z')])
		self.assertTrue(set_of_tuples_is_equivalent(p.contrasts, expected_result))

	@mock.patch('utils.util_methods.parse_annotation_file')
	def test_creates_contrasts_correctly_with_specified_contrast_file(self, mock_parse):

		#make some samples:
		all_samples = [Sample('A', 'X'), Sample('B', 'Y'), Sample('C', 'Z')]
		p = PipelineBuilder('')
		mock_pipeline_params = Params()
		mock_pipeline_params.add(skip_analysis = False)
		mock_pipeline_params.add(contrast_file = 'contrast.txt')
		p.builder_params = mock_pipeline_params
		p.all_samples = all_samples

		mock_parse.return_value = set([('X','Y'),('X','Z'),('Y','Z')]) 

		p._PipelineBuilder__check_contrast_file()
		expected_result = set([('Y','X'),('X','Z'),('Y','Z')])
		self.assertTrue(set_of_tuples_is_equivalent(p.contrasts, expected_result))


	@mock.patch('utils.util_methods.parse_annotation_file')
	def test_raises_exception_if_non_sensible_contrast_specified(self, mock_parse):

		#make some samples:
		all_samples = [Sample('A', 'X'), Sample('B', 'Y'), Sample('C', 'Z')]
		p = PipelineBuilder('')
		mock_pipeline_params = Params()
		mock_pipeline_params.add(skip_analysis = False)
		mock_pipeline_params.add(contrast_file = 'contrast.txt')
		p.builder_params = mock_pipeline_params
		p.all_samples = all_samples

		# note the specification of a contrast of Y against A.  However, we have no samples from condition A.
		mock_parse.return_value = set([('X','Y'),('X','Z'),('Y','A')]) 

		with self.assertRaises(ContrastSpecificationException):
			p._PipelineBuilder__check_contrast_file()

		



if __name__ == "__main__":
	unittest.main()
