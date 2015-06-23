
class ConfigFileNotFoundException(Exception):
	pass

class MultipleFileFoundException(Exception):
	pass

class MissingConfigFileSectionException(Exception):
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

class AnnotationFileParseException(Exception):
	pass

class ProjectStructureException(Exception):
	pass

class ContrastSpecificationException(Exception):
	pass

class InconsistentPairingStatusException(Exception):
	pass
