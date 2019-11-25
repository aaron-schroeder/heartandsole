import datetime
import sys

import fitparse
import numpy as np
import pandas

import spatialfriend as sf

import heartandsole.powerutils as pu
import heartandsole.stressutils as su
import heartandsole.util


# Set to True to add a column to the DataFrame indicating whether a row would
# have been removed if removal of stopped periods were enabled, but don't
# actually remove it.
DEBUG_EXCISE = False


class Activity(object):
  """Represents a running activity.

  Construction of an Activity parses the DataFrame and detects periods
  of inactivity, as such periods must be removed from the data for
  certain calculations.

  TODO: 
    - Get auto-detected stops working.
    - Consider subclassing activity as a dataframe itself.
  """

  # Speeds less than or equal to this value (in m/s) are
  # considered to be stopped
  STOPPED_THRESHOLD = 0.3

  def __init__(self, df, remove_stopped_periods=False):
    """Creates an Activity from a formatted pandas.DataFrame.

    Args:
      df: A pandas.DataFrame representing data read in from an 
          activity file. Formatted according to the scheme defined by
          the output of FileReader.data.
      remove_stopped_periods: If True, regions of data with speed below
                              a threshold will be removed from the data.
                              Default is False.
    """
    self._remove_stopped_periods = remove_stopped_periods

    self.data = df

    # Calculate elapsed time before possibly removing data from
    # stoppages.
    self.elapsed_time = self.data.index.get_level_values('offset')[-1]

    # Calculated when needed and memoized here.
    self._moving_time = None
    self._norm_power = None

    # Clean up any data that was read in from file.
    if self.has_cadence:
      self.data['cadence'].fillna(0, inplace=True)

    if self.has_elevation:
      self.data['elevation'].fillna(method='bfill', inplace=True)
    
    if self.has_position:
      self.data[['lon', 'lat']].fillna(method='bfill').fillna(method='ffill')

    if self.has_speed or self.has_distance:
      self._clean_up_speed_and_distance()

  def _clean_up_speed_and_distance(self):
    """Infers true value of null / missing speed and distance values."""
    if self.has_speed:
      # If speed is NaN, assume no movement.
      # TODO(aschroeder) does it make sense to fill these in?
      # Should they be left as null and handled in @property?
      self.data['speed'].fillna(0., inplace=True)

    if self.has_distance:
      # If distance is NaN, fill in with first non-NaN distance.
      # This assumes the dataframe has no trailing NaN distances.
      # TODO(aschroeder) does it make sense to fill these in?
      # Should they be left as null and handled in @property?
      self.data['distance'].fillna(method='bfill', inplace=True)

    # TODO: If speed exists but distance does not, calculate distances.
    if self.has_speed and not self.has_distance:
      pass

    # If distance exists but speed does not, calculate speeds.
    # TODO: Filter this speed series for noise.
    if self.has_distance and not self.has_speed:
      self.data['speed'] = np.gradient(
          self.data['distance'].values,
          self.data.index.get_level_values('offset').seconds)
      #self.data['speed'] = self.data['distance'].diff() /  \
      #                     self.data.index.get_level_values('offset').seconds
      self.data['speed'].fillna(0., inplace=True)

  @property
  def moving_time(self):
    if self._moving_time is None:
      moving_time = 0
      for _, block_df in self.data.groupby(level='block'):
        # Calculate the number of seconds elapsed since the previous data point
        # and sum them to get the moving time
        moving_time += (
            (block_df['timestamp'] - block_df['timestamp'].shift(1).fillna(
                block_df.iloc[0]['timestamp'])) / np.timedelta64(1, 's')).sum()

      self._moving_time = datetime.timedelta(seconds=moving_time)

    return self._moving_time

  @property
  def has_cadence(self):
    return 'cadence' in self.data.columns

  @property
  def has_heart_rate(self):
    return 'heart_rate' in self.data.columns

  @property
  def has_speed(self):
    return 'speed' in self.data.columns

  @property
  def has_elevation(self):
    return 'elevation' in self.data.columns

  @property
  def has_distance(self):
    return 'distance' in self.data.columns

  @property
  def has_position(self):
    return 'lat' in self.data.columns and 'lon' in self.data.columns

  @property
  def cadence(self):
    if not self.has_cadence:
      return None

    if self._remove_stopped_periods:
      return self.data[
          self.data['cadence'].notnull() & (self.data['cadence'] > 0)
          & (self.data['speed'] > self.STOPPED_THRESHOLD)]['cadence']

    return self.data[
        self.data['cadence'].notnull() & (self.data['cadence'] > 0)]['cadence']

  @property
  def mean_cadence(self):
    if not self.has_cadence:
      return None

    return self.cadence.mean()

  @property
  def heart_rate(self):
    if not self.has_heart_rate:
      return None

    if self._remove_stopped_periods:
      return self.data[self.data['heart_rate'].notnull()
                       & self.data['speed'] 
                         > self.STOPPED_THRESHOLD]['heart_rate']

    return self.data[self.data['heart_rate'].notnull()]['heart_rate']

  @property
  def mean_hr(self):
    if not self.has_heart_rate:
      return None

    return self.heart_rate.mean()

  @property
  def lonlats(self):
    if not self.has_position:
      return None

    return self.data[['lon', 'lat']].values.tolist()

  @property
  def latlons(self):
    if not self.has_position:
      return None

    return self.data[['lat', 'lon']].values.tolist()

  @property
  def speed(self):
    if not self.has_speed:
      return None

    if self._remove_stopped_periods:
      return self.data[self.data['speed'].notnull()
                       & self.data['speed'] 
                         > self.STOPPED_THRESHOLD]['speed']

    # TODO: Decide how I feel about this notnull() business.
    #       I should be able to clean the data, or maybe not,
    #       in which case it should be handled rather than hidden.
    return self.data[self.data['speed'].notnull()]['speed']

  @property
  def mean_speed(self):
    if not self.has_speed:
      return None

    # Assumes each speed value was maintained for 1 second.
    return self.speed.sum() / self.moving_time.total_seconds()

  @property
  def distance(self):
    if not self.has_distance:
      return None
  
    return self.data['distance']

  @property
  def elevation(self):
    if not self.has_elevation:
      return None

    return self.data['elevation']  

  @property
  def grade(self):
    if not self.has_elevation:
      return None

    if 'grade' not in self.data.columns:
      self.data['grade'] = sf.grade_smooth(self.distance,
                                           self.elevation)

    return self.data['grade']

  @property
  def power(self):
    if not self.has_speed:
      return None

    if 'power' not in self.data.columns:
      self.data['power'] = pu.run_power(self.speed, self.grade)

    if self._remove_stopped_periods:
      return self.data[self.data['power'].notnull()
                       & self.data['speed'] 
                       > self.STOPPED_THRESHOLD]['power']

    return self.data[self.data['power'].notnull()]['power']

  @property
  def power_smooth(self):
    if not self.has_speed:
      return None

    if 'power_smooth' not in self.data.columns:
      p = self.power
      p.index = p.index.droplevel(level='block')
    
      self.data['power_smooth'] = heartandsole.util.moving_average(p, 30)

    return self.data['power_smooth']


  @property
  def equiv_speed(self):
    """Calculates the flat-ground pace that would produce equal power.

    Takes the 30-second moving average power, and inverts the pace-power
    equation to calculate equivalent pace.

    If elevation values aren't included in the file, the power values
    are simply a function of speed, and then are smoothed with a 
    30-second moving average. In that case, equivalent paces shouldn't
    be too far off from actual paces.
    """
    if not self.has_speed:
      return None

    if not self.has_elevation:
      return self.speed

    return pu.flat_speed(self.power_smooth)

  @property
  def mean_equiv_speed(self):
    if not self.has_speed:
      return None

    # Assumes each speed value was maintained for 1 second.
    return self.equiv_speed.sum() / self.moving_time.total_seconds()

  @property
  def mean_power(self):
    if not self.has_speed:
      return None

    return self.power.mean()

  @property
  def norm_power(self):
    """Calculates the normalized power for the activity.

    See (Coggan, 2003) cited in README for details on the rationale behind the
    calculation.

    Normalized power is based on a 30-second moving average of power. Coggan's
    algorithm specifies that the moving average should start at the 30 second
    point in the data, but this implementation does not (it starts with the
    first value, like a standard moving average). This is an acceptable
    approximation because normalized power shouldn't be relied upon for efforts
    less than 20 minutes long (Coggan, 2012), so how the first 30 seconds are
    handled doesn't make much difference. Also, the values computed by this
    implementation are very similar to those computed by TrainingPeaks, so
    changing the moving average implementation doesn't seem to be critical.

    This function also does not specially handle gaps in the data. When a pause
    is present in the data (either from autopause on the recording device or
    removal of stopped periods in post-processing) the timestamp may jump by a
    large amount from one sample to the next. Ideally this should be handled in
    some way that takes into account the physiological impact of that rest, but
    currently this algorithm does not. But again, the values computed by this
    implementation are very similar to those computed by TrainingPeaks, so
    changing gap handling doesn't seem to be critical.

    Args:
      power_series: A pandas.Series of the run power values to average,
                    indexed with timestamps. Typical units are Watts/kg.

    Returns:
      Normalized power as a float.
    """
    if not self.has_speed:
      return None

    return su.lactate_norm(self.power_smooth)

  def power_intensity(self, threshold_power):
    """Calculates the intensity factor of the activity.

    One definition of an activity's intensity factor is the ratio of
    normalized power to threshold power (sometimes called FTP). 
    See (Coggan, 2016) cited in README for more details.

    Args:
      threshold_power: Threshold power in Watts/kg.

    Returns:
      Intensity factor as a float.
    """
    if not self.has_speed:
      return None

    return self.norm_power / float(threshold_power)

  def power_training_stress(self, threshold_power):
    """Calculates the power-based training stress of the activity.

    This is essentially a power-based version of Banister's 
    heart rate-based TRIMP (training impulse). Normalized power is 
    used instead of average power because normalized power properly 
    emphasizes high-intensity work. This and other training stress
    values are scaled so that a 60-minute effort at threshold intensity
    yields a training stress of 100. 

    Args:
      threshold_power: Threshold power in Watts/kg.

    Returns:
      Power-based training stress as a float.
    """
    if not self.has_speed:
      return None

    return su.training_stress(self.power_intensity(threshold_power),
                              self.moving_time.total_seconds())

  def hr_intensity(self, threshold_hr):
    """Calculates the heart rate-based intensity factor of the activity.

    One definition of an activity's intensity factor is the ratio of
    average heart rate to threshold heart rate. This heart rate-based
    intensity is similar to TrainingPeaks hrTSS value. This calculation
    uses lactate-normalized heart rate, rather than average heart rate.
    This intensity factor should agree with the power-based intensity
    factor, Because heart rate behaves similarly to a 30-second moving
    average of power, this heart rate intensity factor should agree with
    the power-based intensity factor. Both calculations involve a
    4-norm of power (or a proxy in this case).

    Args:
      threshold_hr: Threshold heart rate in bpm.

    Returns:
      Heart rate-based intensity factor as a float.
    """
    if not self.has_heart_rate:
      return None

    return su.lactate_norm(self.heart_rate) / threshold_hr

  def hr_training_stress(self, threshold_hr):
    """Calculates the heart rate-based training stress of the activity.

    Should yield a value in line with power_training_stress. See the
    documentation for hr_intensity and power_training_stress. 

    Args:
      threshold_hr: Threshold heart rate in bpm.

    Returns:
      Heart rate-based training stress as a float.
    """
    if not self.has_heart_rate:
      return None

    return su.training_stress(self.hr_intensity(threshold_hr),
                              self.moving_time.total_seconds())
