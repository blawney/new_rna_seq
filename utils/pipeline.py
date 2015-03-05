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


	def add_samples(self, sample_list):
		self.sample_list = sample_list

	def add_contrasts(self, contrasts):
		self.contrasts = contrasts


	def summary(self):
		print '**************************'
		print self.params
		print '**************************'
		for comp in self.components:
			print comp

		print '**************************'
		for s in self.sample_list:
			print s
		print '**************************'
		print '**************************'
		print self.contrasts
		print '**************************'

	def run(self):

		if not self.params.get('skip_align'):			

			#call align setup
			self.__align_samples()


	def __align_samples(self):
		print 'here1'
		# create a Component for the aligner
		aligner_name = self.params.get('aligner')
		aligner_dir = os.path.join(self.params.get('aligners_dir'), aligner_name)
		aligner = Component(aligner_name, aligner_dir, self.params, self.sample_list)
		aligner.run()







