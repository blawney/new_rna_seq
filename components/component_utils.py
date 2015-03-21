import imp
import sys

def load_remote_module(module_name, location):
	"""
	Loads and returns the module given by 'module_name' that resides in the given location
	"""
	sys.path.append(location)
	try:
		fileobj, filename, description = imp.find_module(module_name, [location])
		module = imp.load_module(module_name, fileobj, filename, description)
		return module
	except ImportError as ex:
		logging.error('Could not import module %s at location %s' % (module_name, location))
		raise ex


def parse_config_file(project, component_dir, section =  'DEFAULT'):
	"""
	Parses the passed component's configuration file and adds the constants to the project parameters.
	"""

	# get the location of the utils directory:
	utils_dir = project.parameters.get('utils_dir')

	# load the parser and the util_methods modules:
	config_parser = load_remote_module('config_parser', utils_dir)
	util_methods = load_remote_module('util_methods', utils_dir)

	config_filepath = util_methods.locate_config(component_dir)
	project.parameters.add(config_parser.read_config(config_filepath, section))
