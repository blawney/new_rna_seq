import logging
import sys
import os
import imp
import subprocess

sys.path.append( os.path.dirname( os.path.dirname( os.path.abspath(__file__) ) ) )

import component_utils

class CountfileQuantityException(Exception):
	pass

class MissingBamFileException(Exception):
	pass

def run(project):
	logging.info('Beginning featureCounts component of pipeline.')

	# get the location of the utils directory:
	utils_dir = project.parameters.get('utils_dir')

	# load the parser and the util_methods modules:
	config_parser = component_utils.load_remote_module('config_parser', utils_dir)
	util_methods = component_utils.load_remote_module('util_methods', utils_dir)

	# parse this module's config file
	component_utils.parse_config_file(project, util_methods, config_parser, os.path.dirname(os.path.realpath(__file__)))

	# create a full path to the output directory for the featureCount's output and reset the parameter in the project parameters:
	output_dir = os.path.join(project.parameters.get('output_location'), project.parameters.get('feature_counts_output_dir'))
	project.parameters.reset_param('feature_counts_output_dir', output_dir)

	# create the final output directory, if possible
	util_methods.create_directory(output_dir)

	# start the counting:
	execute_counting(project, util_methods)

	# create the final, unnormalized count matrices for each set of BAM files
	merged_count_files = create_count_matrices(project, util_methods)
	
	# add to the project object:
	project.count_matrices = merged_count_files


def create_count_matrices(project, util_methods):
	"""
	In general, there are a set of countfiles for each sample, corresponding to each bamfile.  This method takes the countfile of each 'type' across all samples
	and creates a count matrix such that the genes are in rows and the samples are in columns.  In the end, each 'type' of bamfile (e.g. primary, deduped) will have
	a full count matrix.

	This method iterates through each set of countfiles and writes the countfiles to the appropriate location.  It then returns a list of the paths for all
	of the count matrices
	"""
	merged_count_files = []
	sample_names = sorted([s.sample_name for s in project.samples])
	header_line = ['Gene'] + sample_names

	file_groups = get_countfile_groupings(project, util_methods.case_insensitive_glob)
	
	for file_group in file_groups:
		files = sorted(file_group)
		group_suffix = os.path.basename(files[0]).lstrip(sample_names[0])
		matrix = []
		for f in files:
			read(matrix,f)	

		matrix.insert(0, header_line)
		outfilepath = os.path.join(os.path.dirname(files[0]), project.parameters.get('count_matrix_file_prefix') + group_suffix)
		merged_count_files.append(outfilepath)
		with open(outfilepath, 'w') as outfile:
			for row in matrix:
				outfile.write('\t'.join(row) + '\n')
	return merged_count_files


def read(matrix, filepath):
	"""
	This is a helper method for create_count_matrices(...) that assembles the count matrix by sequentially appending columns as new samples are read/parsed.
	Adds (in-place) to the existing matrix passed as the first argument.    
	"""
	was_empty = True if len(matrix) == 0 else False
	with open(filepath) as f:
		for i, line in enumerate(f):
			if i > 1:
				contents = line.strip().split()
				if was_empty:
					matrix.append([contents[0], contents[6]])
				else:
					matrix[i-2].append(contents[6]) # the (i-2) corrects for the offset due to the two header lines



def get_countfile_groupings(project, case_insensitive_glob):
	"""
	This method aggregates all the countfiles generated from each 'type' of bam file and returns the full filepaths as a list of lists.  
	That is, we may have multiple bam files for each sample (e.g. primary alignments, deduplicated, etc).
	We will be generating a countfile for each one of those.  
	When we assemble into a count matrix, we obviously group the files of a particular 'type' (e.g. those coming from deduplicated BAM files).
	"""
	# get handles (i.e. file suffixes) for all the different count files that were created and make wildcard patterns:
	s = project.samples[0]
	extensions = ['*' + os.path.basename(countfile).lstrip(s.sample_name) for countfile in s.countfiles]

	# create full paths by appending the location of the directory for featureCounts output:
	paths = [os.path.join(project.parameters.get('feature_counts_output_dir'), p) for p in extensions]

	# get the full groups of the countfiles
	file_groups = map(case_insensitive_glob, paths)

	# if there are missing files (e.g. a particular sample does not have a countfile that the other samples have), raise an error:
	sample_count = len(project.samples)
	for grouping in file_groups:
		if len(grouping) != sample_count:
			logging.error('There were %s samples in total.  However, the number of countfiles was not equal to this.' % sample_count)
			logging.error(grouping)
			raise CountfileQuantityException('The number of countfiles did not match the number of samples.  Check log.')
	return file_groups



def execute_counting(project, util_methods):
	"""
	Creates the calls and executes the system calls for running featureCounts
	"""
	logging.info('Begin counting reads in the BAM files.')
	
	# default options, as a list of tuples:
	default_options = [('-a', project.parameters.get('gtf')),('-t', 'exon'),('-g', 'gene_name')]
	base_command = project.parameters.get('feature_counts') + ' ' + ' '.join(map(lambda x: ' '.join(x), default_options))

	# if a paired experiment, count the fragments, not the single reads
	if project.parameters.get('paired_alignment'):
		base_command += ' -p'

	for sample in project.samples:
		countfiles = []
		for bamfile in sample.bamfiles:
			if os.path.isfile(bamfile):
				output_name = util_methods.case_insensitive_rstrip(os.path.basename(bamfile), 'bam') + project.parameters.get('feature_counts_file_extension')
				output_path = os.path.join(project.parameters.get('feature_counts_output_dir'), output_name)
				command = base_command + ' -o ' + output_path + ' ' + bamfile
				try:
					logging.info('Calling featureCounts with: ')
					logging.info(command)
					subprocess.check_call(command, shell = True)
					countfiles.append(output_path)
				except subprocess.CalledProcessError as ex:
					logging.error('There was an error encountered during execution of featureCounts for sample %s ' % sample.sample_name)
					raise ex
			else:
				logging.error('The bamfile (%s) is not actually a file.' % bamfile)
				raise MissingBamFileException('Missing BAM file: %s' % bamfile)

		# keep track of the count files in the sample object:
		sample.countfiles = countfiles



