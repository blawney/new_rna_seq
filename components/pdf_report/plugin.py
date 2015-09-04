import logging
import sys
import os
import glob
import imp
import subprocess
import general_plots
import numpy as np
import StringIO 
import jinja2
import star_methods
import shutil

sys.path.append( os.path.dirname( os.path.dirname( os.path.abspath(__file__) ) ) )

import component_utils

class PdfReportNotConfiguredForAlignerException(Exception):
	pass


class MissingBamIndexFile(Exception):
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

	# read template
	env = jinja2.Environment(loader=jinja2.FileSystemLoader(this_dir))
	template = env.get_template(component_params.get('report_template'))
	output_file = create_report(template, project, component_params, extra_params)

	# change permissions:
	os.chmod(output_file, 0775)

	# create the ComponentOutput object and return it
	c1 = component_utils.ComponentOutput(output_file, component_params.get('report_tab_title'), component_params.get('report_header_msg'), component_params.get('report_display_format'))
	return [ c1 ]


def create_report(template, project, component_params, extra_params = {} ):
	# returns a dict of file name mapping (e.g. what is displayed as the href element) to the file path

	generate_figures(project, component_params, extra_params)

	fill_template(template, project, component_params)

	compile_report(project, component_params)

	return {}


def generate_figures(project, component_params, extra_params = {}):

	if project.parameters.get('aligner') == 'star' and not project.parameters.get('skip_align'):

		# a dict of dicts (sample maps to a dictionary with sample-specific key:value pairs)
		log_data = star_methods.process_star_logs(project, extra_params)
		plot_path = os.path.join(component_params.get('report_output_dir'), extra_params.get('mapping_composition_fig'))
		component_params['mapping_composition_fig'] = plot_path
		star_methods.plot_read_composition(log_data, extra_params.get('log_targets'), plot_path, extra_params.get('mapping_composition_colors'))

		plot_path = os.path.join(component_params.get('report_output_dir'), component_params.get('total_reads_fig'))
		component_params['total_reads_fig'] = plot_path
		star_methods.plot_total_read_count(log_data, plot_path)

	# other plots that do not require aligner-specific methods:

	# the read counts in the various bam files
	bam_count_data = get_bam_counts(project, component_params)
	bam_count_plot_path = os.path.join(component_params.get('report_output_dir'), component_params.get('bamfile_reads_fig'))
	general_plots.plot_bam_counts(bam_count_data, bam_count_plot_path)

	# the coverage plots for the 'usual' chromosomes
	calculate_coverage_data(project, component_params)
	general_plots.plot_coverage(project, component_params)



def calculate_coverage_data(project, component_params):
	target_bam_suffix = project.parameters.get('bam_filter_level')

	for sample in project.samples:

		target_bamfile = [s for s in sample.bamfiles if s.lower().endswith(target_bam_suffix.lower() + '.bam')]

		if len(target_bamfile) == 1:
			bam = target_bamfile[0]
			cvg_filepath = os.path.join( component_params.get('report_output_dir'), sample.sample_name + '.' + target_bam_suffix + '.' + component_params.get('coverage_file_suffix'))
			bedtools_args = [ component_params.get('bedtools_path'), component_params.get('bedtools_cmd'), '-ibam', bam, '-bga']

			with open(cvg_filepath, 'w') as cvg_filehandle:
				p = subprocess.Popen(bedtools_args, stderr=subprocess.STDOUT, stdout=cvg_filehandle)
			stdout, stderr = p.communicate()

			logging.info('STDERR from bedtools genomecov call: ')
			logging.info(stderr)

		else:
			logging.error('Could not find a BAM file ending with %s for sample %s.  Not exiting, but this is likely indicative of a problem')



def fill_template(template, project, component_params):

	# since inserting into a latex doc, need to escape underscores!
	escape = lambda x: x.replace('_', '\_')

	project_id = os.path.basename(project.parameters.get('project_directory'))
	output_tex = os.path.join(component_params.get('report_output_dir'), project_id + '.tex')
	
	# construct the context:

	sample_and_group_pairs = [ (escape(sample.sample_name), escape(sample.condition)) for sample in project.samples ]
	contrast_pairs = [ (escape(cp[0]), escape(cp[1])) for cp in project.contrasts ]

	full_suffix = project.parameters.get('bam_filter_level') + '.' + component_params.get('coverage_plot_suffix')
	stripped_suffix = full_suffix[:-len(full_suffix.split('.')[-1])-1]
	cvg_figures_dictionary = {escape(sample.sample_name):sample.sample_name + '.' + stripped_suffix for sample in project.samples}

	diff_exp_genes = get_diff_exp_gene_summary(project)
	for item in diff_exp_genes:
		item[0] = escape(item[0])
		item[1] = escape(item[1])	

	context = {
		'sample_and_group_pairs':sample_and_group_pairs,
		'contrast_pairs':contrast_pairs,
		'ref_genome_name': project.parameters.get('genome'),
		'ref_genome_url': project.parameters.get('genome_source_link'),
		'cvg_plot_mappings': cvg_figures_dictionary,
		'alignment_performed' : not project.parameters.get('skip_align'),
		'analysis_performed' : not project.parameters.get('skip_analysis'),
		'diff_exp_genes' : diff_exp_genes,
		'project_id': escape(project_id),
		'bam_filter_level': project.parameters.get('bam_filter_level')
	}

	with open(output_tex, 'w') as outfile:
		outfile.write(template.render(context))
	shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)),component_params.get('bibtex_file')), component_params.get('report_output_dir'))


def get_diff_exp_gene_summary(project):
	return [line.strip().split('\t') for line in open(project.diff_exp_summary_filepath)]


def compile_report(project, component_params):
	"""
	Run the compilation for the latex .tex file that was created
	"""
	this_dir = os.path.dirname(os.path.realpath(__file__))
	project_id = os.path.basename(project.parameters.get('project_directory'))
	compile_script = os.path.join(this_dir, component_params.get('compile_script'))
	output_dir = component_params.get('report_output_dir')
	args = [compile_script, output_dir, project_id]
	p = subprocess.Popen(args, stdout = subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = p.communicate()
	logging.info('STDOUT from latex compile script: ')
	logging.info(stdout)
	logging.info('STDERR from latex compile script: ')
	logging.info(stderr)
	if p.returncode != 0:
		logging.error('Error running the compile script for the latex report.')
		raise Exception('Error running the compile script for the latex report.')


def get_bam_counts(project, component_params):
	"""
	Return a dict of dicts-- first level is the 'types' of the bamfiles.  Those each point at dicts which contain samples-to-counts info
	"""

	# get all BAM files
	wildcard_path = os.path.join(project.parameters.get('project_directory'), project.parameters.get('sample_dir_prefix') + '*', project.parameters.get('alignment_dir'), '*bam')
	all_bamfiles = glob.glob(wildcard_path)

	# go through those, make sure we have the same for each sample.  Do this by finding the 'bam types' for each sample, and put into a list of sets.  
	# then, find the intersection of all these sets-- this way the plots will be complete without missing samples (in the fringe case where samples may have missing BAM files
	# at a particular 'level'...for instance, if a deduplicated BAM files does not exist for a sample.
	sample_names = [s.sample_name for s in project.samples]
	bamfile_basenames = [ os.path.basename(x) for x in all_bamfiles ]
	bamfile_types_collection = []
	for s in sample_names:
		sample_bamfiles = [ b for b in bamfile_basenames if b.startswith(s) ]
		bamfile_types_tmp = set([ b[len(s)+1:] for b in sample_bamfiles ]) # strip off the sample name, leaving something like 'sort.primary.bam'
		bamfile_types_collection.append(bamfile_types_tmp)

	# now get the 'type set' (e.g. sorted, primary filtered, etc) for the bam files:
	bamfile_types_set = reduce(lambda x,y: x.intersection(y), bamfile_types_collection) 

	# then get the counts for each bamfile.  
	# !!! check that the bai files are there so we can use samtools idxstats.
	read_count_dict = {}
	for t in bamfile_types_set:
		read_count_dict[t] = {}
		for s in sample_names:
			bam_path = os.path.join(project.parameters.get('project_directory'), 
							project.parameters.get('sample_dir_prefix') + s, 
							project.parameters.get('alignment_dir'), 
							s + '.' + t)
			expected_index_path = bam_path + '.bai'
			if os.path.isfile(expected_index_path):
				call_args = [component_params.get('samtools'), component_params.get('samtools_call'), bam_path]
				p = subprocess.Popen( call_args, stdout = subprocess.PIPE)
				stdout, stderr = p.communicate()
				if p.returncode != 0:
					logging.error('There was an error when calling out to samtools.  The call was: %s' % ' '.join(call_args))
					logging.error('stdout: %s' % stdout)
					logging.error('stderr: %s' % stderr)
					raise Exception('Exception when calling samtools for counting reads in the bam files')
				else:
					total_reads = np.sum(np.loadtxt(StringIO.StringIO(stdout), usecols=(2,)))
					read_count_dict[t][s] = total_reads
			else:
				logging.error('Problem with finding a bam index file.  The expected BAM path was: %s' % bam_path)
				logging.error('The expected BAI file was %s ' % expected_index_path)
				raise MissingBamIndexFile('Looked for .bai file at the following path: (%s) but none was found.  Need this for counting reads.' % expected_path)
	return read_count_dict









