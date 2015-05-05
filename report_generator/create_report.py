import jinja2
import os

class EmptySectionException(Exception):
	pass


class InvalidDisplayException(Exception):
	pass


class Link(object):
	def __init__(self, href, text):
		self.href = href
		self.text = text


class Panel(object):
	def __init__(self, id, link, has_iframe = False):
		self.id = id
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


def add_fastq(project, transformer):
	tab_header = Link("fastq_files","FastQ Files")
	file_links = []
	for sample in project.samples:
		file_links.append(Link(transformer.get_relpath(sample.read_1_fastq), os.path.basename(sample.read_1_fastq)))
		if project.parameters.get('paired_alignment'):
			file_links.append(Link(transformer.get_relpath(sample.read_2_fastq), os.path.basename(sample.read_2_fastq)))
	section = Section("fastq_files", "Sequence files in compressed format:", file_links)
	return tab_header, section


def add_bam(project, transformer):
	tab_header = Link("bam_files","BAM Files")
	file_links = []
	for sample in project.samples:
		for bamfile in sample.bamfiles:
			file_links.append(Link(transformer.get_relpath(bamfile), os.path.basename(bamfile)))

	section = Section("bam_files", "Binary sequence alignment (BAM) files:", file_links)
	return tab_header, section


def add_fastQC_reports(project, transformer):
	tab_header = Link("fastQC_files","FastQC Files")
	subpanels = []
	for sample in project.samples:
		links = [sample.read_1_fastqc_report]
		if project.parameters.get('paired_alignment'):
			links.append(sample.read_2_fastqc_report)
		subpanels += [Panel(os.path.basename(link), transformer.get_relpath(link), True) for link in links]
		
	section = Section("fastQC_files", "Sequencing quality reports:", subpanels)
	return tab_header, section


def add_to_context(context, tab, section):
	context['section_list'].append(tab)
	context['sections'].append(section)


def write_report(pipeline):
	"""
	Main method for writing the output report.  Called with a Pipeline object.
	"""
	try:
		this_directory = os.path.dirname(os.path.realpath(__file__))
		parse_config_file(pipeline.project, this_directory)

		# for shorter referencing
		parameters = pipeling.project.parameters

		# edit the config variables to get the full paths
		parameters.prepend_param('completed_html_report', parameters.get('output_location'), os.path.join)

		# load the template
		env = jinja2.Environment(loader=jinja2.FileSystemLoader(this_directory))
		template = env.get_template(parameters.get('template_html_file'))

		# create the context.  This is a dictionary of key-value pairs that map to items in the template html file
		context = {'section_list' : [], 'sections' : []}

		# create a method which will transform links to relative paths
		transformer = lambda x: os.path.relpath(x, parameters.get('output_location'))

		if not parameters.get('skip_align'):
			add_to_context(add_fastq(pipeline.project, transformer))
			
		add_to_context(add_bam(pipeline.project, transformer))
		add_to_context(add_fastQC_reports(pipeline.project, transformer))
	
		for component in pipeline.components:
			for i, output in enumerate(component.outputs):
				href = component.name + "_" + str(i)
				tab_header = Link(href, output.nav_text)
				if output.display_format == 'list':
					contents = [Link(transformer.get_relpath(href), text) for text,href in output.files.items()]
				elif output.display_format == 'collapse_panel_iframe':
					contents = [Panel(text, transformer.get_relpath(href), True) for text,href in output.files.items()]
				elif output.display_format == 'collapse_panel':
					contents = [Panel(text, transformer.get_relpath(href), False) for text,href in output.files.items()]
				else:
					raise InvalidDisplayException('An invalid display type was specified.')
				section = Section(href, output.header_msg, contents)
				add_to_context(tab_header, section)

		completed_report_path = os.path.join( parameters('output_location'), parameters('completed_html_report'))
		with open(completed_report_path, 'w') as outfile:
			outfile.write(template.render(context))

	except Exception as ex:
		raise ex
