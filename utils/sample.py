import logging

class Sample(object):

	def __init__(self, sample_name, condition, read_1_fastq = None, read_2_fastq = None, bamfiles = []):
		self.sample_name = sample_name
		self.condition = condition
		self.read_1_fastq = read_1_fastq
		self.read_2_fastq = read_2_fastq
		self.read_1_fastqc_report = None
		self.read_2_fastqc_report = None
		self.bamfiles = bamfiles
		self.flowcell_id = 'DEFAULT'
		self.lane = '0'
		self.index = 'DEFAULT_INDEX'


	def __str__(self):
		s = ''
		s += 'Sample name: ' + str(self.sample_name) + '\n'
		s += 'Condition: ' + str(self.condition) + '\n'
		s += 'Read 1 fastq: ' + str(self.read_1_fastq) + '\n'
		s += 'Read 2 fastq: ' + str(self.read_2_fastq) + '\n'
		s += 'Read 1 fastQC: ' + str(self.read_1_fastqc_report) + '\n'
		s += 'Read 2 fastQC: ' + str(self.read_2_fastqc_report) + '\n'
		s += 'BAM path: ' + str(self.bamfiles) + '\n'
		return s
