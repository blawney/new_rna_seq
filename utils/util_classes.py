from printers import pretty_print
import sys
import logging
from custom_exceptions import ParameterNotFoundException, ParameterOverwriteException

class Params(object):
	def __init__(self):
		self.__param_dict__ = {}

	def __str__(self):
		return pretty_print(self.__param_dict__)


	def get_param_dict(self):
		return self.__param_dict__

	def get(self, name):
		"""
		Returns the value, given the key.
		Will raise a KeyError if the key 'name' is not found in the dictionary
		"""
		try:
			return self.__param_dict__[name]
		except KeyError:
			logging.error("Could not locate parameter: '%s' in parameter dictionary.  ", name)
			raise ParameterNotFoundException("Tried to retrieve a parameter that was not set.  See log.")

	def reset_param(self, name, new_value):

		if name in self.__param_dict__:
			self.__param_dict__[name] = new_value
		else:
			logging.error("Could not locate parameter: '%s' in parameter dictionary.  ", name)
			raise ParameterNotFoundException("Tried to reset a parameter that was not already set.  See log.")


	def add(self, *args, **kwargs):
		"""
		Adds key-value pairs to the dictionary of parameters
		"""
		for arg in args:
			self.__add_dict__(arg)
		
		self.__add_dict__(kwargs)



	def __add_dict__(self, d):
		"""
		private method that unpacks a dictionary and adds it to the param_dict dictionary
		Silently errors if the passed argument d is not a dictionary
		"""
		try:
			for k,v in d.iteritems():
				if not k in self.__param_dict__:
					self.__param_dict__[k]=v
				else:
					raise ParameterOverwriteException('Attempted to add/overwrite a parameter that was already set: %s' % k)
		except AttributeError:
			pass
