import logging

class Sample(object):

	def __init__(self, sample_name, condition, read_1_fastq = None, read_2_fastq = None, bamfile = None):
		self.sample_name = sample_name
		self.condition = condition
		self.read_1_fastq = read_1_fastq
		self.read_2_fastq = read_2_fastq
		self.bamfile = bamfile


	def __str__(self):
		s = ''
		s += 'Name: ' + str(self.sample_name) + '\n'
		s += 'Condition: ' + str(self.condition) + '\n'
		s += 'Read 1 fastq: ' + str(self.read_1_fastq) + '\n'
		s += 'Read 2 fastq: ' + str(self.read_2_fastq) + '\n'
		s += 'BAM path: ' + str(self.bamfile) + '\n'
		return s

	"""
		self.align_script_template = None
		self.samplesheet = None
		self.sample_dir = None
		self.fastq_a = None
		self.fastq_b = None
		self.sequencing_info_dict = None
	"""
