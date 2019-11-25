from setuptools import setup, find_packages
import sys


with open('README.md', 'r') as readme_file:
  readme = readme_file.read()

requirements = ['python-dateutil>=2.7.0', 'numpy>=1.14', 'pandas>=0.24',
                'lxml>=4.2.5', 'fitparse>=1', 'spatialfriend>=0.0.1']

setup(name='heartandsole',
      version='0.0.16',
      author='Aaron Schroeder',
      author_email='aaron@trailzealot.com',
      description='Python library for analysis of ANT/Garmin .fit files',
      long_description=readme,
      long_description_content_type='text/markdown',
      url='https://github.com/aaron-schroeder/heartandsole',
      packages=['heartandsole'],
      install_requires=requirements,
      license='MIT License',
      classifiers=['Programming Language :: Python :: 3.6',
                   'License :: OSI Approved :: MIT License',],)
