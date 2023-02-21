import os


def datapath(*relative_path_components):
  path = os.path.join(os.path.dirname(__file__), *relative_path_components)
  if not os.path.exists(path):
    raise ValueError(f'Could not find file {path}.')
  return path