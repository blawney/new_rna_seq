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
	pass


if __name__ == "__main__":
	unittest.main()
