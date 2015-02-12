import os
from custom_exceptions import CannotMakeOutputDirectoryException

def create_directory(path):
	"""
	Creates a directory.  If it cannot (due to write permissions, etc).  Issues a message and kills the pipeline
	"""
	# to avoid overwriting data in an existing directory, only work in a new directory 
	if os.path.isdir(path):
		raise CannotMakeOutputDirectoryException("The path ("+ path +") is an existing directory. To avoid overwriting data, please supply a path to a new directory")
	elif os.access(os.path.dirname(path), os.W_OK):
		os.makedirs(path, 0774)
	else:
		raise CannotMakeOutputDirectoryException("Could not create the output directory at: (" + str(path) + "). Check write-permissions, etc.")
		
