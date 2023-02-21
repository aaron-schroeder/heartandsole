import unittest

# import numpy.testing as tm
import pandas._testing as tm

import heartandsole as hns


class ApiTest(unittest.TestCase):

  # these are optionally imported based on testing
  # & need to be ignored
  ignored = ["tests", "locale", "conftest"]

  # top-level sub-packages
  public_lib = [
      # 'api',
      # "arrays",
      # "options",
      # "test",
      # "testing",
      # "errors",
      # "plotting",
      # 'io',
      # "tseries",
  ]
  private_lib = [
    'api',
    'compat',
    'core',
    'heartandsole',
    'io',
    'util',
  ]

  # top-level classes
  classes = [
    'Activity'
  ]

  # these are already deprecated; awaiting removal
  deprecated_classes = []

  # external modules exposed in heartandsole namespace
  modules = []

  # top-level functions
  funcs = []

  # top-level read_* funcs
  funcs_read = [
    # 'read_xml',
  ]

  # top-level to_* funcs
  # "to_datetime", "to_numeric", "to_pickle", "to_timedelta"
  funcs_to = []

  # top-level to deprecate in the future
  deprecated_funcs_in_future = []

  # these are already deprecated; awaiting removal
  deprecated_funcs = []

  # private modules in heartandsole namespace
  private_modules = [
    # "_config",
    # "_libs",
    # "_is_numpy_dev",
    # "_testing",
    # "_typing",
    # "_version",
  ]

  def check(self, namespace, expected, ignored=None):
    result = sorted(
      f for f in dir(namespace) if not f.startswith('__') # and f !='annotations'
    )
    if ignored is not None:
      result = sorted(set(result) - set(ignored))
    expected = sorted(expected)
    self.assertCountEqual(result, expected)

  def test_api(self):
    checkthese = (
      self.public_lib
      + self.private_lib
      # + self.misc
      + self.modules
      + self.classes
      + self.funcs
      # + self.funcs_option
      + self.funcs_read
      # + self.funcs_json
      + self.funcs_to
      + self.private_modules
    )
    self.check(namespace=hns, expected=checkthese, ignored=self.ignored)

  def test_api_all(self):
    expected = set(
      self.public_lib
      # + self.misc
      + self.modules
      + self.classes
      + self.funcs
      # + self.funcs_option
      + self.funcs_read
      # + self.funcs_json
      + self.funcs_to
    ) - set(self.deprecated_classes)
    actual = set(hns.__all__)

    self.assertCountEqual(expected, actual)

  def test_depr(self):
    deprecated_list = (
      self.deprecated_classes
      + self.deprecated_funcs
      + self.deprecated_funcs_in_future
    )
    for depr in deprecated_list:
      with self.assertWarns(FutureWarning):
        _ = getattr(hns, depr)