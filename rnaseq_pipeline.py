import logging
import os
import sys
import cmd_line_parser as cl_parser
import pickle


from utils.pipeline_builder import PipelineBuilder
from utils.pipeline import Pipeline # allows unpickling the pipeline object

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

		# set the Pipeline object to None by default-- we will only pickle a configured pipeline if analyses have been completed.  
		# If the pipeline raises an exception prior to starting actual analyses, it is quick to make the necessary fix and restart
		# without involving any pickling.  
		configured_pipeline = None

		# if restarting from a pickle object
		if cmd_line_params.get('restart', None):
			configured_pipeline = pickle.load(open( cmd_line_params.get('restart'), 'rb'))
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
		if configured_pipeline:
			output_pickle_path = os.path.join(configured_pipeline.project.parameters.get('output_location'), 'restart.pickle')
			pickle.dump(configured_pipeline, open(output_pickle_path,'wb'))
			logging.info("Created a restart pickle at %s " % output_pickle_path)
		sys.exit(1)
	


