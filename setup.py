import os
from setuptools import setup, find_packages


def read(rel_path):
  """Read a file so python does not have to import it.
  
  Inspired by (taken from) pip's `setup.py`.
  """
  here = os.path.abspath(os.path.dirname(__file__))
  # intentionally *not* adding an encoding option to open, See:
  #   https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
  with open(os.path.join(here, rel_path), 'r') as fp:
    return fp.read()


def get_version(rel_path):
  """Manually read through a file to retrieve its `__version__`.
  
  Inspired by (taken from) pip's `setup.py`.
  """
  for line in read(rel_path).splitlines():
    if line.startswith('__version__'):
      # __version__ = '0.0.1'
      delim = "'" if "'" in line else '"'
      return line.split(delim)[1]
  raise RuntimeError('Unable to find version string.')


with open('README.md', 'r') as readme_file:
  readme = readme_file.read()

requirements = ['numpy>=1.15', 'pandas>=1.0.0']

pkg_name = 'heartandsole'

setup(
  name=pkg_name,
  version=get_version(f'{pkg_name}/__init__.py'),
  author='Aaron Schroeder',
  author_email='aaron@trailzealot.com',
  description='Python library for analysis of running activity data',
  long_description=readme,
  long_description_content_type='text/markdown',
  url='https://github.com/aaron-schroeder/heartandsole',
  project_urls={
    'Documentation': 'https://heartandsole.readthedocs.io/en/stable/',
  },
  packages=find_packages(where='heartandsole'),
  package_dir={'': 'heartandsole'},
  install_requires=requirements,
  license='MIT License',
  classifiers=[
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.7',
    'License :: OSI Approved :: MIT License',
  ],
)
