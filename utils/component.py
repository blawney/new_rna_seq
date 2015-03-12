import os
import imp
import logging

class Component(object):
	def __init__(self, name, directory):
		self.name = name
		self.location = directory
		self.project = None


	def __str__(self):
		s = 'Component name: ' + str(self.name) + '\n'
		s += 'location: '+str(self.location)
		return s


	def add_project_data(self, project):
		self.project = project


	def run(self):

		# the name of the script (minus the .py) that is used to run this component
		module_name = self.project.parameters.get('entry_module')

		# the method name that launches the component
		method_name = self.project.parameters.get('entry_method')

		# import the method from module
		try:
			logging.info('Attempting to locate and load module for component: %s in %s ' % (self.name, self.location))
			fileobj, filename, description = imp.find_module(module_name, [self.location])
			module = imp.load_module(module_name, fileobj, filename, description)
			
			run_method = getattr(module, method_name)

			# run the component:
			run_method(self.project)
		except ImportError as ex:
			logging.error('ImportError: Could not load the module at %s ' % filename)
			raise ex
		except Exception as ex:
			logging.error('''Some other exception was thrown while loading and running module.  If the exception message is vague, 
					 try importing this module directly in the interpreter-- could be due to simple syntax error''')
			raise ex
 
		
