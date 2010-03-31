#!/usr/bin/python2.6
# -*- coding: us-ascii -*-
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab


"""
Module for managing time-series data.

"""

import os
import re
import itertools

import numpy

from pycopia import timespec
from pycopia import timelib
from pycopia import datafile
from pycopia.physics import physical_quantities

# abbreviation
PQ = physical_quantities.PhysicalQuantity


# break up column name and measurement unit.
HEADER_RE = re.compile(r'(\w+)\W*\((\w+)\)')


class DataSet(object):
    """Holds measurement data, label, and unit information.

    Also provides some common methods to operate on the data.

    This may be instantiated from several sources. Use filename parameter if
    source is a data (.dat) file, use dataset parameter if source is another
    dataset object, use array and headers if source is an array object and
    associated headers with labels an units. 
    """
    def __init__(self, filename=None, dataset=None, array=None, headers=None):
        self.metadata = datafile.DataFileData()
        if filename is not None:
            self.fromfile(filename)
        elif dataset is not None:
            self.fromDataSet(dataset)
        elif array is not None and headers is not None:
            self.fromarray(array, headers)
        else:
            self.measurements = None
            self.labels = None
            self.units = None
            self.timeseries = False
            self._mean = None

    def fromfile(self, filename):
        headers, measurements = read_array(filename)
        self.fromarray(measurements, headers)
        self.metadata.update(datafile.decode_filename(filename))

    def fromarray(self, measurements, headers):
        self.measurements = measurements
        self.set_headers(headers)
        self._mean = None

    def fromDataSet(self, dataset):
        self.measurements = dataset.measurements.copy()
        self.labels = dataset.labels[:]
        self.units = dataset.units[:]
        self.metadata = dataset.metadata.copy()
        self._mean = None

    def set_as_timeseries(self):
        self.starttime = self.measurements[0][0]
        self.endtime = self.measurements[-1][0]
        self.samplestart = self.measurements[0][0]
        self.metadata.set_timestamp(self.samplestart)
        self.timeseries = True

    def get_unit(self):
        if self.units:
            if self.timeseries:
                return self.units[1]
            else:
                return self.units[0]
        else:
            return None

    def get_headers(self):
        rv = []
        for label, unit in itertools.izip(self.labels, self.units):
            rv.append("%s (%s)" % (label, unit))
        return rv

    def set_headers(self, headers):
        # headers have labels and units
        labels = []
        units = []
        for h in headers:
            match = HEADER_RE.search(h)
            if match:
                labels.append(match.group(1))
                units.append(match.group(2))
            else:
                raise ValueError("Not a properly formated data header (need: 'name (unit)').")
        self.labels = labels
        self.units = units
        if self.units and self.units[0].endswith("s"):
            self.set_as_timeseries()

    def __len__(self):
        return len(self.measurements)

    def __getitem__(self, idx):
        return self.measurements[idx]

    def __iter__(self):
        return iter(self.measurements)

    def get_stats(self, column=None):
        """Common statistics for a column.

        Returns:
            mean, maximum, minimum, median, crestfactor
            of the measurement data.
        """
        if self._mean is None:
            if column is None:
                if self.timeseries:
                    column = 1
                else:
                    column = 0
            self.transpose()
            unit = self.units[column]
            col1 = self.measurements[column]
            self._mean = PQ(numpy.mean(col1), unit)
            self._maximum = PQ(numpy.amax(col1), unit)
            self._minimum = PQ(numpy.amin(col1), unit)
            self._median    = PQ(numpy.median(col1), unit)
            self._crestfactor    = float(self._maximum / self._mean)
            self.transpose()
        return (self._mean, self._maximum, self._minimum, self._median, self._crestfactor)

    def append(self, *values):
        self.measurements = numpy.append(self.measurements, numpy.array(values), axis=0)

    def __str__(self):
        mean, maxi, mini, median, cf = self.get_stats()
        s = ["DataSet:\n"]
        if self.timeseries:
            offset = timespec.getHMSString(self.starttime - self.samplestart)
            span = timespec.getHMSString(self.endtime - self.starttime)
            s.append("Data offset %s after start time and spans %s." % (offset, span))
        s.append(str(self.metadata))
        s.append("")
        s.append("Out of %s samples:" % (len(self.measurements), ))
        s.append(" Maximum: %s" % maxi)
        s.append(" Minimum: %s" % mini)
        s.append("    Mean: %s" % mean)
        s.append("  Median: %s" % median)
        s.append("      CF: %s" % cf)
        return "\n".join(s)

    def write_file(self, name):
        directory, name = os.path.split(name)
        self.metadata["name"], ext = ps.path.splitext(name)
        fname = datafile.get_filename(self.metadata, directory)
        with open(fname, "w") as fo:
            self.write_fileobject(fo)
        return fname

    def write_fileobject(self, fo):
        for heading in self.get_headers():
            fo.write(repr(heading))
            fo.write("\t")
        fo.write("\n")
        for row in self.measurements:
            fo.write("\t".join([repr(a) for a in row]))
            fo.write("\n")

    def transpose(self):
        self.measurements = self.measurements.transpose()

    def get_columns(self, columns):
        """Returns a tuple of a list of selected columns, and a list of column
        names (without unit).

        Args:
            columns (int, or sequence of ints): The column number, or numbers,
            starting from zero that will be extracted out (vertical slice).

        Returns:
            Tuple of:
                list of arrays of select data columns.
                list of labels as strings. These positionally match the data columns.
        """
        datacolumns = self.measurements.transpose()
        datacols = []
        labels = []
        if type(columns) in (tuple, list):
            for n in columns:
                datacols.append(datacolumns[n])
                labels.append(self.labels[n])
        else:
            n = int(columns)
            datacols.append(datacolumns[n])
            labels.append(self.labels[n])
        return datacols, labels

    def timeslice(self, timespec):
        timemarks = timespec.TimeMarksGenerator(timespec)
        self.measurements = timeslice_array(self.measurements,
                timemarks.next(),
                timemarks.next())

    def normalize_time(self, start=None, offset=None):
        self.measurements = normalize_time(self.measurements, start, offset)

    def get_timeslice(self, timespan):
        if type(timespan) is str:
            timemarks = timespec.TimeMarksGenerator(timespan)
            return timeslice_array(self.measurements, 
                    timemarks.next(),
                    timemarks.next())
        elif type(timespan) in (list, tuple):
            return timeslice_array(self.measurements, timespan[0], timespan[1])
        else:
            raise ValueError("Need timespec string or 2-tuple of (start, end) time.")

    def get_timeslices(self, timespan):
        """Iterator generator to iterate over sections of time.

        Args:
            timespan (string): a time span specification, such as "0s,5m,..." to
            get 5 minute chunks at a time.

        Yields a new DataSet, starttime (s float), endtime (s float)
        """
        timemarks = iter(timespec.TimeMarksGenerator(timespan))
        start = timemarks.next()
        for end in timemarks:
            subset = timeslice_array(self.measurements, start, end)
            ds = DataSet()
            ds.measurements = subset
            ds.units = self.units
            ds.labels = self.labels
            ds.metadata = self.metadata
            yield ds, start, end
            start = end

    # properties
    unit = property(get_unit)
    headers = property(get_headers, set_headers)
    mean = property(lambda self: self.get_stats()[0])
    maximum = property(lambda self: self.get_stats()[1])
    minimum = property(lambda self: self.get_stats()[2])
    median = property(lambda self: self.get_stats()[3])
    crestfactor = property(lambda self: self.get_stats()[4])


def _ReadCSV(fileobj):
    for line in fileobj:
        for el in line.split(","):
            yield float(el)


def read_array(filename):
    """Reads an array from a file.

    The first line must be a header with labels and units in a particular
    format. 
    """
    unused_, filetype = os.path.splitext(filename)
    fo = open(filename, "rU")
    try:
        if filetype == ".txt":
            header = map(eval, fo.readline().split("\t"))
            a = numpy.fromfile(fo, dtype="f8", sep="\n\t")
        elif filetype == ".csv":
            header = map(str.strip, fo.readline().split(","))
            a = numpy.fromiter(_ReadCSV(fo), numpy.float64)
        elif filetype == ".dat": # gnuplot style data
            line1 = fo.readline()[2:].split("\t")
            try:
                header = map(eval, line1)
            except (ValueError, SyntaxError): # assume no header line
                header = line1
                fo.seek(0)
            a = numpy.fromfile(fo, dtype="f8", sep="\n")
        else:
            raise ValueError(
                "read_array: Invalid file type. need .txt, .csv, or .dat (got %r)." % 
                filetype)
    finally:
        fo.close()
    # Data may have SCPI NAN or INF values in it. Convert to numpy
    # equivalents.
    a = numpy.fromiter(itertools.imap(check_value, a), numpy.float64)
    a.shape = (-1, len(header))
    return header, a


def check_value(number):
    """Check for NaN and INF special values.

    Substitute numpy equivalents. These values are the special IEEE-488
    values that signal special numbers.
    """
    if number == 9.91E+37:
        return numpy.nan
    elif number == 9.9E+37:
        return numpy.inf
    elif number == -9.9E+37:
        return -numpy.inf
    else:
        return number


def normalize_time(measurements, start=None, offset=None):
    """Normalize a data array containing timestamps as the first data column
    to start at zero time.

    Args:
        measurements (array) a numpy array containing a measurement set.
        start (float) an optional absolute time stamp to take as start time.
        offset (float) an optional relative time to offset the result.
    """
    if start is None:
        start = measurements[0][0]
    measurements = measurements.transpose()
    # Subtract the first timestamp value from all timestamp values.
    measurements[0] = measurements[0] - start
    if offset is not None:
        measurements[0] = measurements[0] + offset
    return measurements.transpose()


def timeslice_array(measurements, start, end):
  """Return slice of array from start to end time, in seconds. 

  Time is relative to beginning of array.

  Args:
    measurements: multi-dimensional array with time stamps in first column. Array
    should be organized in rows.
    start and end are floats, in seconds. 
  """
  times = measurements.transpose()[0]
  beginning = times[0]
  starti = times.searchsorted(beginning + start)
  endi = times.searchsorted(beginning + end)
  return measurements[starti:endi]



def _test(argv):
    from pycopia import autodebug
    data = numpy.array([
        [0.0, 1.0, 1.1],
        [1.0, 1.2, 1.2],
        [2.0, 1.4, 1.3],
        [3.0, 2.4, 1.8],
        ])
    headers = ['time(s)', 'bias (V)', 'nodeI (I)']
    ds = DataSet(array=data, headers=headers)
    print ds

if __name__ == "__main__":
    import sys
    _test(sys.argv)
