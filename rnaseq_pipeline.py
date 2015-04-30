import logging
import os
import sys
import cmd_line_parser as cl_parser


from utils.pipeline_builder import PipelineBuilder


def create_logger(log_dir):
	"""
	Create a logfile in the log_dir directory
	"""
	timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
	logfile = os.path.join(log_dir, str(timestamp)+".rnaseq.log")
	logging.basicConfig(filename=logfile, level=logging.INFO, format="%(asctime)s:%(levelname)s:%(message)s")


if __name__ == "__main__":

	try:
		# get the 'home' location of this file (the pipeline's 'home' location)
		pipeline_home = os.path.dirname(os.path.realpath(__file__))
	
		# Parse the commandline args:
		cmd_line_params = cl_parser.read()

		if cmd_line_params.get('restart', None):
			#TODO: unpickle the cl-arg
			configured_pipeline = None
		else:
			# build the pipeline:
			builder = PipelineBuilder(pipeline_home)
			builder.setup(cmd_line_params)
			create_logger(builder.builder_params.get('output_location'))
			builder.configure()
			configured_pipeline = builder.build()
		configured_pipeline.run()

	except Exception as ex:
		logging.error("Exception thrown.  Message: %s", ex.message)
		sys.exit(1)
	


