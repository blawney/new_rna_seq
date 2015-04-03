import logging
import os
import sys

from utils.pipeline_builder import PipelineBuilder


if __name__ == "__main__":

	try:
		# get the 'home' location of this file (the pipeline's 'home' location)
		pipeline_home = os.path.dirname(os.path.realpath(__file__))
	
		# build the pipeline:
		builder = PipelineBuilder(pipeline_home)
		builder.setup()
		builder.configure()
		configured_pipeline = builder.build()
		configured_pipeline.run()

	except Exception as ex:
		logging.error("Exception thrown.  Message: %s", ex.message)
		sys.exit(1)
	


