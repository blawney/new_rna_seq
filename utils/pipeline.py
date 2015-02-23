import logging
import util_methods
import config_parser as cfg_parser
from component import Component
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
		self.__collect_samples()

		if not self.params.get('skip_align'):
			#call align setup
			self.__align_samples()
		else:
			pass
			#find bam files


	def __collect_samples(self):
		name_and_condition_pairings = util_methods.parse_annotation_file(self.params.get('sample_annotation_file'))
		self.samples = tuple([Sample(name, condition) for name, condition in name_and_condition_pairings])


	def __align_samples(self):
		print 'here1'
		# create a Component for the aligner
		aligner_name = self.params.get('aligner')
		aligner_dir = os.path.join(self.params.get('aligners_dir'), aligner_name)
		aligner = Component(aligner_name, aligner_dir, self.params, self.samples)
		aligner.run()







