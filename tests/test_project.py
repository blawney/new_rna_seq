import logging
logging.disable(logging.CRITICAL)


import unittest
import mock
import sys
import os
import __builtin__

# for finding modules in the sibling directories
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

from utils.project import Project
from utils.custom_exceptions import *
import utils.config_parser
from utils.util_methods import *


def dummy_join(a,b):
	return os.path.join(a,b)


class TestProject(unittest.TestCase):
	"""
	Tests the Project object
	"""
	@mock.patch('utils.util_methods.os')
	def test_missing_default_config_file_with_no_alternative_given(self, mock_os):
		"""
		No config file passed via commandline and none found in the project_configuration directory
		"""
		
		# mock the missing config file: 
		mock_os.listdir.return_value = []

		# mock there being no command line arg passed for a different config file:
		mock_cl_args = {'project_configuration_file': None}
		
		# mock the pipeline params
		mock_pipeline_params = {'project_configurations_dir': '/path/to/proj_config_dir'}

		with self.assertRaises(ConfigFileNotFoundException):
			p = Project(mock_cl_args)
			p.prepare(mock_pipeline_params)


	@mock.patch('utils.util_methods.os')
	def test_missing_alternative_config_file(self, mock_os):
		"""
		Config filepath passed via commandline, but is not found.
		"""
		
		# mock a default config file (doesn't matter since the alternative takes precedent): 
		mock_os.listdir.return_value = []

		# mock there being a command line arg passed for a different config file:
		mock_cl_args = {'project_configuration_file': 'alternate.cfg'}

		# mock the pipeline params
		mock_pipeline_params = {'project_configurations_dir': '/path/to/proj_config_dir'}

		# here we mock the open() builtin method.  Without this, one could conceivably have
		# the above (intended fake) file in their filesystem, which would cause the test to fail (since said file
		# is, in fact, present).  If the file is not present, open() raises IOError.
		with mock.patch.object(__builtin__, 'open', mock.mock_open()) as mo:
			mo.side_effect = IOError
			with self.assertRaises(ConfigFileNotFoundException):
				p = Project(mock_cl_args)
				p.prepare(mock_pipeline_params)


	@mock.patch('utils.util_methods.os.path.join', side_effect=dummy_join)
	@mock.patch('utils.util_methods.os')
	def test_multiple_config_file_with_no_alternative_given(self, mock_os, mock_join):
		"""
		No config file passed via commandline and multiple found in the project_configurations directory
		"""
		
		# mock the multiple config files: 
		mock_os.listdir.return_value = ['a.cfg','b.cfg']

		# mock there being no command line arg passed for a different config file:
		mock_cl_args = {'project_configuration_file': None}

		# mock the pipeline params
		mock_pipeline_params = {'project_configurations_dir': '/path/to/proj_config_dir'}

		with self.assertRaises(MultipleConfigFileFoundException):
			p = Project(mock_cl_args)
			p.prepare(mock_pipeline_params)




if __name__ == "__main__":
	unittest.main()
