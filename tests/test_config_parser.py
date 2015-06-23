import logging
logging.disable(logging.CRITICAL)


import unittest
import mock
import sys
import os
import StringIO

# for finding modules in the sibling directories
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

import utils.config_parser
from utils.custom_exceptions import * 	


class TestConfigParser(unittest.TestCase):

	def test_parser_correctly_returns_dict(self):
		'''
		Checks that the parser returns the expected dictionary of values
		'''

		# sample text from a config file		
		cfg_text = "[dummy_section] \na = 1 \nb = x \n[desired_section] \nc=foo \nd=bar"
		
		# expected dictionary result:
		expected_result = {'a':'1', 'b':'x', 'c':'foo', 'd': 'bar'}

		#create a fake config file-like object using StringIO
		fake_file = StringIO.StringIO()
		fake_file.write(cfg_text)
		fake_file.seek(0)

		result = utils.config_parser.parse(fake_file, '')
		self.assertEqual(result, expected_result)


	def test_parser_correctly_parses_comma_list(self):
		'''
		The config files can contain comma-separated values-- ensure that the key gets mapped to a tuple composed of those comma-separated vals
		'''

		# sample text from a config file		
		cfg_text = "[dummy_section] \na = 1 \nb = x, y, z"
		
		# expected dictionary result:
		expected_result = {'a':'1', 'b':('x','y','z')}

		#create a fake config file-like object using StringIO
		fake_file = StringIO.StringIO()
		fake_file.write(cfg_text)
		fake_file.seek(0)

		result = utils.config_parser.parse(fake_file, '')
		self.assertEqual(result, expected_result)

	def test_parser_correctly_parses_single_item_comma_list(self):
		'''
		The config files can contain comma-separated values-- ensure that the key gets mapped to a tuple composed of those comma-separated vals
		'''

		# sample text from a config file		
		cfg_text = "[dummy_section] \na = 1 \nb = x, "
		
		# expected dictionary result:
		expected_result = {'a':'1', 'b':('x')}

		#create a fake config file-like object using StringIO
		fake_file = StringIO.StringIO()
		fake_file.write(cfg_text)
		fake_file.seek(0)

		result = utils.config_parser.parse(fake_file, '')
		self.assertEqual(result, expected_result)


	def test_parser_correctly_returns_selected_section(self):
		'''
		The config files can have multiple sections-- see that we correctly can get only a single section
		'''

		# sample text from a config file		
		cfg_text = "[dummy_section] \na = 1 \nb = x \n[desired_section] \nc=foo \nd=bar"
		
		# expected dictionary result:
		expected_result = {'c':'foo', 'd': 'bar'}

		#create a fake config file-like object using StringIO
		fake_file = StringIO.StringIO()
		fake_file.write(cfg_text)
		fake_file.seek(0)

		result = utils.config_parser.parse(fake_file, 'desired_section')
		self.assertEqual(result, expected_result)


	def test_raises_exception_if_section_missing(self):
		'''
		The config files can have multiple sections-- see that we raise an exception if we ask for a section that is not in the file
		'''

		# sample text from a config file		
		cfg_text = "[dummy_section] \na = 1 \nb = x \n[desired_section] \nc=foo \nd=bar"

		#create a fake config file-like object using StringIO
		fake_file = StringIO.StringIO()
		fake_file.write(cfg_text)
		fake_file.seek(0)

		with self.assertRaises(MissingConfigFileSectionException):
			utils.config_parser.parse(fake_file, 'junk')


	def test_parser_returns_only_default_section_when_specified(self):
		# sample text from a config file		
		cfg_text = "[DEFAULT] \na = 1 \nb = x \n[desired_section] \nc=foo \nd=bar"

		#create a fake config file-like object using StringIO
		fake_file = StringIO.StringIO()
		fake_file.write(cfg_text)
		fake_file.seek(0)

		# expected dictionary result:
		expected_result = {'a':'1', 'b': 'x'}
		result = utils.config_parser.parse(fake_file, 'DEFAULT')
		self.assertEqual(result, expected_result)



	def test_parser_returns_correctly_with_default(self):
		"""
		Returns the desired section AND the DEFAULT section if [DEFAULT] section present
		"""
		# sample text from a config file		
		cfg_text = "[DEFAULT] \na = 1 \nb = x \n[desired_section] \nc=foo \nd=bar"

		#create a fake config file-like object using StringIO
		fake_file = StringIO.StringIO()
		fake_file.write(cfg_text)
		fake_file.seek(0)

		# expected dictionary result:
		expected_result = {'a':'1', 'b': 'x','c':'foo', 'd': 'bar'}
		result = utils.config_parser.parse(fake_file, 'desired_section')
		self.assertEqual(result, expected_result)

if __name__ == "__main__":
	unittest.main()
