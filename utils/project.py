
class Project(object):

	def __init__(self):
		self.parameters = None
		self.samples = None
		self.contrasts = None

	def add_parameters(self, params):
		if self.parameters:
			self.parameters += params
		else:
			self.parameters = params


	def add_samples(self, sample_list):
		self.samples = sample_list


	def add_contrasts(self, contrast_list):
		self.contrasts = contrast_list
