"""Based somewhat on pandas accessor testing.

https://github.com/pandas-dev/pandas/blob/master/pandas/tests/strings/test_strings.py
https://github.com/pandas-dev/pandas/blob/master/pandas/tests/strings/test_api.py
https://github.com/pandas-dev/pandas/blob/master/pandas/tests/series/accessors/test_str_accessor.py
https://github.com/pandas-dev/pandas/blob/master/pandas/tests/series/accessors/test_cat_accessor.py

"""
import datetime
import unittest

import dateutil
import pandas as pd
import pandas.testing as tm

import heartandsole
from heartandsole import Activity
from heartandsole.core.field import CachedField
from heartandsole.core.fields.base import ActivityField


def safe_import(mod_name):
  """
  Args:
    mod_name (str): Name of the module to be imported
  Returns:
    The imported module if successful, or False
  """
  try:
    return __import__(mod_name)
  except ImportError:
    return False


def skip_if_installed(package):
  """Skip a test if a package is installed.
  
  Args:
    package (str): The name of the package.
  """
  return unittest.skipIf(
      safe_import(package), reason=f'Skipping because {package} is installed.'
  )


class MyField(ActivityField):
  _field_name = 'mine'


class TestActivityField(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    # Same way that fields are added to Activity in activity.py.
    heartandsole.Activity._fields.add('mine')
    heartandsole.Activity.mine = CachedField('mine', MyField)
    
  @classmethod
  def tearDownClass(cls):
    delattr(heartandsole.Activity, 'mine')
    heartandsole.Activity._fields.remove('mine')

  def test_exists(self):
    self.assertIn('mine', heartandsole.Activity._fields)
    self.assertIn('mine', dir(heartandsole.Activity))
    self.assertIs(heartandsole.Activity.mine, MyField)
    
    activity = heartandsole.Activity(
      pd.DataFrame.from_dict({
        'mine': [0.0, 1.0, 2.0, 3.0, 4.0],
      })
    )
    self.assertIsInstance(activity.mine, MyField)

  def test_has(self):
    activity = heartandsole.Activity(
      pd.DataFrame.from_dict({
        'mine': [0.0, 1.0, 2.0, 3.0, 4.0],
      })
    )
    self.assertTrue(activity.has_streams('mine'))
    self.assertFalse(activity.has_streams('not_mine'))

  def test_stream(self):
    activity = heartandsole.Activity(
      pd.DataFrame.from_dict({
        'mine': [0.0, 1.0, 2.0, 3.0, 4.0],
      })
    )
    data = activity.mine.stream
    # data = activity.mine.stream('records')
    self.assertIs(data, activity.records['mine'])

    activity_not_mine = heartandsole.Activity(
      pd.DataFrame.from_dict({
        'not_mine': [0.0, 1.0, 2.0, 3.0, 4.0],
      })
    )
    self.assertIsNone(activity_not_mine.mine.stream)

  def test_laps(self):
    activity = heartandsole.Activity(
      pd.DataFrame([]),
      laps=pd.DataFrame.from_dict({
        'mine_a': ['a', 'a'],
        'mine_1': [1, 1],
        'other_b': ['b', 'b'],
        'c_mine': ['c', 'c']
      })
    )

    result = activity.mine.laps
    expected = pd.DataFrame.from_dict({
      'a': ['a', 'a'],
      '1': [1, 1],
      'c': ['c', 'c'],
    })
    tm.assert_frame_equal(result, expected)

    result = activity.mine.lap_cols
    expected = pd.Index(['mine_a', 'mine_1', 'c_mine'])
    tm.assert_index_equal(result, expected)

  def test_summary(self):
    activity = heartandsole.Activity(
      pd.DataFrame([]),
      summary=pd.Series({
        'mine_a': 'a',
        'mine_1': 1,
        'other_b': 'b',
        'c_mine': 'c',
      })
    )
    result = activity.mine.summary
    expected = pd.Series({'a': 'a', '1': 1, 'c': 'c'})
    tm.assert_series_equal(result, expected)

    result = activity.mine.summary_rows
    expected = pd.Index(['mine_a', 'mine_1', 'c_mine'])
    tm.assert_index_equal(result, expected)

class TestDistance(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    cls.activity = heartandsole.Activity(
      pd.DataFrame.from_dict({
        'distance': [0.0, 25.0, 50.0, 75.0, 100.0],
        'lat': [40.0, 40.1, 40.2, 40.3, 40.4],
        'lon': [-105.0, -105.0, -105.0, -105.0, -105.0]
      }),
      summary=pd.Series({'distance': 100.0}),
      laps=pd.DataFrame.from_dict({'distance': [50.0, 50.0]}),
    )

  def test_total(self):
    activity = heartandsole.Activity(
      pd.DataFrame.from_dict({
        'distance': [0.0, 25.0, 50.0, 75.0, 100.0],
        'lat': [40 + 0.00001 * i for i in range(5)],
        'lon': [-105.0, -105.0, -105.0, -105.0, -105.0]
      }),
      summary=pd.Series({'distance_total': 101.0}),
      laps=pd.DataFrame.from_dict({'distance_total': [50.0, 52.0]}),
    )
    for src, expected in zip(
      ('records', 'summary', 'laps', 'position'),
      (100.0, 101.0, 102.0, 4 * 0.00001 * 111200)
    ):
      result = activity.distance.total(src)
      self.assertIsInstance(result, float)
      self.assertAlmostEqual(result, expected, places=3)
      # print(self.activity.distance.total(src))

    activity_blank = heartandsole.Activity(pd.DataFrame([]))
    for src in ['records', 'summary', 'laps']:
      # Might wanna raise a warning here, or something.
      self.assertIsNone(activity_blank.distance.total(src))

  def test_records_from_position(self):
    distances = self.activity.distance.records_from_position()
    self.assertIsInstance(distances, pd.Series)
    self.assertTrue(pd.api.types.is_float_dtype(distances))

  @skip_if_installed('pandas_xyz')
  def test_raises(self):
    with self.assertRaisesRegex(ImportError, 'pandas_xyz'):
      self.activity.distance.total('position')


class TestElevation(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    cls.activity = heartandsole.Activity(pd.DataFrame.from_dict({
      'elevation': [0.0, 1.0, 2.0, 1.0, 3.0],
    }))

  @unittest.skip('Not implemented this round')
  def test_convert_units(self):
    # Convert units from native to default.
    self.activity.elevation._convert_record_units(orig='feet')

  @skip_if_installed('pandas_xyz')
  def test_raises(self):
    with self.assertRaisesRegex(ImportError, 'pandas_xyz'):
      self.activity.elevation.gain('records')

  def test_gain(self):
    activity = heartandsole.Activity(
      pd.DataFrame.from_dict({'elevation': [0.0, 1.0, 0.0, 6.0]}),
      summary=pd.Series({'elevation_gain': 100.0}),
      laps=pd.DataFrame.from_dict({'elevation_gain': [50.0, 75.0]}),
    )

    for src, expected in zip(
      ('records', 'summary', 'laps'),
      (6.0, 100.0, 125.0)
    ):
      result = activity.elevation.gain(src)
      self.assertIsInstance(result, float)
      self.assertEqual(result, expected)

    activity_blank = heartandsole.Activity(pd.DataFrame([]))
    for src in ['records', 'summary', 'laps']:
      # Might wanna raise a warning here, or something.
      self.assertIsNone(activity_blank.elevation.gain(src))

  def test_loss(self):
    activity = heartandsole.Activity(
      pd.DataFrame.from_dict({'elevation': [6.0, 0.0, 1.0, 0.0]}),
      summary=pd.Series({'elevation_loss': 100.0}),
      laps=pd.DataFrame.from_dict({'elevation_loss': [50.0, 75.0]}),
    )

    for src, expected in zip(
      ('records', 'summary', 'laps'),
      (6.0, 100.0, 125.0)
    ):
      result = activity.elevation.loss(src)
      self.assertIsInstance(result, float)
      self.assertEqual(result, expected)

    activity_blank = heartandsole.Activity(pd.DataFrame([]))
    for src in ['records', 'summary', 'laps']:
      # Might wanna raise a warning here, or something.
      self.assertIsNone(activity_blank.elevation.loss(src))


class TestPosition(unittest.TestCase):

  def test_convert_units(self):
    # Semicircle units
    activity = heartandsole.Activity(pd.DataFrame.from_dict({
      'lat': [40.0 * 2 ** 31 / 180],
      'lon': [-105.0 * 2 ** 31 / 180]
    }))

    activity.lat._convert_record_units(inplace=True)
    activity.lon._convert_record_units(inplace=True)

    self.assertEqual(activity.records['lat'].iloc[0], 40.0)
    self.assertEqual(activity.records['lon'].iloc[0], -105.0)

  def test_center(self):
    activity = heartandsole.Activity(pd.DataFrame.from_dict({
      'lat': [40.0, 40.1, 40.1, 45.0]
    }))
    self.assertEqual(activity.lat.center, 42.5)


class TestTime(unittest.TestCase):

  def test_time_from_timestamp(self):
    t0 = datetime.datetime.now()
    activity = heartandsole.Activity(
      pd.DataFrame.from_dict({
        'timestamp': [t0 + datetime.timedelta(seconds=s) for s in (0, 50, 75, 100)],
      })
    )

    result = activity.time.records_from_timestamps()
    expected = pd.Series([0, 50, 75, 100], name='time')
    tm.assert_series_equal(result, expected)

  def test_elapsed(self):
    t0 = datetime.datetime.now()
    activity = heartandsole.Activity(
      pd.DataFrame.from_dict({
        'timestamp': [t0 + datetime.timedelta(seconds=s) for s in (0, 50, 75, 100)],
        'time': [0, 100, 200, 400],
      }),
      summary=pd.Series({
        'time_elapsed': 300.0,
        'timestamp_start': t0,
        'timestamp_end': t0 + datetime.timedelta(seconds=101)
      }),
      laps=pd.DataFrame.from_dict({
        'time_elapsed': [200.0, 150.0],
        'timestamp_start': [t0, t0 + datetime.timedelta(seconds=49)],
        'timestamp_end': [t0 + datetime.timedelta(seconds=49), t0 + datetime.timedelta(seconds=99)],
      }),
    )

    self.assertEqual(
      activity.timestamp.elapsed('records'), # pd.Timedelta
      datetime.timedelta(seconds=100)
    )
    self.assertEqual(
      activity.timestamp.elapsed('summary'), # dt.timedelta
      datetime.timedelta(seconds=101)
    )
    self.assertEqual(
      activity.timestamp.elapsed('laps'), # pd.Timedelta
      datetime.timedelta(seconds=99)
    )
    self.assertEqual(
      activity.time.elapsed('records'),
      400
    )
    self.assertEqual(
      activity.time.elapsed('summary'),
      300
    )
    self.assertEqual(
      activity.time.elapsed('laps'),
      350
    )
    
    activity_blank = Activity(pd.DataFrame([]))
    for src in ['records', 'summary', 'laps']:
      self.assertIsNone(activity_blank.time.elapsed(src))
      self.assertIsNone(activity_blank.timestamp.elapsed(src))

  def test_timer(self):
    activity = heartandsole.Activity(
      pd.DataFrame([]),
      summary=pd.Series({
        'time_timer': 300.0,
      }),
      laps=pd.DataFrame.from_dict({
        'time_timer': [200.0, 150.0],
      }),
    )

    self.assertEqual(
      activity.time.timer('summary'),
      300
    )
    self.assertEqual(
      activity.time.timer('laps'),
      350
    )

    activity_blank = Activity(pd.DataFrame([]))
    for src in ['summary', 'laps']:
      self.assertIsNone(activity_blank.time.timer(src))

  def test_tz(self):
    for tz_local in [
      dateutil.tz.gettz(name='UTC'),
      dateutil.tz.gettz(name='America/Denver'),
      # dateutil.tz.gettz(name='AEST-10AEDT-11,M10.1.0/2,M4.1.0/3'), # error
      'UTC',
      'America/Denver'
    ]:

      t0 = datetime.datetime.now()
      activity = heartandsole.Activity(
        pd.DataFrame.from_dict({
          'timestamp': [t0 + datetime.timedelta(seconds=s) for s in (0, 50, 75, 100)],
        }),
        summary=pd.Series({
          'timestamp_start': t0,
          'timestamp_end': t0 + datetime.timedelta(seconds=101)
        }),
        laps=pd.DataFrame.from_dict({
          'timestamp_start': [
            t0, 
            t0 + datetime.timedelta(seconds=49)
          ],
          'timestamp_end': [
            t0 + datetime.timedelta(seconds=49),
            t0 + datetime.timedelta(seconds=99)
          ],
        }),
      )

      activity.timestamp.ensure_aware(tz_local)

      for series in [
        activity.records['timestamp'],
        activity.laps['timestamp_start'],
        activity.laps['timestamp_end']
      ]:
        self.assertTrue(pd.api.types.is_datetime64tz_dtype(series))
      
      for row in [
        activity.summary['timestamp_start'],
        activity.summary['timestamp_end'],
      ]:
        self.assertIsNotNone(row.tz)

      # print(activity.timestamp.start('records').tz)
      # print(activity.timestamp.start('summary').astimezone('America/Denver'))
      # print(activity.timestamp.start('laps').astimezone('America/Denver'))