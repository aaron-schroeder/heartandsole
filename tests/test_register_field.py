"""Based on pandas.tests.test_register_accessor

https://github.com/pandas-dev/pandas/blob/master/pandas/tests/test_register_accessor.py

"""

import contextlib
import inspect
import unittest

import pandas as pd
import pandas._testing as tm

from heartandsole import Activity
from heartandsole.core import field


@contextlib.contextmanager
def ensure_removed(obj, attr):
  """Ensure that an attribute added to 'obj' during the test is
  removed when we're done
  """
  try:
    yield
  finally:
    try:
      delattr(obj, attr)
      delattr(obj, f'has_{attr}')
    except AttributeError:
      pass
    obj._fields.discard(attr)


class MyField:
  def __init__(self, obj):
    self.obj = obj
    self.item = 'item'

  @property
  def prop(self):
    return self.item

  def method(self):
    return self.item


class TestRegisterField(unittest.TestCase):

  def test_register(self):
    obj = Activity
    registrar = field.register_field
    # registrar = Activity.register_field
    with ensure_removed(obj, 'mine'):
      before = set(dir(obj))
      registrar('mine')(MyField)
      o = obj(pd.DataFrame.from_dict({'mine':[]}))
      self.assertEqual(o.mine.prop, 'item')
      after = set(dir(obj))
      self.assertEqual((before ^ after), {'mine'})
      # self.assertEqual((before ^ after), {'mine', 'has_mine'})
      self.assertIn('mine', obj._fields)

  def test_accessor_works(self):
    with ensure_removed(Activity, 'mine'):
      field.register_field('mine')(MyField)

      a = Activity(pd.DataFrame.from_dict({'mine': [1, 2]}))
      self.assertIs(a.mine.obj, a)

      self.assertEqual(a.mine.prop, 'item')
      self.assertEqual(a.mine.method(), 'item')

  def test_overwrite_warns(self):
    # Need to restore at the end
    records_unique = Activity.records_unique
    try:
      with tm.assert_produces_warning(UserWarning) as w:
        field.register_field('records_unique')(MyField)
        a = Activity(pd.DataFrame.from_dict({'mine': [1, 2]}))
        self.assertEqual(a.records_unique.prop, 'item')
      msg = str(w[0].message)
      self.assertIn('records_unique', msg)
      self.assertIn('MyField', msg)
      self.assertIn('Activity', msg)
    finally:
      Activity.records_unique = records_unique

  def test_raises_attribute_error(self):

    with ensure_removed(Activity, 'bad'):

      @field.register_field('bad')
      class Bad:
        def __init__(self, data):
          raise AttributeError('whoops')

      with self.assertRaises(AttributeError, msg='whoops'):
        Activity(pd.DataFrame([], dtype=object)).bad