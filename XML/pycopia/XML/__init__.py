"""
XML
===

XML related modules.
"""


class XMLError(Exception):
    pass

class ValidationError(XMLError):
    """ValidationError
    This exception is raised when an attempt is made to construct an XML POM
    tree that would be invalid.
    """
    pass


class XMLVisitorContinue(Exception):
    """Signal walk method to bybass children."""
    pass


class XMLPathError(XMLError):
    """Raised when a path method is called and it cannot find the
    referenced path.
    """
