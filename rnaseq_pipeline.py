import utils.cmd_line_parser as cl_parser
import utils.os_utils as os_utils
import datetime
import logging
import os
import sys

from utils.pipeline import Pipeline


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
	
		# parse the commandline args
		cl_args = cl_parser.read()

		# create the output directory (if possible) from the commandline args
		output_dir = cl_args['output_location']
		os_utils.create_directory(output_dir)

		# instantiate a logfile in the output directory
		create_logger(output_dir)

		# create the pipeline object:
		pipeline = Pipeline(pipeline_home, cl_args)

	except Exception as ex:
		logging.error("Exception thrown.  Message: %s", ex.message)
		sys.exit(1)


