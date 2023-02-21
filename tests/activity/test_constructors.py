import datetime
import math
import unittest

import pandas as pd

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
  
  def test_create(self):
    self.assertIsNot(self.record_df, self.act.records)

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
