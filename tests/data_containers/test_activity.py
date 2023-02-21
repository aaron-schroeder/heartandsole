import datetime
import math

import numpy as np
from numpy.testing import assert_array_equal, assert_allclose
import pandas as pd
import pandas.testing as tm

import unittest

from heartandsole import Activity

 
class TestActivity(unittest.TestCase):
  # TODO: Separate into TestCases for input data handling,
  #       output data types, and output with missing fields.

  @classmethod
  def setUpClass(cls):
    # Create a DataFrame that is formatted correctly for consumption
    # by Activity. This DataFrame has all available fields.
    nT = 60
    v = 3.0
    data = dict(
      timestamp=[datetime.datetime(2019, 9, 1, second=i) for i in range(nT)],
      time=[i for i in range(nT)],
      distance=[i * 3.0 for i in range(nT)],
      displacement=[3.0 for i in range(nT)],
      speed=[3.0 for i in range(nT)],
      elevation=[1.0 * i for i in range(nT)],
      lat=[40.0 + 0.0001*i for i in range(nT)],
      lon=[-105.4 - 0.0001*i for i in range(nT)],
      heartrate=[140.0 + 5.0 * math.sin(i * math.pi/10) for i in range(nT)],
      cadence=[170.0 + 5.0 * math.cos(i * math.pi/10) for i in range(nT)],
      moving=[bool(i > nT / 2) for i in range(nT)],
      grade=[0.2 * i / nT for i in range(nT)]
      #running_smoothness=[170.0 + 5.0 * math.cos(i * math.pi/10) for i in range(nT)],
      #stance_time=[250.0 + 25.0 * math.cos(i * math.pi/10) for i in range(nT)],
      #vertical_oscillation=[12.5 + 2.0 * math.cos(i * math.pi/10) for i in range(nT)],
    )

    cls.record_df = pd.DataFrame(data)
    cls.act = Activity(cls.record_df)

  def test_convenience_methods(self):
    for fld in ['timestamp', 'distance', 'speed', 'elevation', 'lat', 
      'lon', 'heartrate', 'cadence']:
      # self.assertIn(f'has_{fld}', dir(self.act))
      # self.assertTrue(getattr(self.act, f'has_{fld}'))
      self.assertTrue(self.act.has_streams(fld))

    self.assertTrue(self.act.has_position)

  def test_unique_records(self):
    act = Activity(pd.DataFrame.from_dict(dict(
      distance=[i % 50 for i in range(100)]
    )))
    self.assertEqual(len(act.records), 100)
    self.assertEqual(len(act.records_unique), 50)

  def test_create(self):
    #Verify a new DataFrame instance is attached to the Activity, 
    # not the same one that was passed in.
    pass

  def test_validate(self):
    # Verify that Activity checks the type of each object passed in.
    for record_obj in [
      pd.Series(dict(a=1, b=2)), 
      dict(a=1, b=2), 
      [1, 2, 3]
    ]:
      with self.assertRaises(TypeError):
        a = Activity(record_obj)


  def test_index_format(self):
    # TODO: re-implement this logic; I think it is good.
    
    # df = self.record_df.copy()

    # # Verify the DataFrame index may be an IntegerIndex as well.
    # df.index = pd.Int64Index(range(len(df.index)))
    # try:
    #   act = Activity(df)
    # except:
    #   self.fail('Activity creation with appropriate DF index raised'  \
    #             ' exception unexpectedly!')

    # # Verify an exception is raised when a MultiIndex is used.
    # df.index = pd.MultiIndex.from_arrays(
    #     [
    #         [0 for i in range(len(df.index))],
    #         [i for i in range(len(df.index))]
    #     ],
    #     names=('block', 'record')
    # )
    # self.assertRaisesRegex(TypeError,
    #     'DataFrame index should be some form of pd.Int64Index, not *',
    #     Activity, df)

    pass


if __name__ == '__main__':
  unittest.main()
