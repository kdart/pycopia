# Dictionary containing numbers
#
# These objects are meant to be used like arrays with generalized
# indices. Non-existent elements default to zero. Global operations
# are addition, subtraction, and multiplication/division by a scalar.
#
# Written by Konrad Hinsen <hinsen@cnrs-orleans.fr>
# last revision: 1999-7-23
#
# Modified by Keith Dart to work with new physical_quantities module, and
# modern Python.

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division


from pycopia import dictlib


class NumberDict(dictlib.AttrDictDefault):

  """Dictionary storing numerical values

  Constructor: NumberDict()

  An instance of this class acts like an array of number with
  generalized (non-integer) indices. A value of zero is assumed
  for undefined entries. NumberDict instances support addition,
  and subtraction with other NumberDict instances, and multiplication
  and division by scalars.
  """

  def __coerce__(self, other):
    if isinstance(other, dict):
      return self, self.__class__(other, self._default)

  def __add__(self, other):
    sum = self.copy()
    for key in other:
      sum[key] = sum[key] + other[key]
    return sum

  __radd__ = __add__

  def __sub__(self, other):
    sum = self.copy()
    for key in other:
      sum[key] = sum[key] - other[key]
    return sum

  def __rsub__(self, other):
    sum = self.copy()
    for key in other:
      sum[key] = other[key] - self[key]
    return sum

  def __mul__(self, other):
    new = self.__class__(default=self._default)
    for key in self:
      new[key] = other * self[key]
    return new

  __rmul__ = __mul__

  def __truediv__(self, other):
    new = self.__class__(default=self._default)
    for key in self:
      new[key] = self[key] / other
    return new

  __div__ = __floordiv__ = __truediv__

