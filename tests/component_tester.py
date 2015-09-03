import unittest
import sys
import imp
from os import path

class ComponentTester(object):
	"""
	Creates a common parent class for all the component testing modules.  Loads the module to be tested.
	"""
	def loader(self, module_directory):
		"""
		The 'module_directory' argument is relative to the root directory (where the main launcher script resides)
		"""
		root = path.dirname( path.dirname( path.abspath(__file__) ) ) 
		self.module_directory = path.join(root, module_directory)

		try:
			sys.path.append(self.module_directory)
			module_name = 'plugin' 
			fileobj, filename, description = imp.find_module(module_name, [self.module_directory])
			self.module = imp.load_module(module_name, fileobj, filename, description)
		except ImportError as ex:
			print 'Could not load the plugin module in %s ' % module_directory
			print ex.message
			sys.exit(1) 
