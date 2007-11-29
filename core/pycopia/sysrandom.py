#!/usr/bin/python2.4
# vim:ts=2:sw=2:softtabstop=2:smarttab:expandtab

"""Same as Python's stock random module, except use the system random
source by default.
"""

from random import SystemRandom

_inst = SystemRandom()

# integer functions
getrandbits = _inst.getrandbits
randint = _inst.randint
randrange = _inst.randrange
# sequence functions
choice = _inst.choice
sample = _inst.sample
shuffle = _inst.shuffle
# generator functions
random = _inst.random
uniform = _inst.uniform
normalvariate = _inst.normalvariate
lognormvariate = _inst.lognormvariate
expovariate = _inst.expovariate
vonmisesvariate = _inst.vonmisesvariate
gammavariate = _inst.gammavariate
gauss = _inst.gauss
betavariate = _inst.betavariate
paretovariate = _inst.paretovariate
weibullvariate = _inst.weibullvariate
