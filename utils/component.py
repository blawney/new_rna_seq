import sys

class Component(object):
	def __init__(self, name, directory):
		self.name = name
		self.location = directory
		self.project = None


	def __str__(self):
		s = 'Component: \n'
		s += 'name: ' + str(self.name) + '\n'
		s += 'location: '+str(self.location)
		return s


	def add_project_data(self, project):
		self.project = project


	def run(self):

		# add the directory for the module, so it is in the search path
		sys.path.append(self.location)

		# the name of the script (minus the .py) that is used to run this component
		module = self.project_params.get('entry_module')

		# the method name that launches the component
		method_name = self.project_params.get('entry_method')

		# import the method from module
		run_method = getattr(__import__(module, fromlist=[method_name]), method_name)

		run_method()
		
