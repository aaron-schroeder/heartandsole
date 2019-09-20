from distutils.core import setup
import sys

import heartandsole


requires = ['fitparse', 'numpy', 'pandas']
if sys.version_info < (2, 7):
  requires.append('argparse')

with open('LICENSE', 'r') as f:
  license_content = f.read()

setup(name='heartandsole',
      version=heartandsole.__version__,
      description='Python library for analysis of ANT/Garmin .fit files',
      author='Aaron Schroeder',
      url='https://github.com/aaron-schroeder/heartandsole',
      license=license_content,
      packages=['heartandsole'],
      install_requires=requires)
