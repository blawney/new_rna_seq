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

from utils.pipeline import Pipeline
from utils.custom_exceptions import *
import utils.config_parser
from utils.util_methods import *


def dummy_join(a,b):
	return os.path.join(a,b)


class TestPipeline(unittest.TestCase):
	"""
	Tests the Pipeline object
	"""

	@mock.patch('utils.util_methods.os.path.join', side_effect=dummy_join)
	@mock.patch('utils.config_parser.read_config')
	@mock.patch('utils.util_methods.os')
	def test_missing_default_pipeline_config_file(self, mock_os, mock_cfg_reader, mock_join):
		"""
		Assumptions-- os.listdir() finds a single .cfg file in the pipeline home directory.
		No config file passed via commandline.
		"""
		
		default_cfg_name = 'default.cfg'

		# mock the default config file NOT being found in the home dir: 
		mock_os.listdir.return_value = []

		# create a Pipeline object, which will be populated with the mock return dictionary
		dummy_path = "path/to/home"

		with self.assertRaises(ConfigFileNotFoundException):
			p = Pipeline(dummy_path)
			p.setup()



	@mock.patch('utils.util_methods.os.path.join', side_effect=dummy_join)
	@mock.patch('utils.config_parser.read_config')
	@mock.patch('utils.util_methods.os')
	def test_raises_exception_if_missing_pipeline_components(self, mock_os, mock_cfg_reader, mock_join):
		"""
		This covers where the genome or component directories could be missing (or the path to them is just wrong)
		"""
		
		default_cfg_name = 'default.cfg'

		# mock the default config file being found in the home dir: 
		mock_os.listdir.return_value = [default_cfg_name]
		mock_os.path.isfile.return_value = True

		# mock the return from the reader- does not matter if this is a complete list of the actual, current pipeline components/pieces--
		mock_cfg_dict = {'components_dir':'components', 'genomes_dir':'genome_info'}
		mock_cfg_reader.return_value = mock_cfg_dict

		# create a Pipeline object, which will be populated with the mock return dictionary
		dummy_path = "/path/to/pipeline_home"

		with mock.patch.object(__builtin__, 'open', mock.mock_open()) as mo:
			p = Pipeline(dummy_path)
			mock_os.path.isdir.return_value = False # this mocks the directory not being found
			with self.assertRaises(MissingComponentDirectoryException):
				# this ensures that the method looking for the directory returns a false.  Otherwise it is possible to pass
				# a 'correct' mock parameter (i.e. a directory that actually does exist) which would cause the test to fail
				mock_os.path.isdir.return_value = False   
				p.setup()


if __name__ == "__main__":
	unittest.main()
