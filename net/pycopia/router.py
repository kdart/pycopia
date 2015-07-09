#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Interface to the Linux network emulator and rate limiting features.

"""

# python 3 compatibility
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

import operator
import functools
import re

from pycopia import aid
from pycopia import proctools
from pycopia.physics.physical_quantities import PhysicalQuantity as PQ


class Error(Exception):
    pass


class RouterConfigError(Error):
    """Raised if a configuration command was not able to run.

    Carries a tuple of integer exit status and stderr text.
    """
    pass

class RouterConstructorError(Error):
    """Raised if you try to do something that's not possible."""
    pass


# possible delay distribution values.
DIST_UNIFORM = "uniform"
DIST_NORMAL = "normal"
DIST_PARETO = "pareto"
DIST_PARETONORMAL = "paretonormal"

# Direction values
Up, Down, Level, Unknown = aid.Enums("up", "down", "level", "unknown")


class ImpairmentsConfigurer(object):
    """Simplified interface to configuring network interfaces and path impairments.

    Parameters
    ----------
    interfaces : list of str
        A list of the data interface names used in the path configuration.
    """

    def __init__(self, interfaces):
        self.interfaces = interfaces

    def _perform(self, cmd):
        pm = proctools.get_procmanager()
        proc = pm.spawnpipe(cmd)
        out = proc.read()
        es = proc.wait()
        if es:
            return out
        else:
            raise RouterConfigError(int(es), out)


    def clear(self, interface):
        r"""clear the interface configuration.

        Ensures there are no delay or loss configurations on the interface.

        Parameters
        ----------
        interface : str
            The name of the interface to operate on. e.g. "eth1".

        Raises
        ------
        RouterConfigError
            If there was a problem running the command.

        See Also
        --------
        show, delay, reorder, corrupt, loss

        Examples
        --------
        >>> router.clear("eth1")
        """
        cmd = "tc qdisc del dev {0} root".format(interface)
        try:
            self._perform(cmd)
        except RouterConfigError as rerr:
            if rerr.args[0] == 2: # Indicates it was already clear, which is ok.
                return
            else:
                raise

    def show(self, interface):
        r"""Get the current interface configuration.

        Return information about the current configuration of the interface.

        Parameters
        ----------
        interface : str
            The name of the interface to inspect. e.g. "eth1".

        Returns
        -------
        imp : Impairment
            An instance of the Impairment object.

        Raises
        ------
        RouterConfigError
            If there was a problem running the command.

        See Also
        --------
        clear, delay, reorder, corrupt, duplicate, loss

        Examples
        --------
        >>> info = router.show("eth1")
        >>> print(info)
        """
        res = self._perform("tc qdisc ls dev {0}".format(interface))
        return parse_report(res)

    def delay(self, interface, milliseconds, jitter=None, correlation=None, distribution=None):
        r"""Set delay impairment on an interface.


        Parameters
        ----------
        interface : str
            The name of the interface to add the impairment to, e.g. "eth1".
        milliseconds : int
            The number of milliseconds to delay.
        jitter : int, optional
            The jitter (variation) of the delay value.
        correlation : float (percent), optional
            This causes the next random delay to be this percentage near the last one.
        distribution : str {"normal", "pareto", "paretonormal"}, optional
            The type of statistical distribution of the delay.

        Returns
        -------
        output : str
            the output of the tc command.

        Raises
        ------
        RouterConfigError
            If there was a problem running the command.

        See Also
        --------
        clear, reorder, corrupt, duplicate, loss

        Notes
        -----
        The correlation and distribution parameters are mutually exclusive. Supply only one.

        Examples
        --------
        >>> delay("eth1", 1000)
        """
        self.clear(interface)
        cmd = "tc qdisc add dev {0} root netem delay {1}ms {2} {3} {4}".format(
                    interface,
                    milliseconds,
                    "{0}ms".format(jitter) if jitter else "",
                    "{0:2.1f}%".format(correlation) if correlation else "",
                    "distribution {0}".format(distribution) if distribution else "",
                    )
        return self._perform(cmd)

    def reorder(self, interface, percent, delay=10, correlation=0):
        self.clear(interface)
        cmd = "tc qdisc add dev {0} root netem delay {1:3.0d}ms reorder {2} {3}".format(
                    interface,
                    delay,
                    "{0:2.1f}%".format(float(percent)),
                    "{0:2.1f}%".format(correlation) if correlation else "",
                    )
        return self._perform(cmd)

    def corrupt(self, interface, percent):
        self.clear(interface)
        cmd = "tc qdisc add dev {0} root netem corrupt {1:2.1f}%".format(interface, percent)
        return self._perform(cmd)

    def duplication(self, interface, percent):
        self.clear(interface)
        cmd = "tc qdisc add dev {0} root netem duplicate {1:2.1f}%".format(interface, percent)
        return self._perform(cmd)

    def loss(self, interface, percent, correlation=None):
        self.clear(interface)
        cmd = "tc qdisc add dev {0} root netem loss {1:2.1f}% {2}".format(
                interface,
                percent,
                "{0:2.1f}%".format(correlation) if correlation else "",
                )
        return self._perform(cmd)

    def add_corrupt(self, interface, percent):
        cmd = "tc qdisc change dev {0} root netem corrupt {1:2.1f}%".format(interface, percent)
        return self._perform(cmd)

    def add_duplication(self, interface, percent):
        cmd = "tc qdisc change dev {0} root netem duplicate {1:2.1f}%".format(interface, percent)
        return self._perform(cmd)

    def add_reorder(self, interface, delay=10, percent=10, correlation=None):
        cmd = "tc qdisc change dev {0} root netem delay {1:3.0d}ms reorder {2} {3}".format(
                interface,
                delay,
                "{0:2.1f}%".format(float(percent)),
                "{0:2.1f}%".format(correlation) if correlation else "",
                )
        return self._perform(cmd)

    def add_loss(self, interface, percent, correlation=None):
        cmd = "tc qdisc change dev {0} root netem loss {1:2.1f}% {2}".format(
                interface,
                percent,
                "{0:2.1f}%".format(correlation) if correlation else "",
                )
        return self._perform(cmd)

    def reset(self):
        r"""Reset the router impairments to normal operation.

        Raises
        ------
        RouterConfigError
            If there was a problem running the clear command.

        See Also
        --------
        clear

        Examples
        --------
        >>> routercontroller.reset()
        """
        for intf in self.interfaces:
            self.clear(intf)

    def current(self):
        impairments = map(self.show, self.interfaces)
        if impairments:
            return functools.reduce(operator.add, impairments)
        else:
            return None

    def down(self):
        r"""Down all data interfaces.

        Raises
        ------
        RouterConfigError
            If there was a problem running the ip command.

        See Also
        --------
        up

        Examples
        --------
        >>> routercontroller.down()
        """
        for intf in self.interfaces:
            self._perform("ip link set {} down".format(intf))

    def up(self):
        r"""Bring up all data interfaces.

        Raises
        ------
        RouterConfigError
            If there was a problem running the ip command.

        See Also
        --------
        down

        Examples
        --------
        >>> routercontroller.up()
        """
        for intf in self.interfaces:
            self._perform("ip link set {} up".format(intf))

    @staticmethod
    def get_impairment(latency=None, delay=None, jitter=None,
            loss=None,
            drop=None,
            corrupt=None,
            reorder=None,
            duplicate=None, correlation=None):
        """Simplified constructor function for impairment objects. It can't do
        everything, but makes the common case easier to get.  """
        imp = Impairment()
        # latency and delay are actually synonyms/aliases for the same thing.
        if latency is not None:
            imp.add_delay(latency, jitter=jitter, correlation=correlation)
        if delay is not None:
            imp.add_delay(latency, jitter=jitter, correlation=correlation)
        # loss and drop are synonyms/aliases
        if loss is not None:
            imp.add_drop(loss, correlation=correlation)
        if drop is not None:
            imp.add_drop(drop, correlation=correlation)
        if corrupt is not None:
            imp.add_corrupt(corrupt, correlation=correlation)
        if duplicate is not None:
            imp.add_duplicate(duplicate, correlation=correlation)
        if reorder is not None:
            imp.add_reorder(reorder, correlation=correlation)
        return imp

    def set_impairment(self, latency=None, delay=None, jitter=None,
            loss=None,
            drop=None,
            corrupt=None,
            reorder=None,
            duplicate=None, correlation=None):
        imp = self.get_impairment(latency, delay, jitter,
                loss, drop, corrupt, reorder, duplicate, correlation)
        imp.applyto(self)
        return imp


class Percent(float):
    _symbol = "%"

    def __new__(cls, val):
        if isinstance(val, basestring):
            val = val.replace("%", "")
        return float.__new__(cls, val)

    def __str__(self):
        return "{}{}".format(float.__str__(self), self._symbol)

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, float.__repr__(self))

    def __truediv__(self, other):
        return self.__class__(float.__truediv__(self, float(other)))

    def __div__(self, other):
        return self.__class__(float.__div__(self, float(other)))

    def __add__(self, other):
        return self.__class__(float.__add__(self, float(other)))

    def __sub__(self, other):
        return self.__class__(float.__sub__(self, float(other)))

    def __mul__(self, other):
        return self.__class__(float.__mul__(self, float(other)))


@functools.total_ordering
class Option(object):
    """Base class for netem options."""
    _basetype = None
    _possible_values = ()
    _attributes = ()

    def __init__(self, value, **options):
        if isinstance(value, self.__class__):
            self.__dict__.update(value.__dict__)
        else:
            v = self._basetype(value)
            if self._possible_values and v not in self._possible_values:
                raise ValueError("{!r} is not one of {!r}".format(v, self._possible_values))
            self._value = v
            for name, basetype, default in self.__class__._attributes:
                value = options.pop(name, default)
                if value is not None:
                    setattr(self, name, basetype(value))
            self.setup(options)
            if options:
                raise ValueError("Option got extra options: {!r}".format(options.keys()))

    def setup(self, options):
        pass # override in subclass to setup extra options, if any.

    def copy(self):
        d= {}
        for name, basetype, default in self.__class__._attributes:
            d[name] = getattr(self, name, default)
        return self.__class__(self._value, **d)

    def __repr__(self):
        attrs = self.__class__._attributes
        return "{0}({1!r}{2}{3})".format(
                self.__class__.__name__, self._value, ", " if attrs else "", ", ".join(
                        "%s=%r" % (name, getattr(self, name, default)) for (name, bt, default) in attrs))

    def __str__(self):
        return "{} {}".format(self.__class__.__name__.lower(), self._get_option_string())

    def _get_option_string(self):
        s = [str(self._value)]
        for name, basetype, default in self.__class__._attributes:
            value = getattr(self, name, None)
            if value is not None and value != default:
                s.append(str(value))
        return " ".join(s)

    def __float__(self):
        return float(self._value)

    def _check_obj(self, other):
        if not isinstance(other, self.__class__):
            return self.__class__(other)
        return other

    def __lt__(self, other):
        other = self._check_obj(other)
        return self._value < other._value

    def __eq__(self, other):
        other = self._check_obj(other)
        return self._value == other._value

    def __ne__(self, other):
        other = self._check_obj(other)
        return self._value != other._value

    @property
    def value(self):
        return self._value

class Distribution(Option):
    _basetype = str
    _possible_values = (DIST_UNIFORM, DIST_NORMAL, DIST_PARETO, DIST_PARETONORMAL)


class NumericOption(Option):
    _maximum = 0.0

    def setup(self, options):
        cls = self.__class__
        self._maximum = cls._basetype(options.pop("maximum", cls._maximum))

    def __mul__(self, other):
        return self.__class__(self._value * other, maximum=self._maximum)

    def __truediv__(self, other):
        return self.__class__(self._value / other, maximum=self._maximum)

    __div__ = __truediv__

    def __add__(self, other):
        other = self._check_obj(other)
        return self.__class__(self._value + other._value, maximum=self._maximum)

    def __sub__(self, other):
        other = self._check_obj(other)
        return self.__class__(self._value - other._value, maximum=self._maximum)

    def over_maximum(self):
        return self._value > self._maximum

    def _get_maximum(self):
        return self._maximum

    def _set_maximum(self, maxval):
        self._maximum = self._basetype(maxval)

    def _del_maximum(self):
        self._maximum = self.__class__._maximum # reset to default

    maximum = property(_get_maximum, _set_maximum, _del_maximum,
            "Maximum value of option.")


class Delay(NumericOption):
    _basetype = PQ
    _maximum = PQ("3000ms")
    _attributes = (
            ("jitter", PQ, PQ(0.0, "us")),
            ("correlation", Percent, Percent(0.0)),
    )

    def __float__(self):
        return float(self._value.inUnitsOf("ms"))


class Limit(NumericOption):
    _basetype = int
    _maximum = 5000

class Drop(NumericOption):
    _basetype = Percent
    _maximum = Percent(100.0)
    _attributes = (
            ("correlation", Percent, Percent(0.0)),
    )

class Corrupt(NumericOption):
    _basetype = Percent
    _maximum = Percent(100.0)
    _attributes = (
            ("correlation", Percent, Percent(0.0)),
    )

class Duplicate(NumericOption):
    _basetype = Percent
    _maximum = Percent(100.0)
    _attributes = (
            ("correlation", Percent, Percent(0.0)),
    )

class Reorder(NumericOption):
    _basetype = Percent
    _maximum = Percent(100.0)
    _attributes = (
            ("correlation", Percent, Percent(0.0)),
    )

class Gap(NumericOption):
    _basetype = int
    _maximum = 10



class Impairment(object):
    # name of maximum values and default values
    _max_values = {
        "maxlatency": PQ("3000ms"),
        "maxdrop": Percent(90.0),
        "maxcorruption": Percent(90.0),
        "maxduplicate": Percent(90.0),
        "maxreorder": Percent(90.0),
        "maxgap": Gap,
    }

    def __init__(self, *args, **kwargs):
        self._parent = None
        self._children = []
        self._nodeid = "root"
        self._impairments = list(args)
        for maxname, default in Impairment._max_values.items():
            value = kwargs.pop(maxname, default)
            setattr(self, maxname, value)
        if kwargs:
            raise ValueError("Impairment got extra keyword arguments: {!r}".format(kwargs))

    def add_delay(self, value, **kwargs):
        return self._impairments.append(Delay(value, **kwargs))

    def add_distribution(self, value):
        return self._impairments.append(Distribution(value))

    def add_drop(self, value, **kwargs):
        return self._impairments.append(Drop(value, **kwargs))

    def add_corrupt(self, value, **kwargs):
        return self._impairments.append(Corrupt(value, **kwargs))

    def add_duplicate(self, value, **kwargs):
        return self._impairments.append(Duplicate(value, **kwargs))

    def add_reorder(self, value, **kwargs):
        return self._impairments.append(Reorder(value, **kwargs))

    def add_gap(self, value):
        return self._impairments.append(Gap(value))

    def add_limit(self, value):
        return self._impairments.append(Limit(value))

    def over_maximum(self):
        primary = self._impairments[0]
        return primary.over_maximum()

    def __str__(self):
        s = [self._nodeid if isinstance(self._nodeid, basestring) else  "{:04x}".format(self._nodeid)]
        s.append("netem")
        s.extend(str(imp) for imp in self._impairments)
        return " ".join(s)

    def copy(self):
        return self.__class__(**self.__dict__)

    def clear(self):
        self._impairments = []

    def __repr__(self):
        return "{0}({1})".format(
                self.__class__.__name__, ", ".join(repr(o) for o in self._impairments))

    def __iter__(self):
        return iter(self._impairments)

    def __getitem__(self, idx):
        return self._impairments[idx]

    def __nonzero__(self):
        return len(self._impairments)
    __bool__ = __nonzero__

    def __add__(self, other):
        return self._perform_op(other, operator.add)

    def __sub__(self, other):
        return self._perform_op(other, operator.sub)

    def __truediv__(self, other):
        return self._perform_op(other, operator.truediv)
    __div__ = __truediv__

    def __mul__(self, other):
        return self._perform_op(other, operator.mul)

    def _perform_op(self, other, op):
        new = []
        if not self._impairments:
            return self.__class__()
        imp = self._impairments[0]
        if isinstance(imp, NumericOption):
            new.append(op(imp, other[0]))
        else:
            new.append(imp.copy())
        for imp in self._impairments[1:]:
            new.append(imp.copy())
        return self.__class__(*new)

    def applyto(self, router):
        """Apply impairments from this object using given router instance.

        The impairments values are spread over all of the router interfaces
        to make it symetrical. Typically, this will be two interfaces.
        """
        # e.g.: tc qdisc add dev {0} root netem delay {1}ms {2} {3} {4}
        if self._parent is not None:
            raise RouterConstructorError("May only apply to root impairment.")
        oldimp = router.current()
        router.reset()
        if not self._impairments:
            return
        n = len(router.interfaces)
        parms = self.netem_command(n)
        if self._nodeid == "root":
            change = "add"
        else:
            change = "change"
        for intf in router.interfaces:
            cmd = "tc qdisc {} dev {} {} {}".format(change, intf, self._nodeid, parms)
            router._perform(cmd)
        # TODO apply child impairments
        return oldimp

    def netem_command(self, n=1):
        s = ["netem"]
        for imp in self._impairments:
            if isinstance(imp, NumericOption):
                s.append(str(imp / n))
            else:
                s.append(str(imp))
        return " ".join(s)

    def get_direction(self, oldvalue):
        if not oldvalue:
            return Unknown
        assert type(oldvalue) is type(self)
        oldvalue = oldvalue._impairments[0]
        value = self._impairments[0]
        if oldvalue > value:
            return Down
        elif oldvalue < value:
            return Up
        else:
            return Level

    # tree management
    @property
    def parent(self):
        return self._parent

    def _check_obj(self, other):
        if not isinstance(other, self.__class__):
            raise ValueError("Must operate on same Impairment type.")

    def replace(self, imp):
        self._check_obj(imp)
        if self._parent:
            p = self._parent
            i = self._parent.index(self)
            del self._parent[i]
            self._parent = None
            p.insert(i, newtree)
        return self

    def detach(self):
        if self._parent:
            try:
                i = self._parent.index(self)
                del self._parent[i]
            except ValueError:
                pass
        self._parent = None
        return self

    def destroy(self):
        if self._parent:
            i = self._parent.index(self)
            del self._parent[i]
        self._parent = None
        for n in self._children:
            n._parent = None
        self._children = None

    def get_children(self):
        return self._children[:]

    def _find_index(self, index):
        if type(index) is str:
            for i, ch in enumerate(self._children):
                if ch.matchpath(index):
                    return i
            raise IndexError("no impairments match")
        else:
            return index

    _path_re = re.compile(r'(\w+)\[(.*)]')

    def matchpath(self, pathelement):
        if "[" not in pathelement:
            return pathelement == self._name
        else:
            mo = Impairment._path_re.match(pathelement)
            if mo:
                name, match = mo.groups()
                if name != self._name:
                    return False
                mp = match.split("=")
                attr = getattr(self, mp[0], None)
                if attr is None:
                    return False
                if len(mp) > 1:
                    return mp[1][1:-1] == attr
                else:
                    return True
            else:
                raise ValueError("Path element {!r} not found.".format(pathelement))


def parse_report(bigstring):
    imps = []
    for line in bigstring.splitlines():
        if line.startswith("qdisc"):
            if "netem" in line:
                if "delay" in line:
                    delay = PQ(0.0, "ms")
                    jitter = PQ(0.0, "ms")
                    correlation = 0.0
                    mo = re.search(r"delay ([0-9.]+\s*\D+)\s+([0-9.]+\s*\D+)\s+([0-9.]+)%", line)
                    if mo:
                        delay = PQ(mo.group(1))
                        jitter = PQ(mo.group(2))
                        correlation = Percent(mo.group(3))
                    else:
                        mo = re.search(r"delay ([0-9.]+\s*\D+)\s+([0-9.]+\s*\D+)", line)
                        if mo:
                            delay = PQ(mo.group(1))
                            jitter = PQ(mo.group(2))
                        else:
                            mo = re.search(r"delay ([0-9.]+\s*\D+)", line)
                            if mo:
                                delay = PQ(mo.group(1))
                    imps.append(Delay(delay, jitter=jitter, correlation=correlation))
                if "distribution" in line:
                    mo = re.search(r"distribution (\w+)", line)
                    dist = mo.group(1)
                    imps.append(Distribution(dist))
                if "loss" in line:
                    correlation = 0.0
                    mo = re.search(r"loss\s+([0-9.]+)%\s+([0-9.]+)%", line)
                    if mo:
                        pstr = mo.group(1)
                        correlation = mo.group(2)
                    else:
                        mo = re.search(r"loss\s+([0-9.]+)%", line)
                        if mo:
                            pstr = mo.group(1)
                    imps.append(Drop(pstr, correlation=correlation))
                if "corrupt" in line:
                    correlation = 0.0
                    mo = re.search(r"corrupt\s+([0-9.]+)%\s+([0-9.]+)%", line)
                    if mo:
                        pstr = mo.group(1)
                        correlation = mo.group(2)
                    else:
                        mo = re.search(r"corrupt\s+([0-9.]+)%", line)
                        if mo:
                            pstr = mo.group(1)
                    imps.append(Corrupt(pstr, correlation=correlation))
                if "duplicate" in line:
                    correlation = 0.0
                    mo = re.search(r"duplicate\s+([0-9.]+)%\s+([0-9.]+)%", line)
                    if mo:
                        pstr = mo.group(1)
                        correlation = mo.group(2)
                    else:
                        mo = re.search(r"duplicate\s+([0-9.]+)%", line)
                        if mo:
                            pstr = mo.group(1)
                    imps.append(Duplicate(pstr, correlation=correlation))
                if "reorder" in line:
                    correlation = 0.0
                    mo = re.search(r"reorder\s+([0-9.]+)%\s+([0-9.]+)%", line)
                    if mo:
                        pstr = mo.group(1)
                        correlation = mo.group(2)
                    else:
                        mo = re.search(r"reorder\s+([0-9.]+)%", line)
                        if mo:
                            pstr = mo.group(1)
                    imps.append(Reorder(pstr, correlation=correlation))
                if "gap" in line:
                    mo = re.search(r"gap\s+([0-9]+)", line)
                    pstr = mo.group(1)
                    imps.append(Gap(pstr))
    return Impairment(*imps)


