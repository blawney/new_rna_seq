import os
import imp

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
		fileobj, filename, description = imp.find_module(module_name, [self.location])
		module = imp.load_module(module_name, fileobj, filename, description)
		run_method = getattr(module, method_name)

		# run the component:
		run_method(self.project)
		
