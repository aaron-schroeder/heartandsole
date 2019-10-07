# heartandsole

> Python library for analysis of running data files.

[![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)](https://www.python.org/downloads/release/python-360/)
[![License](http://img.shields.io/:license-mit-blue.svg)](http://badges.mit-license.org)

---

## Table of Contents                                                                    
- [Introduction](#introduction)
- [Dependencies and Installation](#dependencies-and-installation)
- [Example](#example)
- [Project Status](#project-status)
- [References](#references)
- [Contact](#contact)
- [License](#license)

---

## Introduction

heartandsole is designed to work with running or walking activity files.
It allows for extraction of data from a `.fit` file as well as calculations,
such as the following:
- elapsed time
- moving time
- average heart rate
- running power (based on Dr. Philip Friere Skiba's GOVSS algorithm)
- average running power
- normalized running power (based on information publicly available about
  TrainingPeaks' NP® and NGP®, and Dr. Philip Friere Skiba's GOVSS algorithm)
- intensity (based on information publicly available about TrainingPeaks' IF®)
- training stress (based on information publicly available about
  TrainingPeaks' TSS® and Dr. Philip Friere Skiba's GOVSS algorithm)

My impetus for this project was to implement a version of Philip Friere Skiba's 
GOVSS algorithm (with tweaks to better align with the underlying research). 
The end result will be a free, open-source version of proprietary calculations
found in platforms like Strava and Training Peaks. My hope is that other runners
will benefit as I have from taking these secret algorithms out of their black box, 
by understanding the science behind these calculations and training smarter.

This package was originally forked from Michael Traver's 
[fitanalysis package](https://github.com/mtraver/python-fitanalysis), but the two
projects diverged significantly enough for me to move my fork to a separate 
repository. I am indebted to Michael for writing such a clean, useful,
easy-to-understand package that served as heartandsole's starting point.

---

## Dependencies and Installation

[Pandas](http://pandas.pydata.org/), [NumPy](http://www.numpy.org/), [fitparse](https://github.com/dtcooper/python-fitparse), and [spatialfriend](https://github.com/aaron-schroeder/spatialfriend) are required.

`pip install heartandsole` to install.

---

## Example

heartandsole provides the `Activity` class.

```python
import heartandsole

activity = heartandsole.Activity('my_activity.fit')

print(activity.elapsed_time)
print(activity.moving_time)

# Also available for heart rate and cadence.
print(activity.mean_power)

# Uses power values from .fit file if available,
# otherwise calculates running power from speed,
# distance, and elevation data.
print(activity.norm_power)

# Intensity and training stress calculations require
# a functional threshold power value (in Watts/kg).
print(activity.intensity(17.0))
```

Construction of an `Activity` parses the `.fit` file and detects periods of
inactivity. The decision to remove inactive periods is left to the user.

---

## Project Status

### Complete

### Current Activities

### Future Work

---

## References

Coggan, A. (2012, June 20). Re: Calculate Normalised Power for an Interval [Online forum comment]. Retrieved June 14, 2017, from http://www.timetriallingforum.co.uk/index.php?/topic/69738-calculate-normalised-power-for-an-interval/&do=findComment&comment=978386

Coggan, A. (2016, February 10). Normalized Power, Intensity Factor and Training Stress Score. _TrainingPeaks_. Retrieved June 14, 2017, from
https://www.trainingpeaks.com/blog/normalized-power-intensity-factor-training-stress/

Coggan, A. (2003, March 13). TSS and IF - at last! [Online forum post]. Retrieved June 14, 2017, from http://lists.topica.com/lists/wattage/read/message.html?mid=907028398&sort=d&start=9353

Di Prampero, P. E., Atchou, G., Brückner, J. C., & Moia, C. (1986). The energetics of endurance running. _European Journal of Applied Physiology and Occupational Physiology, 55_(3), 259-266.

Di Prampero, P. E., Capelli, C., Pagliaro, P., Antonutto, G., Girardis, M., Zamparo, P., & Soule, R. G. (1993). Energetics of best performances in middle-distance running. _Journal of Applied Physiology, 74_(5), 2318-2324.

Eckner, A. (2017, April 3). Algorithms for Unevenly Spaced Time Series: Moving Averages and Other Rolling Operators. Retrieved June 14, 2017, from http://eckner.com/papers/Algorithms%20for%20Unevenly%20Spaced%20Time%20Series.pdf

Friel, J. (2009, September 21). Estimating Training Stress Score (TSS). _TrainingPeaks_. Retrieved June 22, 2017, from https://www.trainingpeaks.com/blog/estimating-training-stress-score-tss/

Minetti, A. E., Moia, C., Roi, G. S., Susta, D., & Ferretti, G. (2002). Energy cost of walking and running at extreme uphill and downhill slopes. _Journal of Applied Physiology, 93_(3), 1039-1046.

Pugh, L. G. E. (1971). The influence of wind resistance in running and walking and the mechanical efficiency of work against horizontal or vertical forces. _The Journal of Physiology, 213_(2), 255-276.

Skiba, P. F. (2006, September 16). Calculation of Power Output and Quantification of Training Stress in Distance Runners: The Development of the GOVSS Algorithm. _RunScribe_. Retrieved August 20, 2019, from http://runscribe.com/wp-content/uploads/power/GOVSS.pdf

---

## Contact

Reach out to me at one of the following places!

- Website: <a href="https://trailzealot.com" target="_blank">trailzealot.com</a>
- LinkedIn: <a href="https://www.linkedin.com/in/aarondschroeder/" target="_blank">linkedin.com/in/aarondschroeder</a>
- Twitter: <a href="https://twitter.com/trailzealot" target="_blank">@trailzealot</a>
- Instagram: <a href="https://instagram.com/trailzealot" target="_blank">@trailzealot</a>
- GitHub: <a href="https://github.com/aaron-schroeder" target="_blank">github.com/aaron-schroeder</a>

---

## License

[![License](http://img.shields.io/:license-mit-blue.svg)](http://badges.mit-license.org)

This project is licensed under the MIT License. See
[LICENSE](https://github.com/aaron-schroeder/heartandsole/blob/master/LICENSE)
file for details.
