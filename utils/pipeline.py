import logging
import util_methods
import config_parser as cfg_parser
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


	def print_summary(self):
		logging.info('Configuration parameters:\n%s' % self.project.parameters)
		logging.info('Pipeline components (in order to be executed):\n%s' % '\n'.join(str(c) for c in self.components))
		logging.info('Samples:\n%s' % '\n'.join(str(s) for s in self.project.samples))
		if not self.project.parameters.get('skip_analysis'):
			logging.info('Contrasts:\n%s' % '\n'.join(map( lambda x: str(x[0])+ ' versus ' + str(x[1]) ,self.project.contrasts)))
		else:
			logging.info('No contrasts since skipping downstream analysis.')


	def run(self):
		if self.project and len(self.project.samples) > 0:
			for component in self.components:
				component.add_project_data(self.project)
				component.run()
		else:
			logging.error('Could not run the pipeline since no project was added, or there were zero samples detected.')
			raise Exception('There was nothing to run.  Check the Samples were properly added to the project.')






