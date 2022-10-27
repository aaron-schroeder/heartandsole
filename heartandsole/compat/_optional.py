'''Based on pandas.compat._optional.

https://github.com/pandas-dev/pandas/blob/v1.2.4/pandas/compat/_optional.py

NOTE:
  * distutils discontinued here:
    https://github.com/pandas-dev/pandas/blob/f40e58cc50abcd03efae372df0586467a957f695/pandas/compat/_optional.py
    https://github.com/pandas-dev/pandas/pull/41207

'''
import distutils.version
import importlib
import sys
import warnings

# (pandas comment)
# Update install.rst when updating versions!

VERSIONS = {
  'fitparse': '1.1.0',
  'pandas_xyz': '0.0.5',
  'activereader': '0.0.2',
  # 'query': 0.0.1,
}

# A mapping from import name to package name (on PyPI) for packages where
# these two names are different.

INSTALL_MAPPING = {
  'pandas_xyz': 'pandas-xyz',
  # 'query': 'elevation-query',
}


def get_version(module):
  """
  Args:
  module (ModuleType): 

  Returns:
  str: version number of the installed module.
  
  """
  version = getattr(module, '__version__', None)
  if version is None:
    # xlrd uses a capitalized attribute name
    version = getattr(module, '__VERSION__', None)

  if version is None:
    raise ImportError(f'Can\'t determine version for {module.__name__}')
  return version


def import_optional_dependency(
  name, extra='', errors='raise', min_version=None,
):
  """Import an optional dependency.
  
  By default, if a dependency is missing an ImportError with a nice
  message will be raised. If a dependency is present, but too old,
  we raise.
  
  Args:
  name (str): The module name. This should be top-level only, so that
    the version may be checked.
  extra (str): Additional text to include in the ImportError message.
  errors (str): What to do when a dependency is not found or its
    version is too old.
    * raise : Raise an ImportError
    * warn : Only applicable when a module's version is to old.
      Warns that the version is too old and returns None
    * ignore: If the module is not installed, return None, otherwise,
      return the module, even if the version is too old.
      It's expected that users validate the version locally when
      using ``errors="ignore"``
  min_version (str): Specify a minimum version that is different from
    the global Heartandsole minimum version required. Default None.

  Returns:
  Optional[ModuleType]
    The imported module, when found and the version is correct.
    None is returned when the package is not found and
    `raise_on_missing` is False, or when the package's version
    is too old and `errors` is ``'warn'``.
  """

  assert errors in {'warn', 'raise', 'ignore'}

  package_name = INSTALL_MAPPING.get(name)
  install_name = package_name if package_name is not None else name

  msg = (
    f'Missing optional dependency "{install_name}". {extra} '
    f'Use pip to install {install_name}.'
  )
  try:
    module = importlib.import_module(name)
  except ImportError:
    if errors == 'raise':
      raise ImportError(msg) from None
    else:
      return None

  # Handle submodules: if we have submodule, grab parent module from sys.modules
  parent = name.split('.')[0]
  if parent != name:
    install_name = parent
    module_to_get = sys.modules[install_name]
  else:
    module_to_get = module
  minimum_version = min_version if min_version is not None else VERSIONS.get(parent)
  if minimum_version:
    version = get_version(module_to_get)
    if distutils.version.LooseVersion(version) < minimum_version:
      msg = (
        f'Heartandsole requires version "{minimum_version}" or newer of "{parent}" '
        f'(version "{version}" currently installed).'
      )
      if errors == 'warn':
        warnings.warn(msg, UserWarning)
        return None
      elif errors == 'raise':
        raise ImportError(msg)

  return module