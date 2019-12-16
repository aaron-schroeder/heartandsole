"""Functions related to training stress."""

import numpy as np


def lactate_norm(series):
  """Weights a series of values using a lactate norm.

  The lactate norm is described in (Skiba, 2006) as a method to
  weight a time series of intensity values, like heart rate or power,
  to correspond to the physiological stress of a bout of exercise.
  In contrast to averaging, which emphasizes the contributions of
  high- and low-intensity efforts equally, the lactate norm reflects
  the significance of high-intensity bouts within a workout.

  Args:
    series: A pandas.Series of intensity-related values such as power,
            heart rate, or speed.
  Returns:
    The lactate norm of the series as a float.
  """
  return np.sqrt(np.sqrt(np.mean(series ** 4)))


def training_stress(intensity, moving_time_seconds):
  """Calculates the training stress of a time series.

  The concept behind this calculation is TrainingPeaks Training Stress
  Score (TSS), which awards 100 points to a 60-minute effort at
  threshold intensity. Training stress can be calculated from any
  intensity metric that has a threshold value, such as power, pace, or
  heart rate.

  Args:
    intensity: A factor that relates the intensity level of the activity
               to the threshold intensity level. 1.0 is threshold
               intensity, < 1.0 is sub-threshold, and > 1.0 is 
               super-threshold.
    moving_time_seconds: A float representing the duration of the
                         activity in seconds.
  Returns:
    Training stress based on the chosen intensity metric as a float.
  """
  return 100.0 * (moving_time_seconds / 3600.0) * intensity ** 2
