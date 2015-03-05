import logging
import util_methods
import config_parser as cfg_parser
from component import Component
from custom_exceptions import *
import os

DEFAULT_CONTRAST = 'contrasts.txt'

class Pipeline(object):

	def __init__(self):
		self.components = None
		self.project = None


	def register_components(self, components):
		self.components = components


	def add_project(self, project):
		self.project = project


	def summary(self):
		print '**************************'
		print self.project.parameters
		print '**************************'
		for comp in self.components:
			print comp

		print '**************************'
		for s in self.project.samples:
			print s
		print '**************************'
		print '**************************'
		print self.project.contrasts
		print '**************************'

	def run(self):

		if not self.project.parameters.get('skip_align'):			

			#call align setup
			self.__align_samples()


	def __align_samples(self):
		print 'in align...'
		"""
		# create a Component for the aligner
		aligner_name = self.project.parameters.get('aligner')
		aligner_dir = os.path.join(self.project.parameters.get('aligners_dir'), aligner_name)
		aligner = Component(aligner_name, aligner_dir, self.params, self.sample_list)
		aligner.run()
		"""







