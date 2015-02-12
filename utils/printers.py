def __print_dict__(d):
	"""
	Simple method for returning a dictionary as a string.  Capable of handling any dict, but will not print
	arbitrarily nested dictionaries- only the first 'layer'
	"""
	s = "\n"
	for key, value in d.iteritems():
		s+= str(key)+" : "+str(value)+"\n"
	return s


def pretty_print(obj):
	if type(obj) == dict:
		s = __print_dict__(obj)
	else:
		s = str(obj)
	return s
