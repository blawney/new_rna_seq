def write_report(pipeline):
	"""
	Main method for writing the output report.  Called with a Pipeline object.
	"""
	try:
		this_directory = os.path.dirname(os.path.realpath(__file__))
		parse_config_file(pipeline.project, this_directory)

		# edit the config variables to get the full paths
		pipeline.project.parameters.prepend_param('template_html_file', this_directory, os.path.join)
		pipeline.project.parameters.prepend_param('completed_html_report', pipeline.project.parameters.get('output_location'), os.path.join)
		pipeline.project.parameters.prepend_param('template_elements_dir', this_directory, os.path.join)

		# for shorter referencing
		parameters = pipeling.project.parameters
