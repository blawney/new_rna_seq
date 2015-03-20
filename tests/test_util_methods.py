import logging
logging.disable(logging.CRITICAL)

import unittest
import mock
import sys
import __builtin__
from StringIO import StringIO

# for finding modules in the sibling directories
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

from utils.util_methods import *
from utils.custom_exceptions import *

def dummy_join(a,b):
	return os.path.join(a,b)


def create_mock_open(fileobj):

	mock_obj = mock.MagicMock(spec = file)
	mock_obj.__enter__.return_value = fileobj
	mock_obj.return_value = mock_obj
	return mock_obj


class UtilMethodsTest(unittest.TestCase):

	@mock.patch('utils.util_methods.os')
	def test_missing_file_raises_exception(self, mock_os):

		mock_os.path.isfile.return_value = False
		with self.assertRaises(MissingFileException):
			check_for_file('/path/to/nothing')


	@mock.patch('utils.util_methods.os')
	def test_missing_config_file_raises_exception(self, mock_os):

		mock_os.listdir.return_value = []
		with self.assertRaises(ConfigFileNotFoundException):
			locate_config('/path/to/dir')


	@mock.patch('utils.util_methods.os.path.join', side_effect=dummy_join)
	@mock.patch('utils.util_methods.os')
	def test_multiple_config_files_raises_exception(self, mock_os, mock_join):
		"""
		Tests multiple configuration files with no way to distinguish via the prefix arg
		"""
		mock_os.listdir.return_value = ['a.cfg','b.cfg']
		with self.assertRaises(MultipleFileFoundException):
			locate_config('/path/to/dir')


	@mock.patch('utils.util_methods.os.path.join', side_effect=dummy_join)
	@mock.patch('utils.util_methods.os')
	def test_finds_file_with_desired_prefix(self, mock_os, mock_join):
		mock_path = '/path/to/dir'
		mock_os.listdir.return_value = ['hg19.cfg', 'mm10.cfg']
		self.assertEqual(locate_config(mock_path, 'hg19'), os.path.join(mock_path, 'hg19.cfg'))


	@mock.patch('utils.util_methods.os.path.join', side_effect=dummy_join)
	@mock.patch('utils.util_methods.os')
	def test_single_config_file(self, mock_os, mock_join):

		mock_os.listdir.return_value = ['a.cfg']
		self.assertEqual(locate_config('/path/to/dir'), '/path/to/dir/a.cfg')


	@mock.patch('utils.util_methods.os')
	def test_missing_module_script(self, mock_os):
		"""
		This tests if a module is missing the 'main' script
		"""		
		mock_os.listdir.return_value = []
		dummy_path = '/path/to/nothing'
		self.assertFalse(component_structure_valid(dummy_path, 'script.py', 'run'))


	@mock.patch('utils.util_methods.os')
	@mock.patch('utils.util_methods.imp')
	def test_module_script_missing_entry_method(self, mock_imp, mock_os):
		"""
		This tests if a module is missing the 'main' script
		"""		
		mock_os.listdir.return_value = ['script.py']
		dummy_path = '/path/to/something'
		mock_module = mock.MagicMock(spec=[])
		mock_imp.load_source.return_value = mock_module

		self.assertFalse(component_structure_valid(dummy_path, 'script.py', 'run'))


	def test_parse_annotation_file(self):
		mock_data = 'A\tX\nB\tX\nC\tY'
		expected_result = set([('A','X'),('B','X'),('C','Y')])
		mock_data = StringIO(mock_data)
		mock_open = create_mock_open(mock_data)
		with mock.patch.object(__builtin__, 'open', mock_open) as mo:
			self.assertEqual(parse_annotation_file('/path/to/file'), expected_result)



	def test_malformatted_annotation_file_raises_exception(self):
		mock_data = 'A\tX\nB\nC\tY'
		expected_result = [('A','X'),('B','X'),('C','Y')]
		mock_data = StringIO(mock_data)
		mock_open = create_mock_open(mock_data)
		with mock.patch.object(__builtin__, 'open', mock_open) as mo:
			with self.assertRaises(AnnotationFileParseException):
				parse_annotation_file('/path/to/file')


	def test_missing_annotation_file_raises_exception(self):
		mock_open = mock.Mock(side_effect = IOError)
		with mock.patch.object(__builtin__, 'open', mock_open) as mo:
			with self.assertRaises(AnnotationFileParseException):
				parse_annotation_file('/path/to/file')



	@mock.patch('utils.util_methods.os')
	def test_does_not_write_output_into_existing_directory(self, mock_os):
		
		mock_os.path.isdir.return_value = True
		self.assertRaises(CannotMakeOutputDirectoryException, create_directory, "some/path")
	
	
	@mock.patch('utils.util_methods.os')
	def test_fails_to_create_new_directory_where_blocked(self, mock_os):
		
		mock_os.path.isdir.return_value = False
		mock_os.access.return_value = False
		self.assertRaises(CannotMakeOutputDirectoryException, create_directory, "some/path")
	
	
	@mock.patch('utils.util_methods.os')
	def test_create_new_directory(self, mock_os):
		
		mock_os.path.isdir.return_value = False
		create_directory("some/path")
		self.assertTrue(mock_os.makedirs.called, "Did not call the os.makedirs() method")


	@mock.patch('utils.util_methods.os.path.join', side_effect = dummy_join)
	@mock.patch('utils.util_methods.os')
	def test_find_file_returns_single_file(self, mock_os, my_join):
		"""
		Tests that the correct file is returned for several cases.
		"""
		project_home = '/path/to/project/dir'
		mock_os.walk.return_value = [('/path/to/project/dir', ['Sample_A', 'Sample_B'], ['C.sort.primary.bam']),
			('/path/to/project/dir/Sample_A', ['another_dir'], ['A.sort.primary.bam']),
			('/path/to/project/dir/Sample_B', [], ['B.sort.primary.bam']),
			('/path/to/project/dir/Sample_A/another_dir', [], ['A.sort.bam']),
			]
		sample_name = 'A'
		pattern = sample_name + '.*?' + 'sort.primary.bam'
		result_1 = find_files(project_home, pattern)
		expected_result_1 = [os.path.join(project_home,'Sample_A/A.sort.primary.bam')]

		sample_name = 'A'
		pattern = sample_name + '.*?' + 'sort.bam'
		result_2 = find_files(project_home, pattern)
		expected_result_2 = [os.path.join(project_home,'Sample_A/another_dir/A.sort.bam')]

		sample_name = 'C'
		pattern = sample_name + '.*?' + 'bam'
		result_3 = find_files(project_home, pattern)
		expected_result_3 = [os.path.join(project_home,'C.sort.primary.bam')]

		self.assertEqual(result_1, expected_result_1)
		self.assertEqual(result_2, expected_result_2)
		self.assertEqual(result_3, expected_result_3)


	@mock.patch('utils.util_methods.os.path.join', side_effect = dummy_join)
	@mock.patch('utils.util_methods.os')
	def test_find_file_raises_exception_if_pattern_not_matched(self, mock_os, my_join):
		"""
		Tests that an exception is raised if we are searching for a file that does not match the desired pattern
		"""
		project_home = '/path/to/project/dir'
		mock_os.walk.return_value = [('/path/to/project/dir', ['Sample_A', 'Sample_B'], ['C.sort.primary.bam']),
			('/path/to/project/dir/Sample_A', ['another_dir'], ['A.sort.primary.bam']),
			('/path/to/project/dir/Sample_B', [], ['B.sort.primary.bam']),
			('/path/to/project/dir/Sample_A/another_dir', [], ['A.sort.bam']),
			]
		sample_name = 'B'
		# above we have a file 'B.sort.primary.bam'.  Search for something that should NOT be there.
		pattern = sample_name + '.*?' + 'sort.bam'

		with self.assertRaises(MissingFileException):
			f=find_files(project_home, pattern)


	@mock.patch('utils.util_methods.os.path.join', side_effect = dummy_join)
	@mock.patch('utils.util_methods.os')
	def test_find_files_returns_multiple_files(self, mock_os, my_join):
		"""
		Tests the case where the search term is more broad and several matches are found
		"""
		project_home = '/path/to/project/dir'
		mock_os.walk.return_value = [('/path/to/project/dir', ['Sample_A', 'Sample_B'], ['C.sort.primary.bam']),
			('/path/to/project/dir/Sample_A', ['another_dir'], ['A.sort.primary.bam']),
			('/path/to/project/dir/Sample_B', [], ['B.sort.primary.bam']),
			('/path/to/project/dir/Sample_A/another_dir', [], ['A.sort.bam']),
			]
		sample_name = 'A'
		# above we have two files that match the 'A.*?bam' pattern
		pattern = sample_name + '.*?' + 'bam'

		f=find_files(project_home, pattern)
		expected_result = ['/path/to/project/dir/Sample_A/A.sort.primary.bam','/path/to/project/dir/Sample_A/another_dir/A.sort.bam']
		self.assertEqual(f, expected_result)



	def test_case_insensitive_regex_generator_for_character(self):
		c = 'a'
		expected_result = '[aA]'
		result = either_case(c)
		self.assertEqual(expected_result, result)

	def test_case_insensitive_regex_generator_for_number(self):
		c = '1'
		expected_result = '1'
		result = either_case(c)
		self.assertEqual(expected_result, result)

	def test_case_insensitive_rstrip(self):
		s = 'something.BaM'
		expected_result = 'something'
		result = case_insensitive_rstrip(s, '.bam')
		self.assertEqual(expected_result, result)


if __name__ == "__main__":
	unittest.main()
