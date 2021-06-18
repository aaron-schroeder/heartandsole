# heartandsole: Python library for analysis of running data files

[![PyPI Latest Release](https://img.shields.io/pypi/v/heartandsole.svg)](https://pypi.org/project/heartandsole/)
[![License](https://img.shields.io/pypi/l/heartandsole.svg)](https://github.com/aaron-schroeder/heartandsole/blob/master/LICENSE)
[![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/)

## Table of Contents                                                                    
- [Introduction](#introduction)
- [Dependencies](#dependencies)
- [Installation](#installation)
- [Example](#example)
- [License](#license)
- [Documentation](#documentation)
- [Contact](#contact)

## Introduction

heartandsole is designed to work with running activity files.
It reads data from `.fit`, `.tcx`, `.gpx`, and `.csv` files, converts it to
pandas data structures, then performs calculations and summarizes the data,
for example:
<!-- - running power (based on Dr. Philip Friere Skiba's GOVSS algorithm)
- average running power
- normalized running power (based on information publicly available about
  TrainingPeaks' NP® and NGP®, and Dr. Philip Friere Skiba's GOVSS algorithm)
- intensity (based on information publicly available about TrainingPeaks' IF®)
- training stress (based on information publicly available about
  TrainingPeaks' TSS® and Dr. Philip Friere Skiba's GOVSS algorithm)
- average heart rate -->
- elevation gain
- elapsed time
- timer time
- distance from GPS coordinates

## Dependencies

[Pandas](http://pandas.pydata.org/) and [NumPy](http://www.numpy.org/) are required.

A number of optional dependencies enable various features, such as
reading data from specific activity file formats and performing geospatial
calculations:

 - [fitparse](https://github.com/dtcooper/python-fitparse) allows data
   to be read in from `.fit` files.
 - [activereader](https://github.com/aaron-schroeder/pandas-xyz) allows data
   to be read in from `.tcx` and `.gpx` files.
 - [pandas-xyz](https://github.com/aaron-schroeder/pandas-xyz) allows geospatial
   calculations, like converting GPS coordinates to distance and determining
   elevation gain along a route.

## Installation

`pip install heartandsole` to install.

## Example

heartandsole provides the `Activity` class. 

Activities can be constructed manually with a required records DataFrame 
and optional summary Series and laps DataFrame, or they can be constructed
directly from various activity file formats using `Activity.from_*` class
methods.

```python
from heartandsole import Activity

# Reading from a fit file requires the fitparse package to be
# installed.
activity = heartandsole.Activity.from_fit('my_activity.fit')

# Various field accessors provide methods related to specific data fields
# commonly found in activity files.
print(activity.time.elapsed(source='records'))
print(activity.time.timer(source='summary'))

# Geospatial calculations require pandas-xyz to be installed.
print(activity.elevation.gain(source='records'))  # scalar
print(activity.distance.records_from_position())  # Series
```

## License

[![License](https://img.shields.io/pypi/l/heartandsole.svg)](https://github.com/aaron-schroeder/heartandsole/blob/master/LICENSE)

This project is licensed under the MIT License. See
[LICENSE](https://github.com/aaron-schroeder/heartandsole/blob/master/LICENSE)
file for details.

## Documentation

The official documentation is hosted on readthedocs.io: https://heartandsole.readthedocs.io/en/stable

## Background

My impetus for this project was to implement a version of Philip Friere Skiba's 
GOVSS algorithm (with tweaks to better align with the underlying research). 
The end result will be a free, open-source version of proprietary calculations
found in platforms like Strava and Training Peaks (eventually - bear with me).
My hope is that other runners will benefit as I have from taking these secret
algorithms out of their black box, by understanding the science behind these 
calculations, and training smarter.

This package was originally forked from Michael Traver's 
[fitanalysis package](https://github.com/mtraver/python-fitanalysis), but the two
projects diverged significantly enough for me to move my fork to a separate 
repository. I am indebted to Michael for writing such a clean, useful,
easy-to-understand package that served as heartandsole's starting point.

## Contact

Reach out to me at one of the following places!

- Website: [trailzealot.com](https://trailzealot.com)
- LinkedIn: [linkedin.com/in/aarondschroeder](https://www.linkedin.com/in/aarondschroeder/)
- Twitter: [@trailzealot](https://twitter.com/trailzealot)
- Instagram: [@trailzealot](https://instagram.com/trailzealot)
- GitHub: [github.com/aaron-schroeder](https://github.com/aaron-schroeder)

