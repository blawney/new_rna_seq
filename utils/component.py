import sys

class Component(object):
	def __init__(self, name, directory, project_params, samples):
		self.name = name
		self.location = directory
		self.project_params = project_params
		self.samples = samples


	def __str__(self):
		s = 'name: ' + str(self.name) + '\n'
		s += 'location: '+str(self.location)
		return s

	def run(self):
		sys.path.append(self.location)
		module = self.project_params.get('entry_module')
		method_name = self.project_params.get('entry_method')
		run_method = getattr(__import__(module, fromlist=[method_name]), method_name)
		run_method()
		
