
class Component(object):
	def __init__(self, name, directory, project_params):
		self.name = name
		self.location = directory
		self.project_params = project_params

	def __str__(self):
		s = 'name: ' + str(self.name) + '\n'
		s += 'location: '+str(self.location)
		return s
