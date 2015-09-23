import os
import imp
import logging

class UnknownComponentTypeException(Exception):
	pass

class Component(object):

	COMPONENT_TYPES = ['STANDARD', 'ANALYSIS']

	def __init__(self, name, directory, component_type = 'STANDARD'):
		self.name = name
		self.location = directory
		self.project = None
		self.completed = False # keeps track of whether the component has been executed successfully.
		self.outputs = [] 

		if component_type in Component.COMPONENT_TYPES:
			self.component_type = component_type
		else:
			raise UnknownComponentTypeException('Exception when setting the type of Component object.  The value %s was passed, and the acceptable values are %s.' % (t, COMPONENT_TYPES))


	def __str__(self):
		s = 'Component name: ' + str(self.name) + '\n'
		s += 'location: '+str(self.location)
		return s


	def add_project_data(self, project):
		"""
		Adds a reference to a Project object.  This way the Component has access to the various parameters/constants 
		"""
		self.project = project


	def run(self):

		# in the case of components that can be re-run (e.g. report generation components which can be produced at various points in the pipeline)
		# we need to reset this, so it doesn't save the older result
		self.outputs = []

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

			# run the component and add the output objects to this object:
			self.outputs.extend(run_method(self.name, self.project))

		except ImportError as ex:
			logging.error('ImportError: Could not load the module at %s ' % filename)
			raise ex
		except Exception as ex:
			logging.error('''Some other exception was thrown while loading and running module.  If the exception message is vague, 
					 try importing this module directly in the interpreter-- could be due to simple syntax error''')
			raise ex
 
		
