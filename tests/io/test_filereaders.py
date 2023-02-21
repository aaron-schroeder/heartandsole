import unittest

from numpy.testing import assert_array_equal, assert_allclose
import pandas as pd
from pandas.testing import assert_frame_equal, assert_series_equal

from heartandsole import read_gpx, read_fit, read_json, read_tcx
from tests.util import datapath


class FileReaderTestMixin:
  
  @classmethod
  def setUpClass(cls):
    cls.reader = staticmethod(cls.READER)

  def setUp(self):
    self.data = self.reader(self.TESTDATA_FILENAME)

  # TODO: Figure out what NEW tests need to be here.
  #  - If we're encapsulated, the read_* functions will be schema-agnostic
  #    so we're just getting dataframes back, and they can be passed to
  #    one of the schema-based classes (which are originally created 
  #    manually or by factory func):
  #      `hns.FitActivity(hns.read_fit('activity.fit'))`

  def test_is_dataframe(self):
    self.assertIsInstance(self.data, pd.DataFrame)


class TestGpxTrk(FileReaderTestMixin, unittest.TestCase):
  TESTDATA_FILENAME = datapath('io', 'data', 'gpx', 'trk.gpx')
  READER = read_gpx


class TestGpxRte(FileReaderTestMixin, unittest.TestCase):
  TESTDATA_FILENAME = datapath('io', 'data', 'gpx', 'rte.gpx')
  READER = read_gpx


class TestTcxActivity(FileReaderTestMixin, unittest.TestCase):
  TESTDATA_FILENAME = datapath('io', 'data', 'tcx', 'activity.tcx')
  READER = read_tcx


class TestTcxCourse(FileReaderTestMixin, unittest.TestCase):
  TESTDATA_FILENAME = datapath('io', 'data', 'tcx', 'course.tcx')
  READER = read_tcx


class TestFitActivity(FileReaderTestMixin, unittest.TestCase):
  TESTDATA_FILENAME = datapath('io', 'data', 'fit', 'activity.fit')
  READER = read_fit


class TestFitCourse(FileReaderTestMixin, unittest.TestCase):
  TESTDATA_FILENAME = datapath('io', 'data', 'fit', 'course.fit')
  READER = read_fit


class TestJsonStravaStreams(FileReaderTestMixin, unittest.TestCase):
  TESTDATA_FILENAME = datapath('io', 'data', 'json', 'strava_streams.json')
  READER = read_json


@unittest.skip('Need to create a test CSV file.')
class TestCsv(unittest.TestCase):
  # TESTDATA_FILENAME = datapath('io', 'data', 'csv', 'heartandsole.csv')
  pass


class TestCompareActivity(unittest.TestCase):
  """Need to decide what will be required by ActivityMixin
  
  (It may not end up in the package long-term)
  """

  @classmethod
  def setUpClass(cls):
    cls.fit = read_fit(TestFitActivity.TESTDATA_FILENAME)
    cls.tcx = read_tcx(TestTcxActivity.TESTDATA_FILENAME)
    cls.gpx = read_gpx(TestGpxTrk.TESTDATA_FILENAME)
