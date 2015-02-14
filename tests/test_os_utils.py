import unittest
import mock
import sys

# for finding modules in the sibling directories
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

from utils.os_utils import *
from utils.custom_exceptions import CannotMakeOutputDirectoryException

class OSUtilsTest(unittest.TestCase):
	
	@mock.patch('utils.os_utils.os')
	def test_does_not_write_output_into_existing_directory(self, mock_os):
		
		mock_os.path.isdir.return_value = True
		self.assertRaises(CannotMakeOutputDirectoryException, create_directory, "some/path")
	
	
	@mock.patch('utils.os_utils.os')
	def test_fails_to_create_new_directory_where_blocked(self, mock_os):
		
		mock_os.path.isdir.return_value = False
		mock_os.access.return_value = False
		self.assertRaises(CannotMakeOutputDirectoryException, create_directory, "some/path")
	
	
	@mock.patch('utils.os_utils.os')
	def test_create_new_directory(self, mock_os):
		
		mock_os.path.isdir.return_value = False
		create_directory("some/path")
		self.assertTrue(mock_os.makedirs.called, "Did not call the os.makedirs() method")
	

if __name__ == "__main__":
	unittest.main()
