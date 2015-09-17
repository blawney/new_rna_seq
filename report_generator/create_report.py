import logging
import jinja2
import shutil
import os
import sys
import imp

class EmptySectionException(Exception):
	pass


class InvalidDisplayException(Exception):
	pass


class Link(object):
	def __init__(self, href, text):
		self.href = href
		self.text = text


class Panel(object):
	def __init__(self, id, title, link, has_iframe = False):
		self.id = id
		self.title = title
		self.link = link
		self.has_iframe = has_iframe


class Section(object):
	def __init__(self, href, header_message, contents):
		self.href = href
		self.header_message = header_message
		if len(contents) > 0:
			self.contents = contents
			if type(contents[0]) is Panel:
				self.panel_section = True
			elif type(contents[0]) is Link:
				self.link_section = True
			else:
				raise InvalidDisplayException('Display type has not been implemented.')
		else:
			raise EmptySectionException('Attempting to populate an empty section.')


def load_remote_module(module_name, location):
	"""
	Loads and returns the module given by 'module_name' that resides in the given location
	"""
	sys.path.append(location)
	try:
		fileobj, filename, description = imp.find_module(module_name, [location])
		module = imp.load_module(module_name, fileobj, filename, description)
		return module
	except ImportError as ex:
		logging.error('Could not import module %s at location %s' % (module_name, location))
		raise ex


def add_fastq(project, transformer):
	tab_header = Link("fastq_files","FastQ Files")
	file_links = []
	for sample in project.samples:
		file_links.append(Link(transformer(sample.read_1_fastq), os.path.basename(sample.read_1_fastq)))
		if project.parameters.get('paired_alignment'):
			file_links.append(Link(transformer(sample.read_2_fastq), os.path.basename(sample.read_2_fastq)))
	section = Section("fastq_files", "Sequence files in compressed format:", file_links)
	return tab_header, section


def add_bam(project, transformer):
	tab_header = Link("bam_files","BAM Files")
	file_links = []
	for sample in project.samples:
		for bamfile in sample.bamfiles:
			file_links.append(Link(transformer(bamfile), os.path.basename(bamfile)))

	section = Section("bam_files", "Binary sequence alignment (BAM) files:", file_links)
	return tab_header, section


def add_fastQC_reports(project, transformer):
	tab_header = Link("fastQC_files","FastQC Files")
	subpanels = []
	for sample in project.samples:
		links = [sample.read_1_fastqc_report]
		if project.parameters.get('paired_alignment'):
			links.append(sample.read_2_fastqc_report)
		subpanels += [Panel(sample.sample_name + '_fastqc_' + str(i+1), sample.sample_name + ' ( read ' + str(i+1) + ' )', transformer(link), True) for i,link in enumerate(links) if link]
	if len(subpanels) > 0:
		section = Section("fastQC_files", "Sequencing quality reports:", subpanels)
		return tab_header, section
	else:
		return None, None


def add_to_context(context, tab, section):
	context['section_list'].append(tab)
	context['sections'].append(section)


def write_report(pipeline):
	"""
	Main method for writing the output report.  Called with a Pipeline object.
	"""
	try:
		# for shorter referencing
		parameters = pipeline.project.parameters

		# get the location of the utils directory:
		utils_dir = parameters.get('utils_dir')

		# load the parser and the util_methods modules:
		config_parser = load_remote_module('config_parser', utils_dir)
		util_methods = load_remote_module('util_methods', utils_dir)

		# read the config file for this report generator:
		this_directory = os.path.dirname(os.path.realpath(__file__))
		config_filepath = util_methods.locate_config(this_directory)
		report_parameters = config_parser.read_config(config_filepath, 'DEFAULT')

		# create the report directory:
		report_directory = os.path.join(parameters.get('output_location'), report_parameters.get('report_directory'))
		util_methods.create_directory(report_directory)

		# load the template
		env = jinja2.Environment(loader=jinja2.FileSystemLoader(this_directory))
		template = env.get_template(report_parameters.get('template_html_file'))

		# create the context.  This is a dictionary of key-value pairs that map to items in the template html file
		context = {'section_list' : [], 'sections' : []}

		# create a method which will transform links to relative paths
		transformer = lambda x: os.path.relpath(x, report_directory)

		if not parameters.get('skip_align'):
			logging.info('Adding fastq files to output report.')
			add_to_context(context, *add_fastq(pipeline.project, transformer))
			
		logging.info('Adding BAM files to output report.')
		add_to_context(context, *add_bam(pipeline.project, transformer))
		logging.info('Adding fastQC files to output report.')
		add_to_context(context, *add_fastQC_reports(pipeline.project, transformer))

		for component in pipeline.components:
			for i, output in enumerate(component.outputs):
				if output:
					logging.info('Adding files from Component: %s to output report.' % component.name)
					section_href = component.name + "_" + str(i)
					tab_header = Link(section_href, output.nav_text)
					if output.display_format == 'list':
						contents = [Link(transformer(href), text) for text,href in output.files.items()]
					elif output.display_format == 'collapse_panel_iframe':
						contents = [Panel( section_href + '_' + str(i) , t[0], transformer(t[1]), True) for i,t in enumerate(output.files.items())]
					elif output.display_format == 'collapse_panel':
						contents = [Panel( section_href + '_' + str(i) , t[0], transformer(t[1]), False) for i,t in enumerate(output.files.items())]
					else:
						raise InvalidDisplayException('An invalid display type was specified.')
					section = Section(section_href, output.header_msg, contents)
					add_to_context(context, tab_header, section)

		logging.info('Rendering report.')
		completed_report_path = os.path.join(report_directory, report_parameters.get('completed_html_report'))
		with open(completed_report_path, 'w') as outfile:
			outfile.write(template.render(context))

		# move the lib files (javascript, css, etc)
		destination = os.path.join(report_directory, report_parameters.get('libraries_directory'))
		src = os.path.join(this_directory, report_parameters.get('libraries_directory'))
		shutil.copytree(src, destination)

	except Exception as ex:
		raise ex



