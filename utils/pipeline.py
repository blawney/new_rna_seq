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

	def run(self):
		self.collect_samples()


	def collect_samples(self):
		name_and_condition_pairings = util_methods.parse_annotation_file(self.params.get('sample_annotation_file'))
		self.samples = tuple([Sample(name, condition) for name, condition in name_and_condition_pairings])
