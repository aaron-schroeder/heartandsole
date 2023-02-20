import os


def datapath(*args):
  """
  Get the path to a data file.
  Parameters
  ----------
  path : str
      Path to the file, relative to ``tests/``
  
  Returns
  -------
  path including ``tests``.
  
  Raises
  ------
  ValueError
      If the path doesn't exist.
  """
  BASE_PATH = os.path.dirname(__file__)
  path = os.path.join(BASE_PATH, *args)
  if not os.path.exists(path):
    raise ValueError(f'Could not find file {path}.')
  return path