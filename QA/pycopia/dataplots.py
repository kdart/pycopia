#!/usr/bin/python2.7 -i
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
#    Copyright (C) 2009 Keith Dart <keith@dartworks.biz>
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.

"""
Operate on and plot time-series data.

"""

import itertools

import pylab
from matplotlib.font_manager import FontProperties

from pycopia import dataset

PLOT_COLORS = [
    (0.0, 0.8, 0.0, 1.),
    (0.5, 0.0, 0.9, 1.),
    (0.0, 0.0, 1.0, 1.),
    (0.9, 0.0, 0.5, 1.),
    (1.0, 0.0, 0.0, 1.),
]

color_cycler = itertools.cycle(PLOT_COLORS)


def make_plots(dset, timemarks="0s,9d", ylim=None, columns=None,
            autoscale=False, events=None, interactive=False):
    pylab.ioff()
    names = []
    if type(events) is dataset.DataSet:
        events.normalize_time(dset.measurements[0][0])
    dset.normalize_time()
    unit = dset.unit

    for subset, start, end in dset.get_timeslices(timemarks):
        if len(subset) > 0:
            datacols, labels = subset.get_columns(columns)
            x_time = datacols[0]
            if len(x_time) < 100:
                mrk = "."
                ls = "-"
            else:
                mrk = ","
                ls = "None"
            for col, label, color in itertools.izip(datacols[1:], labels[1:], color_cycler):
                pylab.plot(x_time, col, color=color, label=label, ls=ls, marker=mrk)
            pylab.setp(pylab.gcf(), dpi=100, size_inches=(9,6))
            pylab.xlabel("Time (s)")
            pylab.ylabel(unit)

            if events is not None:
                ax = pylab.gca()
                for row in events:
                    ax.axvline(row[0], color="rgbymc"[int(row[1]) % 6])

            metadata = subset.metadata
            title = "%s-%s-%s-%ss-%ss" % (metadata.name,
                    metadata.timestamp.strftime("%m%d%H%M%S"),
                    "-".join(labels),
                    int(start),
                    int(end))
            pylab.title(title, fontsize="x-small")
            font = FontProperties(size="x-small")
            pylab.legend(prop=font)

            if not interactive:
                fname = "%s.%s" % (title, "png")
                pylab.savefig(fname, format="png")
                names.append(fname)
                pylab.cla()
        else:
            break
    return names


# Functions for interactive reporting from command line.

def do_plots(filename, timemarks=None, columns=None, ylim=None, autoscale=False, eventsfile=None):
    """Make a series of graphs from the the data in file split on the time
    marks.
    """
    data = dataset.DataSet(filename=filename)
    if timemarks:
        data.timeslice(timemarks)
    if eventsfile is not None:
        events = dataset.DataSet(filename=eventsfile)
    else:
        events = None
    names = make_plots(data, columns=columns, ylim=ylim, events=events, autoscale=autoscale)
    for name in names:
        print "PNG file saved to:", name


def Plot(filename=None, data=None, timemarks=None,
    events=None, eventfile=None,
    ylim=None, columns=(0, 1),
    autoscale=True):
    """Plot from ipython.

      Args:
        filename (string): name of a data file to plot. This will be loaded
        into a DataSet object.

        data (DataSet): pre-existing dataset to plot. Mutually exclusive
        with filename parameter.

        timemarks (string): a time spec indicating a span of time to slice.

        eventfile (string): name of data file containing event marks.

        events (DataSet): A pre-existing event dataset.

        ylim (tuple of (min, max): minimum and maximum Y values to plot.

        columns (int, or sequence of ints): The column number, or numbers,
        starting from zero that will be extracted out (vertical slice).

        autoscale (bool): If True, automatically fit graph scale to data.
        False means use a fixed scale (2.5 amp max).

    """
    if filename is not None:
        data = dataset.DataSet(filename=filename)
    if eventfile is not None:
        events = dataset.DataSet(filename=eventfile)
    if data is None:
        print "You should supply a filename or a dataset."
        return
    if timemarks:
            data.timeslice(timemarks)

    make_plots(data, ylim=ylim, events=events,
            columns=columns, autoscale=autoscale, interactive=True)
    pylab.gcf().set_size_inches((9,7))
    #plotaxes = pylab.gca()
    pylab.subplots_adjust(bottom=0.15)
    pylab.ion()
    pylab.show()



if __name__ == "__main__":
    from pylab import *
