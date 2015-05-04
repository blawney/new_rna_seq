import jinja2

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
		parameters.prepend_param('completed_html_report', pipeline.project.parameters.get('output_location'), os.path.join)

		# load the template
		env = jinja2.Environment(loader=jinja2.FileSystemLoader(this_directory))
		template = env.get_template(parameters.get('template_html_file'))

		# create the context.  This is a dictionary of key-value pairs that map to items in the template html file
		context = {}

		# TODO: add the fastq, bam, fastqc
	
		# TODO: add components by using pipeline.components
	except Exception as ex:
		raise ex
