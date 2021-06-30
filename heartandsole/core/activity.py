import datetime
import sys
import warnings

import numpy as np
import pandas as pd

from heartandsole.core.field import CachedField
from heartandsole.core.fields.cadence import CadenceField
from heartandsole.core.fields.distance import DistanceField
from heartandsole.core.fields.elevation import ElevationField
from heartandsole.core.fields.grade import GradeField
from heartandsole.core.fields.heartrate import HeartrateField
from heartandsole.core.fields.position import LatField, LonField
from heartandsole.core.fields.speed import SpeedField
from heartandsole.core.fields.time import TimeField
from heartandsole.core.fields.timestamp import TimestampField
from heartandsole.compat._optional import import_optional_dependency
import heartandsole.util


# Keep these names straight, in one place.
TIMESTAMP = TimestampField._field_name
TIME = TimeField._field_name
LAT = LatField._field_name
LON = LonField._field_name
SPEED = SpeedField._field_name
DISTANCE = DistanceField._field_name
ELEVATION = ElevationField._field_name
GRADE = GradeField._field_name
CADENCE = CadenceField._field_name
HEARTRATE = HeartrateField._field_name
MOVING = 'moving'
POWER = 'power'


class Activity(object):
  """Represents a running activity.

  Composed of one mandatory DataFrame representing record data 
  (rows=records, columns=fields), one optional DataFrame representing
  lap data (rows=laps, columns=stats), and one optional Series
  representing summary data (each element a summary statistic for the
  entire activity).

  Args:
    records (pandas.DataFrame): data records from an activity.
      Each column of the DataFrame corresponds to a data stream
      of some field, and each row is a record corresponding to a
      certain point in time.
    laps (pandas.DataFrame): lap data from the activity. Each row
      represents one lap and the index corresponds to lap number.
      Optional.
    summary (pandas.Series): summary data for the activity.
      Row values could be anything. Optional.

  Examples:

    Constructing an Activity from a records DataFrame.

    >>> df = pd.DataFrame(data=dict(
    ...   timestamp=[datetime.datetime(2019, 9, 1, second=i) for i in range(5)],
    ...   distance=[i * 3.0 for i in range(5)],
    ...   elevation=[1.0 * i for i in range(5)],
    ... ))
    >>> act = Activity(df)
    >>> act.records
                 timestamp  distance  elevation  time
    0  2019-09-01 00:00:00       0.0        0.0     0
    1  2019-09-01 00:00:01       3.0        1.0     1
    2  2019-09-01 00:00:02       6.0        2.0     2
    3  2019-09-01 00:00:03       9.0        3.0     3
    4  2019-09-01 00:00:04      12.0        4.0     4
    5  2019-09-01 00:00:05      15.0        5.0     5
    >>> act.summary
    Series([], dtype: object)
    >>> act.laps
    Empty DataFrame
    Columns: []
    Index: []

  TODO: 
    * Remove the primary source limitation. Allow a user to
      input a dataframe with sufficient information to make
      a special HNS one. This would facilitate reading in
      data from CSV files as well. 

  """

  _fields = {
    ELEVATION, DISTANCE, LAT, LON, TIMESTAMP, TIME, SPEED, HEARTRATE, CADENCE,
    GRADE,
  }

  # Memoize property attributes.
  _records = None
  _laps = pd.DataFrame([])
  _summary = pd.Series(
    [],
    dtype='object',
    index=pd.Index([], dtype='object')
  )

  def __init__(self, records, laps=None, summary=None):

    # Set properties.
    self.records = records
    if laps is not None:
      self.laps = laps
    if summary is not None:
      self.summary = summary

    # Drop any columns (DataFrame) or rows (Series) that lack data,
    # so we know data is good if the column or row exists.
    self.records.dropna(axis=1, how='all', inplace=True)
    self.laps.dropna(axis=1, how='all', inplace=True)
    self.summary.dropna(inplace=True)

    # Calculate new record streams based on what data is available.
    if self.timestamp.stream is not None and self.time.stream is None:
      self.time.records_from_timestamps(inplace=True)

    # TODO: Decide if this stays. Maybe move to properties.
    # Calcs are their own thing - universal across Activities.
    # start_time_naive = self.records['timestamp'].iloc[0]
    # end_time_naive = self.records['timestamp'].iloc[-1]
    # self.start_time = start_time_naive.replace(tzinfo=tzutc())
    # self.end_time = end_time_naive.replace(tzinfo=tzutc())
    # self.elapsed_time = self.end_time - self.start_time

  # --------------------------------------------------------------------
  # IO methods (to / from other formats)

  @classmethod
  def from_fit(cls, file_obj):
    """Construct an Activity from a .fit file.

    Args:
      file_obj: Any file-like object accepted by :class:`fitparse.FitFile`.
    
    Returns:
      Activity

    Examples:
      Provide a file path:

      >>> act = Activity.from_fit('my_activity.fit')

      Provide a file-like object:
      
      >>> file_obj = open('my_activity.fit', 'rb')
      >>> act = Activity.from_fit(file_obj)

      Provide a raw string of bytes:
      
      >>> file_obj = open('my_activity.fit', 'rb')
      >>> raw_fit_data = file_obj.read()
      >>> act = Activity.fom_fit(raw_fit_data)

    """
    fitparse = import_optional_dependency('fitparse')

    reader = fitparse.FitFile(file_obj)

    def _build_dataframe_from_msg(msg_type):

      return pd.DataFrame.from_records(
        [msg.get_values() for msg in reader.get_messages(msg_type)]
      )

    # msg_names = set(msg.name for msg in self.reader.get_messages())
    # print(msg_names)

    # 'file_id' messages (worthwhile maybe)
    # 'serial_number': 3888752595, 'time_created': (timestamp), 
    # 'manufacturer': 'garmin', 'garmin_product': 'fr220', 
    # 'number': None, 'type': 'activity'
    # msg_type = 'file_id'
    
    # Nothing worthwhile
    # msg_type = 'device_info'
    # msg_type = 'file_creator'
    # msg_type = 'unknown_22'
    # msg_type = 'unknown_79'
    # msg_type = 'unknown_141'
    # print(self._build_dataframe_from_msg(msg_type))

    # 'activity' messages. Typically only be one row. Exception if not.
    # No relevant data that doesn't also appear in 'session' messages.
    # Fields:
    # ['timestamp', 'total_timer_time', 'local_timestamp', 'num_sessions',
    #  'type', 'event', 'event_type', 'event_group']
    activities = _build_dataframe_from_msg('activity')
    if len(activities) > 1:
      raise ValueError('multi-activity files not supported')

    activities = activities.rename(columns=dict(
      timestamp=f'{TIMESTAMP}_end',
      total_timer_time=f'{TIME}_timer',
    ))

    activity_series = activities.iloc[0]

    # 'session' messages. Typically only one row. Exception if not.
    # Fields:
    # ['timestamp', 'start_time', 'start_position_lat', 'start_position_long',
    #  'total_elapsed_time', 'total_timer_time', 'total_distance',
    #  'total_strides', 'nec_lat', 'nec_long', 'swc_lat', 'swc_long',
    #  'message_index', 'total_calories', 'enhanced_avg_speed', 'avg_speed',
    #  'enhanced_max_speed', 'max_speed', 'total_ascent', 'total_descent',
    #  'first_lap_index', 'num_laps', 'avg_vertical_oscillation',
    #  'avg_stance_time_percent', 'avg_stance_time', 'event', 'event_type',
    #  'sport', 'sub_sport', 'avg_heart_rate', 'max_heart_rate',
    #  'avg_running_cadence', 'max_running_cadence', 'total_training_effect',
    #  'event_group', 'trigger', 'unknown_81', 'avg_fractional_cadence',
    #  'max_fractional_cadence', 'total_fractional_cycles']
    sessions = _build_dataframe_from_msg('session')
    if len(sessions) > 1:
      raise ValueError('multi-session files not supported')
    
    sessions = sessions.rename(columns=dict(
      start_time=f'{TIMESTAMP}_start',
      timestamp=f'{TIMESTAMP}_end',
      start_position_lat=f'{LAT}_start',
      start_position_long=f'{LON}_start',
      total_elapsed_time=f'{TIME}_elapsed',
      total_timer_time=f'{TIME}_timer',
      total_distance=f'{DISTANCE}_total',
      total_calories='calories',
      avg_speed=f'{SPEED}_avg',
      max_speed=f'{SPEED}_max',
      total_ascent=f'{ELEVATION}_gain',
      total_descent=f'{ELEVATION}_loss',
      avg_heart_rate=f'{HEARTRATE}_avg',
      max_heart_rate=f'{HEARTRATE}_max',
      avg_running_cadence=f'{CADENCE}_avg',
      max_running_cadence=f'{CADENCE}_max',
    ))

    session = sessions.iloc[0]

    # Verify that the session and activity data is the same.
    for field in [f'{TIMESTAMP}_end', f'{TIME}_timer']:
      if activity_series[field] != session[field]:
        # raise ValueError(f'Activity and session data disagree for {field}')
        warnings.warn(
          f'Activity and session data disagree for {field}: '
          f'(Activity = {activity_series[field]}; Session = {session[field]}). '
          f'Session values are used by default.'
        )

    summary = session

    # ['timestamp', 'start_time', 'start_position_lat', 'start_position_long',
    #  'end_position_lat', 'end_position_long', 'total_elapsed_time',
    #  'total_timer_time', 'total_distance', 'total_strides', 'unknown_27',
    #  'unknown_28', 'unknown_29', 'unknown_30', 'message_index',
    #  'total_calories', 'enhanced_avg_speed', 'avg_speed',
    #  'enhanced_max_speed', 'max_speed', 'total_ascent', 'total_descent',
    #  'wkt_step_index', 'avg_vertical_oscillation', 'avg_stance_time_percent',
    #  'avg_stance_time', 'event', 'event_type', 'avg_heart_rate',
    #  'max_heart_rate', 'avg_running_cadence', 'max_running_cadence',
    #  'intensity', 'lap_trigger', 'sport', 'event_group', 'sub_sport',
    #  'unknown_72', 'avg_fractional_cadence', 'max_fractional_cadence',
    #  'total_fractional_cycles']
    laps = _build_dataframe_from_msg('lap')

    laps = laps.rename(columns=dict(
      start_time=f'{TIMESTAMP}_start',
      timestamp=f'{TIMESTAMP}_end',
      start_position_lat=f'{LAT}_start',
      start_position_long=f'{LON}_start',
      end_position_lat=f'{LAT}_end',
      end_position_long=f'{LON}_end',
      total_elapsed_time=f'{TIME}_elapsed',
      total_timer_time=f'{TIME}_timer',
      total_distance=f'{DISTANCE}_total',
      total_calories='calories',
      avg_speed=f'{SPEED}_avg',
      max_speed=f'{SPEED}_max',
      total_ascent=f'{ELEVATION}_gain',
      total_descent=f'{ELEVATION}_loss',
      avg_heart_rate=f'{HEARTRATE}_avg',
      max_heart_rate=f'{HEARTRATE}_max',
      avg_running_cadence=f'{CADENCE}_avg',
      max_running_cadence=f'{CADENCE}_max',
      lap_trigger='trigger_method',
    ))

    records = _build_dataframe_from_msg('record')

    # TODO: Move this check to base file reader?
    if not records[TIMESTAMP].is_monotonic_increasing or records[TIMESTAMP].duplicated().any():
      warnings.warn('Something funky is going on with timestamps.', UserWarning)

    records = records.rename(columns=dict(
      position_lat=LAT,
      position_long=LON,
      altitude=ELEVATION,
      heart_rate=HEARTRATE
    ))

    # Drop BS cols if they are there
    # self.records = self.records.drop(
    #   columns=[
    #       'enhanced_speed',
    #       'enhanced_altitude',
    #       # 'timestamp', 
    #       # Garmin
    #       'unknown_88',
    #       # Wahoo
    #       'battery_soc',
    #   ], 
    #   errors='ignore',
    # )

    # TODO: Consider if records should be duplicated if they belong to
    # two bouts or laps...
    # Just noticed TCX files duplicate Trackpoints...

    # Create a row multiindex for records.
    # self.records.index.name = 'record'
    # self.records = self.records.set_index(['lap', 'bout'], append=True)

    # print(
    #   f'End time:\n'
    #   f'  Session: {sessions.iloc[0][f"{TIMESTAMP}_end"]}\n'
    #   f'  Activity: {self.activity.loc[f"{TIMESTAMP}_end"]}\n'
    #   f'  Last lap: {self.laps.iloc[-1][f"{TIMESTAMP}_end"]}\n'
    #   f'  Last record: {self.records.iloc[-1][f"{TIMESTAMP}"]}\n'
    #   f'  Last pause: {self.events[self.events["event_type"]=="stop_all"].iloc[-1][TIMESTAMP]}\n'
    #   f'  Full stop: {self.events[self.events["event_type"]=="stop_disable_all"].iloc[-1][TIMESTAMP]}\n'
    # )

    # return cls(records, laps, summary)

    activity = cls(records, laps, summary)

    # Convert semicircles to degrees
    activity.lat._convert_record_units(inplace=True)
    activity.lon._convert_record_units(inplace=True)

    # Convert cadence from RPM to strides per minute.
    activity.cadence._convert_units()

    # activity.elevation._set_record_stream('altitude')
    # activity.cadence._convert_record_units(orig='rpm')
    # activity.lat._set_record_stream('position_lat')
    # activity.lon._set_record_stream('position_long')
    # activity.heartrate._set_record_stream('heart_rate')

    # ------------------------------------------------------------------
    # Add 'bout' and 'lap' columns to record DF. 
    # TODO: Figure out how to make this not take so long. It ruins the
    # read-in process for large files. In general, I'll leave off the
    # lap/bout feature for all files for now.

    # If the record timestamp straddles two laps, put it into the
    # earlier lap.
    # activity.records['lap'] = [
    #   activity.laps.index[
    #     activity.timestamp.laps['start'].le(timestamp_rec)
    #     & activity.timestamp.laps['end'].ge(timestamp_rec)
    #     # laps[f'{TIMESTAMP}_start'].le(timestamp_rec)
    #     # & laps[f'{TIMESTAMP}_end'].ge(timestamp_rec)
    #   ][0]
    #   for timestamp_rec in activity.timestamp.stream
    # ]

    # events = _build_dataframe_from_msg('event')
    # start_events = events[events['event_type'] == 'start'].reset_index()
    # pause_events = events[events['event_type'] == 'stop_all'].reset_index()

    # # If the record timestamp straddles two bouts, put it into the
    # # earlier bout. (That should be impossible, but JIC)
    # activity.records['bout'] = [
    #   start_events.index[
    #     start_events['timestamp'].le(timestamp_rec)
    #     & pause_events['timestamp'].ge(timestamp_rec)
    #   ][0]
    #   for timestamp_rec in activity.timestamp.stream
    # ]

    # ------------------------------------------------------------------

    # Naive timestamps represent UTC in .fit files, which is the
    # default timezone assigned to naive timestamps by this method, which
    # affects the record DF column, summary Series elements, and 
    # lap DF columns.
    activity.timestamp.ensure_aware()

    return activity

  @classmethod
  def from_tcx(cls, file_obj):
    """Construct an Activity from a .tcx file.

    Args:
      file_obj: Any file-like object accepted by :class:`activereader.Tcx`
    Returns:
      Activity

    Examples:
      Provide a file path:

      >>> act = Activity.from_tcx('my_activity.tcx')

      Provide a raw string of bytes:
      
      >>> with open('my_activity.tcx', 'rb') as fb:
      ...   raw_data = fb.read()
      >>> act = Activity.fom_tcx(raw_data)

      Provide a string (no encoding info):

      >>> with open('my_activity.tcx', 'r') as f:
      ...   xml_string = f.read()
      >>> act = Activity.fom_tcx(xml_string)
    
    """
    activereader = import_optional_dependency('activereader')

    reader = activereader.Tcx.from_file(file_obj)

    activities = pd.DataFrame.from_records([
      {
        'sport': act.sport,
        'device': act.device,
        'unit_id': act.device_id,
        'product_id': act.product_id,
      } for act in reader.activities
    ])

    if len(activities) > 1:
      raise ValueError('multi-activity files not supported')

    summary = activities.iloc[0]

    laps = pd.DataFrame.from_records([
      # lap.to_dict()
      {
        f'{TIMESTAMP}_start': lap.start_time,
        f'{TIME}_timer': lap.total_time_s,
        f'{DISTANCE}_total': lap.distance_m,
        f'{SPEED}_max': lap.max_speed_ms,
        f'{SPEED}_avg': lap.avg_speed_ms,
        'calories': lap.calories,
        f'{HEARTRATE}_avg': lap.hr_avg,
        f'{HEARTRATE}_max': lap.hr_max,
        f'{CADENCE}_avg': lap.cadence_avg,
        f'{CADENCE}_max': lap.cadence_max,
        'intensity': lap.intensity,
        'trigger_method': lap.trigger_method,
      }
      for lap in reader.laps
    ])

    # Build a DataFrame using only trackpoints (as records).
    records = pd.DataFrame.from_records([
      {
        TIMESTAMP: tp.time,
        LAT: tp.lat,
        LON: tp.lon,
        DISTANCE: tp.distance_m,
        ELEVATION: tp.altitude_m,
        HEARTRATE: tp.hr,
        SPEED: tp.speed_ms,
        CADENCE: tp.cadence_rpm,
      }
      for tp in reader.trackpoints
    ])

    # TODO: Rethink how I want to use this lap column.
    # records['lap'] = [
    #   i for i, l in enumerate(reader.laps) for t in l.trackpoints
    # ]

    # Make the lap column into an additional index level.
    # TODO: Consider if 'time' or 'timestamp' might make a good
    # additional index. Or whether we need these as indexes at all.
    # records.index.name = 'record'
    # records = records.set_index('lap', append=True)

    activity = cls(records, laps, summary)

    # Convert cadence from RPM to strides per minute.
    activity.cadence._convert_units()

    return activity

  @classmethod
  def from_gpx(cls, file_obj):
    """Construct an Activity from a .gpx file.

    Args:
      file_obj: Any file-like object accepted by :class:`activereader.Gpx`
    Returns:
      Activity

    Examples:
      Provide a file path:

      >>> act = Activity.from_gpx('my_activity.gpx')

      Provide a raw string of bytes:
      
      >>> with open('my_activity.gpx', 'rb') as fb:
      ...   raw_data = fb.read()
      >>> act = Activity.fom_gpx(raw_data)

      Provide a string (no encoding info):
      
      >>> with open('my_activity.gpx', 'r') as f:
      ...   xml_string = f.read()
      >>> act = Activity.fom_gpx(xml_string)
    """
    activereader = import_optional_dependency('activereader')

    reader = activereader.Gpx.from_file(file_obj)
    
    summary = pd.Series({
      f'{TIMESTAMP}_start': reader.start_time,
    })

    activities = pd.DataFrame.from_records([
      {
        'title': trk.name,
        'sport': trk.activity_type
      } for trk in reader.tracks
    ])

    if len(activities) > 1:
      raise ValueError('multi-activity files not supported')

    summary = pd.concat([summary, activities.iloc[0]])

    records = pd.DataFrame.from_records([
      {
        TIMESTAMP: tp.time,
        LAT: tp.lat,
        LON: tp.lon,
        ELEVATION: tp.altitude_m,
        CADENCE: tp.cadence_rpm,
        HEARTRATE: tp.hr,
      } for tp in reader.trackpoints
    ])
    
    # TODO: Figure out how laps are represented in gpx files, if at all.

    activity = cls(records, summary=summary)

    # Convert cadence from RPM to strides per minute.
    activity.cadence._convert_units()

    return activity

  @classmethod
  def from_csv(cls, filepath_or_buffer):
    """Construct an Activity from a .csv file.

    The CSV file should represent a record DataFrame. Currently the
    summary and laps data structures are not included.

    TODO:
      * Right now this is just completely mangled so the tests pass with
        what they're given. Need to clean up.

    Args:
      filepath_or_buffer (str, path object or file-like object): Any
        acceptable input to :func:`pandas.read_csv`.
    Returns:
      Activity
    
    """ 
    records = pd.read_csv(filepath_or_buffer)

    return cls(records)

    # ------------------------------------------------------------------
    # Old implementation kept for future use:

    # # Read the data from the csv file, assuming the third column of the
    # # file represents timestamp and parsing it as a datetime.
    # records = pd.read_csv(
    #   filepath,
    #   index_col=[0, 1],
    #   header=[0, 1], 
    #   parse_dates=[2]
    # )

    # # Convert the index's 'offset' level to TimedeltaIndex.
    # records.index = records.index.set_levels(
    #     pd.TimedeltaIndex(data.index.get_level_values('offset')),
    #     level='offset')

    # # Fix column level values, an artifact of blank level values in a
    # # .csv file.
    # fields = data.columns.get_level_values('field')

    # #srcs = data.columns.get_level_values('source').str.replace('Un.*', 'device')
    # srcs = data.columns.get_level_values('elev_source').str.replace('Un.*', 'device')
   
    # col_tups = [(field, src) for field, src in zip(fields, srcs)]
    # data.columns = pandas.MultiIndex.from_tuples(col_tups,
    #                                              names=['field', 'source'])
    # data['time', 'device'] =  \
    #     (data['timestamp', 'device']  \
    #      - data['timestamp', 'device'].iloc[0]).dt.total_seconds()

    # ------------------------------------------------------------------

  # --------------------------------------------------------------------
  @property
  def records(self):
    """pandas.DataFrame: The records (time series) of the Activity."""
    return self._records

  @records.setter
  def records(self, value):
    if not isinstance(value, pd.DataFrame):
      raise TypeError('`records` must be a pandas.Dataframe')
 
    self._records = value.copy()

  @property
  def laps(self):
    """pandas.DataFrame: The lap data of the Activity."""
    return self._laps

  @laps.setter
  def laps(self, value):
    if not isinstance(value, pd.DataFrame):
      raise TypeError('`laps` must be a pandas.Dataframe')
    
    self._laps = value.copy()

  @property
  def summary(self):
    """pandas.Series: The summary data of the Activity."""
    return self._summary

  @summary.setter
  def summary(self, value):
    if not isinstance(value, pd.Series):
      raise TypeError('`summary` must be a pandas.Series')

    self._summary = value.copy()

  @property
  def records_unique(self):
    """Unique rows in the records DataFrame.

    Sometimes, a data source will repeat a record at the end of one lap
    and the beginning of the next one. This property drops lap numbering
    from the records DataFrame and returns the unique records.

    Examples:

      >>> records = pd.DataFrame({
      ...   'timestamp': ['2021-04-16 13:38:54',
      ...                 '2021-04-16 13:38:56',
      ...                 '2021-04-16 13:38:56',
      ...                 '2021-04-16 13:39:01'],
      ...   'lat': [40.037947, 40.037947, 40.037947, 40.037919],
      ...   'lon': [-105.259236, -105.259276, -105.259276, -105.259354],
      ...   'distance': [0.0, 3.4, 3.4, 11.1],
      ...   'elevation': [1626.6, 1626.6, 1626.6, 1626.6],
      ...   'lap': [0, 0, 1, 1]
      ... })
      >>> act = Activity(records)
      >>> act.records
                  timestamp        lat         lon  distance  elevation  lap  time
      0 2021-04-16 13:38:54  40.037947 -105.259236       0.0     1626.6    0     0
      1 2021-04-16 13:38:56  40.037947 -105.259276       3.4     1626.6    0     2
      2 2021-04-16 13:38:56  40.037947 -105.259276       3.4     1626.6    1     2
      3 2021-04-16 13:39:01  40.037919 -105.259354      11.1     1626.6    1     7
      >>> act.records_unique
                  timestamp        lat         lon  distance  elevation  time
      0 2021-04-16 13:38:54  40.037947 -105.259236       0.0     1626.6     0
      1 2021-04-16 13:38:56  40.037947 -105.259276       3.4     1626.6     2
      2 2021-04-16 13:39:01  40.037919 -105.259354      11.1     1626.6     7
    """
    return self.records.drop(
      columns=['bout', 'lap'], errors='ignore'
    ).drop_duplicates(ignore_index=True)

  # --------------------------------------------------------------------
  # Convenience methods 

  def has_streams(self, *field_names):
    """Return whether all given streams exist in the records DataFrame.
    
    Args:
      *field_names (scalar): fields to check for in the record DataFrame
        column index.
    Returns:
      bool: Whether or not all field names are column labels in the record
      DataFrame.

    Examples:

      All requested column labels must be present:

      >>> act = Activity(pd.DataFrame({'a': [1, 2, 3], 'b': [0, 2, 4]}))
      >>> act.has_streams('a', 'b')
      True
      >>> act.has_streams('a', 'c')
      False
    """
    return all(field_name in self.records.columns for field_name in field_names)

  @property
  def has_position(self):
    """bool: Return whether the records DataFrame contains GPS coordinates.

      "lat" and "lon" streams must **both** be present.    
    """
    return self.has_streams(LAT, LON)

  @property
  def latlons(self):
    """list or None: GPS coordinate records as a list of [lat, lon] lists.
    
    If either "lat" or "lon" is missing from the records DataFrame, None is
    returned.
    """
    if not self.has_position:
      return None

    return list(self.records[[LAT, LON]])
  
  @property
  def lonlats(self):
    """list or None: GPS coordinates as a list of [lon, lat] lists.
        
    If either "lat" or "lon" is missing from the records DataFrame, None is
    returned.
    """
    if not self.has_position:
      return None

    return list(self.records[[LON, LAT]])

  # --------------------------------------------------------------------

  # ----------------------------------------------------------------------
  # Field Accessors
  # ----------------------------------------------------------------------
  elevation = CachedField(ELEVATION, ElevationField)
  distance = CachedField(DISTANCE, DistanceField)
  timestamp = CachedField(TIMESTAMP, TimestampField)
  time = CachedField(TIME, TimeField)
  lat = CachedField(LAT, LatField)
  lon = CachedField(LON, LonField)
  speed = CachedField(SPEED, SpeedField)
  grade = CachedField(GRADE, GradeField)
  heartrate = CachedField(HEARTRATE, HeartrateField)
  cadence = CachedField(CADENCE, CadenceField)

  # FUTURE:
  # power = CachedField('power', PowerField)
  # moving = CachedField('moving', MovingField)
  # plot = CachedAccessor('plot', pandas.plotting.PlotAccessor)
