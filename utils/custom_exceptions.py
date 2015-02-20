
class ConfigFileNotFoundException(Exception):
	pass

class MultipleConfigFileFoundException(Exception):
	pass

class CannotMakeOutputDirectoryException(Exception):
	pass

class ParameterNotFoundException(Exception):
	pass

class MissingComponentDirectoryException(Exception):
	pass

class MissingFileException(Exception):
	pass

class IncorrectGenomeException(Exception):
	pass

class IncorrectAlignerException(Exception):
	pass

class MalformattedComponentException(Exception):
	pass

class MissingAlignerConfigFileException(Exception):
	pass

class ParameterOverwriteException(Exception):
	pass
