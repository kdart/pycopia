# NMS Web applications.
"""
A web application that provides network management functions.

This also serves as an example of how to use the Pycopia components.
"""

import os
import gettext

#gettext.bindtextdomain('nmsapps', os.path.join(__path__[0], "translations"))
gettext.bindtextdomain('nmsapps', "/usr/share/locale")
gettext.textdomain('nmsapps')
_ = gettext.gettext



