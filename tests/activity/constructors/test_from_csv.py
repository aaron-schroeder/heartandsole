import os
import unittest

from heartandsole import Activity


@unittest.skip('Need to create a test CSV file.')
class TestCsv(unittest.TestCase):

  TESTDATA_FILENAME = os.path.join(os.path.dirname(__file__), 'testdata.csv')

  @classmethod
  def setUpClass(cls):
    cls.act = Activity.from_csv(cls.TESTDATA_FILENAME)

  def test_1(self):
    pass