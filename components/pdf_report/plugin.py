import logging
import sys
import os
import glob
import imp
import subprocess

sys.path.append( os.path.dirname( os.path.dirname( os.path.abspath(__file__) ) ) )

import component_utils

class PdfReportNotConfiguredForAlignerException(Exception):
	pass

def run(name, project):
	logging.info('Beginning creation of custom latex report')

	# get the location of the utils directory:
	utils_dir = project.parameters.get('utils_dir')

	# load the util_methods module:
	util_methods = component_utils.load_remote_module('util_methods', utils_dir)

	# parse this module's config file
	this_dir = os.path.dirname(os.path.realpath(__file__))
	project.parameters.add(component_utils.parse_config_file(project, this_dir))
	component_params = component_utils.parse_config_file(project, this_dir, 'COMPONENT_SPECIFIC')

	# TODO: generate report when we didn't align-- use samtools, etc. to get alignment stats
	if project.parameters.get('aligner') == 'star' and not project.parameters.get('skip_align'):
		extra_params = component_utils.parse_config_file(project, this_dir, 'STAR')		
	else:
		raise PdfReportNotConfiguredForAlignerException('Please configure the pdf report generator for this particular aligner.')

	# create a full path to the output directory for the output:
	output_dir = os.path.join(project.parameters.get('output_location'), component_params.get('report_output_dir'))
	component_params['report_output_dir']  = output_dir 

	# create the final output directory, if possible
	util_methods.create_directory(output_dir, overwrite = True)

	output_file = create_report(project, component_params, extra_params)

	# change permissions:
	os.chmod(output_file, 0775)

	# create the ComponentOutput object and return it
	c1 = component_utils.ComponentOutput(output_file, component_params.get('report_tab_title'), component_params.get('report_header_msg'), component_params.get('report_display_format'))
	return [ c1 ]


def create_report(project, component_params, extra_params = {} ):
	# returns a dict of file name mapping (e.g. what is displayed as the href element) to the file path

	generate_figures(project, component_params, extra_params)

	compile_report(project, component_params)

	return {}


def generate_figures(project, component_params, extra_params = {}):
	if project.parameters.get('aligner') == 'star' and not project.parameters.get('skip_align'):

		# a dict of dicts (sample maps to a dictionary with sample-specific key:value pairs)
		log_data = process_star_logs(project, component_params, extra_params)


def compile_report(project, component_params):
	pass



def get_bam_counts(f):
	#TODO: Write this method.  It is general, so can be used regardless of whether we aligned or not.
	# Do check issues with starting from existing BAM file-- may not have all the 'levels' of the BAM file, so the plot may not be informative
	"""
	#x=! /cccbstore-rc/projects/cccb/apps/samtools-0.1.19/samtools idxstats $f | cut -f3
	x = [int(xx) for xx in x]
	return np.sum(x)

	def get_sample_name(f):
	return os.path.basename(f).split('.')[0]

	types = ['sort.bam', 'sort.primary.bam', 'sort.primary.dedup.bam']
	count_dict = {}
	for t in types:
	files = sorted(glob.glob('*/star_align/*' + t))
	count_dict[t] = {get_sample_name(f):get_total_counts(f) for f in files}
	"""


def process_star_logs(project, component_params, extra_params):
	"""
	Returns a dictionary of dictionaries.  The outer dict maps the samples as keys to a dictionary of data parsed from the logfile (Stored in key-value pairs)
	"""
	def get_log_contents(f):
		"""
		Parses the star-created Log file to get the mapping stats.
		Input: filepath to Log file
		Output: dictionary mapping 'log terms' to the values
		"""
		d = {}
		for line in open(f):
			try:
				key, val = line.strip().split('|')
				d[key.strip()] = val.strip()
			except ValueError as ex:
				pass
		return d


	wildcard_path = os.path.join( project.parameters.get('project_directory') , project.parameters.get('sample_dir_prefix') + '*', project.parameters.get('alignment_dir'), '*' + extra_params.get('star_log_suffix'))
	logfiles = glob.glob(wildcard_path)
	#TODO: get a list of the log file pahts
	d = {}
		for log in logfiles:
			sample = os.path.basename(log)[:-len(suffix)]
			d[sample] = get_log_contents(log)
	return d









