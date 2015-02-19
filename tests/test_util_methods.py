import unittest
import mock
import sys

# for finding modules in the sibling directories
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

from utils.util_methods import *
from utils.custom_exceptions import *

def dummy_join(a,b):
	return os.path.join(a,b)

def return_false(a,b):
	return False

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
		with self.assertRaises(MultipleConfigFileFoundException):
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
		self.assertFalse(component_structure_valid(dummy_path))


	@mock.patch('utils.util_methods.os')
	@mock.patch('utils.util_methods.imp')
	def test_module_script_missing_entry_method(self, mock_imp, mock_os):
		"""
		This tests if a module is missing the 'main' script
		"""		
		mock_os.listdir.return_value = ['main.py']
		dummy_path = '/path/to/something'
		mock_module = mock.MagicMock(spec=[])
		mock_imp.load_source.return_value = mock_module

		self.assertFalse(component_structure_valid(dummy_path))



if __name__ == "__main__":
	unittest.main()
