
"""
iSCSI package exceptions.

"""



class Error(Exception):
    pass

class ValidationError(Error):
    """Raised on invalid paramters, such as badly formed names."""


