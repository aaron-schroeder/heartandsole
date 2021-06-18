"""Based on:
https://github.com/pandas-dev/pandas/blob/master/pandas/tests/test_optional_dependency.py

"""

import sys
import types

import unittest
from unittest import mock

from heartandsole.compat._optional import (
  VERSIONS,
  import_optional_dependency,
)


class TestOptionalDependency(unittest.TestCase):
  def test_import_optional(self):
    match = 'Missing .*notapackage.* pip .* notapackage'
    with self.assertRaisesRegex(ImportError, match):
      import_optional_dependency('notapackage')

    result = import_optional_dependency('notapackage', errors='ignore')
    self.assertIsNone(result)

  def test_bad_version(self):
    name = 'fakemodule'
    module = types.ModuleType(name)
    module.__version__ = '0.9.0'
    sys.modules[name] = module

    with mock.patch.dict(VERSIONS, {name: '1.0.0'}):

      match = 'Heartandsole requires .*1.0.0.* of .fakemodule.*"0.9.0"'
      with self.assertRaisesRegex(ImportError, match):
        import_optional_dependency('fakemodule')

      # Test min_version parameter
      result = import_optional_dependency('fakemodule', min_version='0.8')
      self.assertIs(result, module)

      with self.assertWarns(UserWarning):
        result = import_optional_dependency('fakemodule', errors='warn')
      self.assertIsNone(result)

      module.__version__ = '1.0.0'  # exact match is OK
      result = import_optional_dependency('fakemodule')
      self.assertIs(result, module)

  def test_submodule(self):
    # Create a fake module with a submodule
    name = 'fakemodule'
    module = types.ModuleType(name)
    module.__version__ = '0.9.0'
    sys.modules[name] = module
    sub_name = 'submodule'
    submodule = types.ModuleType(sub_name)
    setattr(module, sub_name, submodule)
    sys.modules[f'{name}.{sub_name}'] = submodule
    
    with mock.patch.dict(VERSIONS, {name: '1.0.0'}):

      match = 'Heartandsole requires .*1.0.0.* of .fakemodule.*"0.9.0"'
      with self.assertRaisesRegex(ImportError, match):
        import_optional_dependency('fakemodule.submodule')

      with self.assertWarns(UserWarning):
        result = import_optional_dependency('fakemodule.submodule', errors='warn')
      self.assertIsNone(result)

      module.__version__ = '1.0.0'  # exact match is OK
      result = import_optional_dependency('fakemodule.submodule')
      self.assertIs(result, submodule)

  def test_no_version_raises(self):
    name = 'fakemodule'
    module = types.ModuleType(name)
    sys.modules[name] = module

    with mock.patch.dict(VERSIONS, {name: '1.0.0'}):

      with self.assertRaisesRegex(ImportError, 'Can\'t determine .* fakemodule'):
        import_optional_dependency(name)