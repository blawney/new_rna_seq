import logging
from util_classes import Params
import util_methods
import config_parser as cfg_parser

class Project(object):

	def __init__(self, cl_args):
		self.project_params = Params()
		self.project_params.add(cl_args)


	def prepare(self, pipeline_params):
		self.__read_config__(pipeline_params.get('project_configurations_dir'))
		logging.info('After reading project parameters:')
		logging.info(self.project_params)
		logging.info("********************")
		logging.info(pipeline_params)

	def __read_config__(self, directory):

		# if a custom configuration file was not given in cmd line args, use default:
		if not self.project_params.get('project_configuration_file'):
			self.project_params.add( project_configuration_file = util_methods.locate_config(directory) )

		config_filepath = self.project_params.get('project_configuration_file')
		logging.info("Project configuration file is: %s", config_filepath)
		try:
			with open(config_filepath, 'r') as cfg_fileobj:
				self.project_params.add(cfg_parser.read(cfg_fileobj))
		except IOError:
			logging.error("Could not find configuration file at: %s", config_filepath)
			raise ConfigFileNotFoundException("Configuration file was not found.")
		except Exception as ex:
			raise ex
