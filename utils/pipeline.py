import logging
import util_methods
import config_parser as cfg_parser
from custom_exceptions import *
import os 

DEFAULT_CONTRAST = 'contrasts.txt'

class Pipeline(object):

	def __init__(self, params):
		self.params = params


	def register_components(self, components):
		self.components = components

	def summary(self):
		print '**************************'
		print self.params
		print '**************************'
		for comp in self.components:
			print comp
