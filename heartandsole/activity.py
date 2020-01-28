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

  # Fields that will exist as columns in the DataFrame from
  # potentially multiple elevation sources.
  ELEV_FIELDS = ['elevation', 'grade', 'power', 'power_smooth']

  def __init__(self, df, remove_stopped_periods=False):
    """Creates an Activity from a formatted pandas.DataFrame.

    Args:
      df: A pandas.DataFrame representing data read in from an 
          activity file. Formatted one of two ways: according to the
          scheme defined by the output of FileReader.data, or according
          to the scheme defined in Activity.data (two 
      remove_stopped_periods: If True, regions of data with speed below
                              a threshold will be removed from the data.
                              Default is False.
    TODO(aschroeder): Beef up the checks on the data format.
    """
    self._remove_stopped_periods = remove_stopped_periods

    # To enforce conformity to 1-second spacing between records,
    # calulate corrections to the timestamp column. This fixes errors 
    # due to rounding the time to the second, and due to timekeeping
    # changes when the device resets its time using GPS. 
    timesteps = df['timestamp'].diff()
    timesteps.iloc[0] = datetime.timedelta(seconds=1)
    errs = datetime.timedelta(seconds=1) - timesteps
    corrections = errs.cumsum()

    # Correct the timestamp column.
    df['timestamp'] = df['timestamp'] + corrections

    # Correct the index labels of the offset level. These operations
    # are equivalent to creating an evenly-1sec-spaced index starting
    # at the activity start time.
    # TODO: How to make this efficient and DRY? I named the levels at
    #       another point, and now I am re-creating and re-naming them.
    #       Some way to surgically repair level 1 in-place?
    corrected_offset = df.index.get_level_values('offset') + corrections
    index_arrays = [df.index.get_level_values('block').to_list(),
                    corrected_offset.to_list()]
    df.index = pandas.MultiIndex.from_arrays(index_arrays,
                                             names=('block', 'offset'))

    self.data = df.copy()

    # Calculate elapsed time before possibly removing data from
    # stoppages.
    self.elapsed_time = self.data.index.get_level_values('offset')[-1]

    # Calculated when needed and memoized here.
    self._moving_time = None
    self._norm_power = None

    # Add a second index level to the columns to distinguish between
    # identically named columns corresponding to different elevation
    # data. If the DataFrame already has two column levels, do nothing.
    if 'elev_source' not in self.data.columns.names:
      # For fields that have no possible alternate sources, like speed,
      # leave the elev_source level value blank, so that these columns
      # can be accessed based on their field name alone.
      index_tups = [(field_name, 'file') if field_name in self.ELEV_FIELDS
                    else (field_name, '') for field_name in self.data.columns]
      multiindex = pandas.MultiIndex.from_tuples(index_tups,
                                                 names=('field', 'elev_source'))
      self.data.columns = multiindex

    # Assume all null cadence data corresponds to no movement.
    if self.has_cadence:
      self.data['cadence', ''].fillna(0, inplace=True)

    # Assuming missing elevations only occur at the start of the file
    # (before satellite acquisition), backfill the first valid value
    # to the beginning of the DataFrame.
    if self.has_source('file'):
      self.data['elevation', 'file'].fillna(method='bfill', inplace=True)
    
    # Assuming that missing elevation values happen exclusively at the
    # beginning and end of the series: extend the first non-null value
    # backward to the start of the DataFrame, and extend the last non-null
    # value forward to the end of the DataFrame.
    if self.has_position:
      self.data['lon', ''].fillna(method='bfill', inplace=True)
      self.data['lon', ''].fillna(method='ffill', inplace=True)
      self.data['lat', ''].fillna(method='bfill', inplace=True)
      self.data['lat', ''].fillna(method='ffill', inplace=True)

    if self.has_speed or self.has_distance:
      self._clean_up_speed_and_distance()

  def _clean_up_speed_and_distance(self):
    """Infers true value of null / missing speed and distance values."""
    if self.has_speed:
      # If speed is NaN, assume no movement.
      # TODO(aschroeder) does it make sense to fill these in?
      # Should they be left as null and handled in @property?
      self.data['speed', ''].fillna(0., inplace=True)

    if self.has_distance:
      # If distance is NaN, fill in with first non-NaN distance.
      # This assumes the dataframe has no trailing NaN distances.
      # TODO(aschroeder) does it make sense to fill these in?
      # Should they be left as null and handled in @property?
      self.data['distance', ''].fillna(method='bfill', inplace=True)

    # TODO: If speed exists but distance does not, calculate distances.
    if self.has_speed and not self.has_distance:
      pass

    # If distance exists but speed does not, calculate speeds.
    # TODO: Filter this speed series for noise.
    if self.has_distance and not self.has_speed:
      self.data['speed', ''] = np.gradient(
          self.data['distance', ''].values,
          self.data.index.get_level_values('offset').seconds)
      self.data['speed', ''].fillna(0., inplace=True)

  def add_elevation_source(self, elev_list, name):
    """Adds an alternate elevation column to the DataFrame.

    A Multi Index distinguishes between columns containing fields 
    calculated using different elevation sources.

    Args:
      elev_list: a list of elevation values at each timestep, in meters.
      name: a string to be used as the value of the source index.
    """
    self.data['elevation', name] = elev_list
    self.data['elevation', name].fillna(method='bfill', inplace=True)

  @property
  def file_data(self):
    """Returns a DataFrame that consists only of data from the file.

    The full DataFrame may have data from other sources. This property
    takes the full MultiIndexed DataFrame and distills it to a
    single-Indexed DataFrame.
    """
    return self.data.xs('file', level='elev_source', axis=1)

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

  def has_source(self, source_name):
    return source_name in self.data.columns.get_level_values('elev_source')

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
      return self.data[self.data['speed'] > self.STOPPED_THRESHOLD]['cadence']

    return self.data['cadence']

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
    """TODO: Decide on heart_rate or hr, and be consistent."""
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
    # TODO: Remove this assumption.
    return self.speed.sum() / self.moving_time.total_seconds()

  @property
  def distance(self):
    if not self.has_distance:
      return None
  
    return self.data['distance']

  def elevation(self, source_name='file'):
    if not (self.has_elevation and self.has_source(source_name)):
      return None

    return self.data['elevation', source_name]

  def grade(self, source_name='file'):
    if not (self.has_elevation and self.has_source(source_name)):
      return None

    if ('grade', source_name) not in self.data.columns:
      grade_array = sf.grade_smooth(self.distance, self.elevation(source_name))
      self.data['grade', source_name] = grade_array 

    #return pandas.Series(data=grade_array, index=self.data.index)    
    return self.data['grade', source_name]

  def power(self, source_name='file'):
    if not (self.has_speed and self.has_source(source_name)):
      return None

    if ('power', source_name) not in self.data.columns:
      power_array = pu.run_power(self.speed, self.grade(source_name))
      self.data['power', source_name] = power_array

    #return pandas.Series(data=power_array, index=self.data.index)
    return self.data['power', source_name]

  def power_smooth(self, source_name='file'):
    if not (self.has_speed and self.has_source(source_name)):
      return None

    if ('power_smooth', source_name) not in self.data.columns:
      p = self.power(source_name=source_name)  #.copy()
      p.index = p.index.droplevel(level='block')
      power_array =  heartandsole.util.moving_average(p, 30)
      self.data['power_smooth', source_name] = power_array

    return self.data['power_smooth', source_name]

  def equiv_speed(self, source_name='file'):
    """Calculates the flat-ground pace that would produce equal power.

    Takes the 30-second moving average power, and inverts the pace-power
    equation to calculate equivalent pace.

    TODO: Decide on missing-elevation-handling. Return smoothed pace,
          or return None?    

    If elevation values aren't included in the file, the power values
    are simply a function of speed, and then are smoothed with a 
    30-second moving average. In that case, equivalent paces shouldn't
    be too far off from actual paces.
    """
    if not (self.has_speed and self.has_source(source_name)):
      return None

    return pu.flat_speed(self.power_smooth(source_name=source_name))

  def mean_equiv_speed(self, source_name='file'):
    if not (self.has_speed and self.has_source(source_name)):
      return None

    # Assumes each speed value was maintained for 1 second.
    return self.equiv_speed(source_name=source_name).sum()  \
           / self.moving_time.total_seconds()

  def mean_power(self, source_name='file'):
    if not (self.has_speed and self.has_source(source_name)):
      return None

    return self.power(source_name=source_name).mean()

  def norm_power(self, source_name='file'):
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
    if not (self.has_speed and self.has_source(source_name)):
      return None

    return su.lactate_norm(self.power_smooth(source_name=source_name))

  def power_intensity(self, threshold_power, source_name='file'):
    """Calculates the intensity factor of the activity.

    One definition of an activity's intensity factor is the ratio of
    normalized power to threshold power (sometimes called FTP). 
    See (Coggan, 2016) cited in README for more details.

    Args:
      threshold_power: Threshold power in Watts/kg.

    Returns:
      Intensity factor as a float.
    """
    if not (self.has_speed and self.has_source(source_name)):
      return None

    return self.norm_power(source_name=source_name) / float(threshold_power)

  def power_training_stress(self, threshold_power, source_name='file'):
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
    if not (self.has_speed and self.has_source(source_name)):
      return None

    return su.training_stress(self.power_intensity(threshold_power,
                                                   source_name=source_name),
                              self.moving_time.total_seconds())

  def hr_intensity(self, threshold_hr):
    """Calculates the heart rate-based intensity factor of the activity.

    One definition of an activity's intensity factor is the ratio of
    average heart rate to threshold heart rate. This heart rate-based
    intensity is similar to TrainingPeaks hrTSS value. This calculation
    uses lactate-normalized heart rate, rather than average heart rate.
    This intensity factor should agree with the power-based intensity
    factor, because heart rate behaves similarly to a 30-second moving
    average of power, this heart rate intensity factor should agree with
    the power-based intensity factor. Both calculations involve a
    4-norm of power (or of a proxy in this case).

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

  @classmethod
  def from_csv(cls, filepath):
    """Creates and returns an Activity from a .csv file.

    Args:
      filepath: Path to a .csv file containing data that is structured
                identically to activity.data.to_csv(): a multi-level
                index with block and offset, and a multi-level column
                system with field and elev_source.
    """ 
    # Read the data from the csv file, assuming the third column of the
    # file represents timestamp and parsing it as a datetime.
    data = pandas.read_csv(filepath, index_col=[0, 1],
                           header=[0, 1], parse_dates=[2])
    
    # Convert the index's 'offset' level to TimedeltaIndex.
    data.index = data.index.set_levels(
        pandas.TimedeltaIndex(data.index.get_level_values('offset')),
        level='offset')

    # Fix column level values, an artifact of blank level values in a
    # .csv file.
    fields = data.columns.get_level_values('field')
    srcs = data.columns.get_level_values('elev_source').str.replace('Un.*', '')
    col_tups = [(field, src) for field, src in zip(fields, srcs)]
    data.columns = pandas.MultiIndex.from_tuples(col_tups,
                                                 names=data.columns.names)

    return cls(data, remove_stopped_periods=False)
