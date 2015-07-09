
"""
Dummy module for firewalls so that other modules that use the
platform-independent firewall modules won't fail on import.

"""

#import sudo
#import socketlib


def port_forward(srcport, destport, rule=None):
    """Use firewall rule to forward a TCP port to a different port. Useful for
    redirecting privileged ports to non-privileged ports.  """
    return NotImplemented

def add(rule, action):
    return NotImplemented

def delete(rule):
    return NotImplemented

def flush():
    return NotImplemented

class Firewall(object):
    def read(self):
        return NotImplemented


if __name__ == "__main__":
    pass

