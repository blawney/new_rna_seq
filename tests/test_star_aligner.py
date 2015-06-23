import logging
logging.disable(logging.CRITICAL)

import unittest
import mock
import sys
import os

from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

from utils.project import Project
from utils.sample import Sample
from utils.util_classes import Params

from component_tester import ComponentTester

class TestStarAligner(unittest.TestCase, ComponentTester):
	
	def setUp(self):		
		ComponentTester.loader(self, 'aligners/star')


	def test_parameter_injector_raises_exception_if_replacement_target_not_found(self):	
		template = 'ITEM=%FOO%\nVAR=3'
		with self.assertRaises(self.module.IncorrectParameterSubstitutionException):
			result = self.module.inject_parameter('%BAR%', 'abc', template)


	def test_parameter_injector_accepts_non_string(self):	
		template = 'ITEM=%FOO%\nVAR=3'
		parameter = 5.6
		expected_result = 'ITEM=5.6\nVAR=3'	
		result = self.module.inject_parameter('%FOO%', parameter, template)
		self.assertEqual(result, expected_result)

	def test_parameter_injector(self):	
		template = 'ITEM=%FOO%\nVAR=3'
		parameter = 'bar'
		expected_result = 'ITEM=bar\nVAR=3'	
		result = self.module.inject_parameter('%FOO%', parameter, template)
		self.assertEqual(result, expected_result)


	def test_general_portion_of_template_injected_correctly(self):
		template = 'STAR=%STAR%\nSAMTOOLS=%SAMTOOLS%\nPICARD_DIR=%PICARD_DIR%\nGTF=%GTF%\nGENOME_INDEX=%GENOME_INDEX%'
		expected_result = 'STAR=STARPATH\nSAMTOOLS=SAM\nPICARD_DIR=PIC\nGTF=my.gtf\nGENOME_INDEX=GI'
		p = Params()
		p.add(star_align = 'STARPATH')
		p.add(samtools = 'SAM')
		p.add(gtf = 'my.gtf')
		p.add(star_genome_index= 'GI')
		p.add(picard = 'PIC') 
		myproject = Project()
		myproject.parameters = p

		result = self.module.fill_out_general_template_portion(myproject, template)
		self.assertEqual( result, expected_result)


	def test_sample_specific_template_injected_correctly_for_single_end_alignment(self):
		sample_template = 'FASTQFILEA=%FASTQFILEA%\nFASTQFILEB=%FASTQFILEB%\nSAMPLE_NAME=%SAMPLE_NAME%\nPAIRED=%PAIRED%\nOUTDIR=%OUTDIR%\nFCID=%FCID%\nLANE=%LANE%\nINDEX=%INDEX%\n'
		expected_result = 'FASTQFILEA=/path/to/ABC_r1_001.fastq.gz\nFASTQFILEB=\nSAMPLE_NAME=ABC\nPAIRED=0\nOUTDIR=/path/to/aln\nFCID=DEFAULT\nLANE=0\nINDEX=DEFAULT_INDEX\n'
		s = Sample('ABC', 'X', read_1_fastq = '/path/to/ABC_r1_001.fastq.gz')
		s.alignment_dir = '/path/to/aln'
		s.flowcell_id = 'DEFAULT'
		s.lane = '0'
		s.index = 'DEFAULT_INDEX'
		result = self.module.fill_out_sample_specific_portion(s, sample_template)
		self.assertEqual(result, expected_result)


	def test_sample_specific_template_injected_correctly_for_paired_alignment(self):
		sample_template = 'FASTQFILEA=%FASTQFILEA%\nFASTQFILEB=%FASTQFILEB%\nSAMPLE_NAME=%SAMPLE_NAME%\nPAIRED=%PAIRED%\nOUTDIR=%OUTDIR%\nFCID=%FCID%\nLANE=%LANE%\nINDEX=%INDEX%\n'
		expected_result = 'FASTQFILEA=/path/to/ABC_r1_001.fastq.gz\nFASTQFILEB=/path/to/ABC_r2_001.fastq.gz\nSAMPLE_NAME=ABC\nPAIRED=1\nOUTDIR=/path/to/aln\nFCID=DEFAULT\nLANE=0\nINDEX=DEFAULT_INDEX\n'
		s = Sample('ABC', 'X', read_1_fastq = '/path/to/ABC_r1_001.fastq.gz', read_2_fastq = '/path/to/ABC_r2_001.fastq.gz')
		s.alignment_dir = '/path/to/aln'
		s.flowcell_id = 'DEFAULT'
		s.lane = '0'
		s.index = 'DEFAULT_INDEX'
		result = self.module.fill_out_sample_specific_portion(s, sample_template)
		self.assertEqual(result, expected_result)


	def test_alignment_calls(self):

		mock_process = mock.Mock(name='mock_process')
		mock_process.communicate.return_value = (('',''))
		mock_process.returncode = 0

		mock_popen = mock.Mock(name='mock_popen')
		mock_popen.return_value = mock_process
		
		self.module.subprocess = mock.Mock()
		self.module.subprocess.Popen = mock_popen
		self.module.subprocess.STDOUT = ''
		self.module.subprocess.PIPE = ''

		self.module.os.chmod = mock.Mock()
		self.module.assert_memory_reasonable = mock.Mock()
		self.module.assert_memory_reasonable.return_value = True
		p = Params()
		p.add(wait_length = '10')
		p.add(wait_cycles = '50')
		p.add(min_memory = '40')
		paths = ['/path/to/a.sh', '/path/to/b.sh']
		self.module.execute_alignments(paths, p)

		calls = [mock.call('/path/to/a.sh', shell=True, stderr=self.module.subprocess.STDOUT, stdout=self.module.subprocess.PIPE),
			mock.call('/path/to/b.sh', shell=True, stderr=self.module.subprocess.STDOUT, stdout=self.module.subprocess.PIPE)]
		self.module.subprocess.Popen.assert_has_calls(calls)


	def test_alignment_call_raises_exception(self):
		import subprocess

		mock_process = mock.Mock(name='mock_process')
		mock_process.communicate.return_value = (('',''))
		mock_process.returncode = 1

		mock_popen = mock.Mock(name='mock_popen')
		mock_popen.return_value = mock_process
		
		self.module.subprocess = mock.Mock()
		self.module.subprocess.Popen = mock_popen
		self.module.subprocess.STDOUT = ''
		self.module.subprocess.PIPE = ''

		self.module.os.chmod = mock.Mock()
		self.module.assert_memory_reasonable = mock.Mock()
		self.module.assert_memory_reasonable.return_value = True
		p = Params()
		p.add(wait_length = '10')
		p.add(wait_cycles = '50')
		p.add(min_memory = '40')
		paths = ['/path/to/a.sh', '/path/to/b.sh']
		with self.assertRaises(self.module.AlignmentScriptErrorException):
			self.module.execute_alignments(paths, p)

		# assert that the second script was not called due to the first one failing.
		calls = [mock.call('/path/to/a.sh', shell=True, stderr=self.module.subprocess.STDOUT, stdout=self.module.subprocess.PIPE)]
		self.module.subprocess.Popen.assert_has_calls(calls)


	def test_alignment_call_waits_properly(self):
		import subprocess

		mock_process = mock.Mock(name='mock_process')
		mock_process.communicate.return_value = (('',''))
		mock_process.returncode = 0

		mock_popen = mock.Mock(name='mock_popen')
		mock_popen.return_value = mock_process
		
		self.module.subprocess = mock.Mock()
		self.module.subprocess.Popen = mock_popen
		self.module.subprocess.STDOUT = ''
		self.module.subprocess.PIPE = ''

		self.module.os.chmod = mock.Mock()
		self.module.assert_memory_reasonable = mock.Mock()
		self.module.sleep = mock.Mock()
		self.module.assert_memory_reasonable.side_effect = [False, False, True, True]
		p = Params()
		p.add(wait_length = '10')
		p.add(wait_cycles = '50')
		p.add(min_memory = '40')
		paths = ['/path/to/a.sh', '/path/to/b.sh']
			
		self.module.execute_alignments(paths, p)

		# assert that the script was eventually called.
		calls = [mock.call('/path/to/a.sh', shell=True, stderr=self.module.subprocess.STDOUT, stdout=self.module.subprocess.PIPE),
			mock.call('/path/to/b.sh', shell=True, stderr=self.module.subprocess.STDOUT, stdout=self.module.subprocess.PIPE)]
		self.module.subprocess.Popen.assert_has_calls(calls)

		# assert that it had to wait twice (via calling sleep() twice)
		calls = [mock.call(600), mock.call(600)]
		self.module.sleep.assert_has_calls(calls)
	

	def test_alignment_call_timesout_properly(self):
		import subprocess
		self.module.subprocess = mock.Mock()
		self.module.os.chmod = mock.Mock()
		self.module.assert_memory_reasonable = mock.Mock()
		self.module.sleep = mock.Mock()
		self.module.assert_memory_reasonable.side_effect = [False, False, False, False]
		p = Params()
		p.add(wait_length = '10')
		p.add(wait_cycles = '3')
		p.add(min_memory = '40')
		paths = ['/path/to/a.sh']
			
		with self.assertRaises(self.module.AlignmentTimeoutException):
			self.module.execute_alignments(paths, p)


		# assert that it had to wait the proper amount of times (via calling sleep())
		calls = [mock.call(600), mock.call(600), mock.call(600)]
		self.module.sleep.assert_has_calls(calls)
	

if __name__ == "__main__":
	unittest.main()




