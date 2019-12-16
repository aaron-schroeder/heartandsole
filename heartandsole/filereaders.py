import datetime
import sys

from dateutil import parser
import fitparse
from lxml import etree, objectify
import numpy as np
import pandas

import heartandsole.util


FIELD_NAMES = ['timestamp', 'distance', 'speed', 'elevation',
               'lat', 'lon', 'heart_rate', 'cadence',
               'running_smoothness', 'stance_time', 'vertical_oscillation']


class BaseFileReader(object):
  """Base class for file readers."""
  def __init__(self, blocks, time_offsets, rows):
    """Instantiates a BaseFileReader.

    Args:
      blocks: A list of ints, length n_time, which defines a block index
              for the DataFrame. Each block represents a period of
              movement, as defined by the start/stop buttons on the
              device.
      time_offsets: A list of datetime.timedeltas, length n_time, which
                    defines a timedelta index for the DataFrame. Each 
                    index is the elapsed time since the start of the
                    activity.
      rows: A list of length n_time made up of equal-length lists 
            which define values of each field at each row's timestep.
    """
    # Check that lists of indices are formatted correctly.
    assert len(blocks) == len(time_offsets)

    #       Then, check that all blocks are ints, all time_offsets are
    #       timedeltas, all row elements are the correct type for the field 
    #       (or None).

    self._build_dataframe(blocks, time_offsets, rows)

    # Memoize for use in subclasses and methods. Must be initialized
    # by subclasses.
    # TODO: Evaluate if these are necessary.
    self.start_time = None
    self.end_time = None
    self.elapsed_time = None

  def _build_dataframe(self, blocks, time_offsets, rows):
    """Constructs a time series DataFrame of activity data.

    Args:
      blocks: A list of ints, length n_time, which defines a block index
              for the DataFrame. Each block represents a period of
              movement, as defined by the start/stop buttons on the
              device.
      time_offsets: A list of datetime.timedeltas, length n_time, which
                    defines a timedelta index for the DataFrame. Each 
                    index is the elapsed time since the start of the
                    activity.
      rows: A list of length n_time made up of equal-length lists 
            which define values of each field at each row's timestep.
    """
    # Build the DataFrame
    self.data = pandas.DataFrame(rows, columns=FIELD_NAMES,
                                 index=[blocks, time_offsets])
    self.data.index.names = ['block', 'offset']

    # Fields may not exist in all files (except timestamp),
    # so drop the columns if they're not present.
    for field in FIELD_NAMES:
      if self.data[self.data[field].notnull()].empty:
        self.data.drop(field, axis=1, inplace=True)

  @property
  def has_position(self):
    return 'lat' in self.data.columns and  \
           'lon' in self.data.columns

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
  def latlons(self):
    if not self.has_position:
      return None

    return self.data[['lat', 'lon']].values.tolist()

  @property
  def lonlats(self):
    if not self.has_position:
      return None

    return self.data[['lon', 'lat']].values.tolist()


class FitFileReader(BaseFileReader):
  """Represents an activity recorded as a .fit file.

  Construction of an Activity parses the .fit file and detects periods of
  inactivity, as such periods must be removed from the data for certain
  calculations.

  TODO: Fix this doc.
  """
  FIELD_NAME_DICT = {
      'timestamp': 'timestamp',
      'distance': 'distance',
      'speed': 'enhanced_speed',
      'elevation': 'enhanced_altitude',
      'lat': 'position_lat',
      'lon': 'position_long',
      'heart_rate': 'heart_rate',
      'cadence': 'cadence',
      'running_smoothness': 'running_smoothness',
      'stance_time': 'stance_time',
      'vertical_oscillation': 'vertical_oscillation',
  }

  EVENT_TYPE_START = 'start'
  EVENT_TYPE_STOP = 'stop'

  def __init__(self, file_obj):
    """Creates a FitFileReader from a .fit file.

    Args:
      file_obj: A file-like object representing a .fit file.
    """
    self.fitfile = fitparse.FitFile(file_obj)

    records = list(self.fitfile.get_messages('record'))

    # Get elapsed time before modifying the data
    self.start_time = records[0].get('timestamp').value
    self.end_time = records[-1].get('timestamp').value
    self.elapsed_time = self.end_time - self.start_time

    # This is unique to .fit files.
    # .tcx activities handle pauses by breaking the Lap up
    # into separate Tracks, and they handle new laps by
    # starting a new Lap within the Activity.
    self.events = self._df_from_messages(
        self.fitfile.get_messages('event'),
        ['event', 'event_type', 'event_group', 'timer_trigger', 'data'],
        timestamp_index=True)

    # MOVE DOCUMENTATION TO BASEREADER
    # The primary index of the DataFrame is the "block". A block is defined as
    # a period of movement. Blocks may be defined by start/stop event messages
    # from the .fit file, or they may be detected based on speed in the case
    # that the recording device did not automatically pause recording when
    # stopped.
    blocks = []
    curr_block = -1

    # The secondary index is the duration from the start of the activity
    time_offsets = []

    # Get start/stop events from .fit file.
    # TODO: Find out other event types, and consider working with them.
    #       eg lost connection to satellite.
    timer_events = self.events[self.events['event'] == 'timer']

    # TO ACTIVITY?
    # We will build a DataFrame with these fields as columns. Values for each
    # of these fields will be extracted from each record from the .fit file.
    fields = [val for val in self.FIELD_NAME_DICT.values() if val is not None]
    #fields = [self.FIELD_NAME_DICT[field_name] for field_name in self.field_names
    #          if self.FIELD_NAME_DICT[field_name] is not None]

    # Build the rows and indices of the DataFrame.
    event_index = 0
    rows = []
    for record in records:
      curr_timestamp = record.get('timestamp').value

      # Match data record timestamps with event timestamps in order to mark
      # "blocks" as described above. Periods of no movement will be excised
      # (if the recording device did not have autopause enabled there will be
      # blocks of no movement that should be removed before data analysis).
      if event_index < len(timer_events) and (
          curr_timestamp >= timer_events.iloc[event_index].name):

        # Events usually have timestamps that correspond to a data timestamp,
        # but this isn't always the case. Process events until the events catch
        # up with the data.
        while True:
          event_type = timer_events.iloc[event_index]['event_type']

          if event_type == self.EVENT_TYPE_START:
            curr_block += 1

          # This other case is irrelevant with no auto-detecting stops.
          # The logic checks, in the case that the manual event was
          # a stop event, if the stop event was triggered by the device's
          # auto-pause feature. This logic is now handled in Activity.
          # I'm leaving the code snippet temporarily if I get confused :)
          #elif event_type.startswith(self.EVENT_TYPE_STOP):
          #  # If the stop event was detected based on speed, excise the region
          #  # until the next start event, because we know that it's a region of
          #  # data with speed under the stopped threshold.
          #  if trigger == self.TIMER_TRIGGER_DETECTED:
          #    excise = True

          event_index += 1

          # Once the event timestamp is ahead of the data timestamp we can
          # continue processing data; the next event will be processed as the
          # data timestamps catch up with it.
          if event_index >= len(timer_events) or (
              curr_timestamp < timer_events.iloc[event_index].name):
            break

      # Build indices
      time_offsets.append(curr_timestamp - self.start_time)
      blocks.append(curr_block)

      row = []
      for field_name in fields:
        field = record.get(field_name)
        if field is not None:
          row.append(field.value if field.units != 'semicircles'
                                 or field.value is None
                                 else field.value * 180 / 2 ** 31)
        else:
          row.append(None)

      rows.append(row)

    super().__init__(blocks, time_offsets, rows)

  def _df_from_messages(self, messages, fields, timestamp_index=False):
    """Creates a DataFrame from an iterable of fitparse messages.

    Args:
      messages: Iterable of fitparse messages.
      fields: List of message fields to include in the DataFrame. Each one will
              be a separate column, and if a field isn't present in a particular
              message, its value will be set to None.
      timestamp_index: If True, message timestamps will be used as the index of
                       the DataFrame. Otherwise the default index is used.
                       Default is False.

    Returns:
      A DataFrame with one row per message and columns for each of
      the given fields.
    """
    rows = []
    timestamps = []
    for m in messages:
      timestamps.append(m.get('timestamp').value)

      row = []
      for field_name in fields:
        field = m.get(field_name)
        row.append(field.value if field is not None else None)

      rows.append(row)

    if timestamp_index:
      return pandas.DataFrame(rows, columns=fields, index=timestamps)
    else:
      return pandas.DataFrame(rows, columns=fields)


class TcxFileReader(BaseFileReader):
  """
  See https://stackoverflow.com/questions/53319313/iterate-xpath-elements-to-get-individual-elements-instead-of-list
  """

  FIELD_NAME_DICT = {
      'timestamp': 'Time',
      'distance': 'DistanceMeters',
      'speed': 'Extensions/TPX/Speed',
      'elevation': 'AltitudeMeters',
      'lat': 'Position/LatitudeDegrees',
      'lon': 'Position/LongitudeDegrees',
      'heart_rate': 'HeartRateBpm/Value',
      'cadence': 'Extensions/TPX/RunCadence',
      'running_smoothness': None,             # TBD 
      'stance_time': None,                    # TBD
      'vertical_oscillation': None,           # TBD
  }

  def __init__(self, file_path, namespace=None):
    # Verify that this is .tcx (it should be if it is passed here)
    # if file_path.lower().endswith('.tcx'):

    # Attach these fields to the instance in case the user wants 
    # to interact with the file data in some way.
    self.tree = etree.parse(file_path)
    self.root = self.tree.getroot()

    # Strip namespaces.
    for elem in self.root.getiterator():
      if not hasattr(elem.tag, 'find'): continue
      i = elem.tag.find('}')
      if i >= 0:
        elem.tag = elem.tag[i+1:]
    objectify.deannotate(self.root, cleanup_namespaces=True)

    trackpoints = self.tree.xpath('//Track/Trackpoint')

    # Not sure how I feel about this. Go with the file summary
    # timestamp, or the timestamp of the first trackpoint?
    # What if the first few trackpoints don't have a timestamp?
    # Is that possible?
    trackpoint_0 = trackpoints[0]

    # Read the start time from a string formatted as xsd:dateTime
    # into a timezone-aware datetime.
    # http://www.datypic.com/sc/xsd/t-xsd_dateTime.html
    # https://www8.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd
    # TODO: Check that this works correctly for timezone stuff.
    self.start_time = parser.isoparse(trackpoints[0].findtext('Time'))

    # Iterate through all the tracks in the activity. tcx activities
    # are made up of laps, which are created when the 'lap' button is 
    # pressed on the device. Within a lap is a single track, with
    # another track added each time a pair of (stop, start) buttons
    # is pressed on the device.
    #
    # For now, I will group by laps in addition to pauses. There should
    # not be any harm in defining two blocks of movement with no actual
    # pause in between.
    # TODO: Ignore laps and group data into blocks separated by pauses.
    #       How to group multiple laps that are from the same activity
    #       period? 
    blocks = []
    curr_block = 0
    time_offsets = []
    rows = []
    for track in self.tree.xpath('//Track'):
      for tp in track:
        blocks.append(curr_block)
        curr_timestamp = parser.isoparse(tp.findtext('Time'))
        time_offsets.append(curr_timestamp - self.start_time)

        # Create a list with data for this dataframe row.
        # All available fields at this timestep.
        row = []
        for field_name in FIELD_NAMES:
          row.append(self.get_field_value(tp, field_name))
        rows.append(row)

      # Moving into a new track, assume a new block is needed.
      curr_block += 1

    super().__init__(blocks, time_offsets, rows)

  def get_field_value(self, trackpoint, field_name):
    """Processes data read in from file based on field."""
    tcx_field_name = self.FIELD_NAME_DICT.get(field_name)

    if tcx_field_name is None:
      return None

    value_str = trackpoint.findtext(tcx_field_name) 

    # floats
    if field_name in ['distance', 'speed', 'elevation', 'lat', 'lon',
                      'running_smoothness', 'stance_time',
                      'vertical_oscillation']:
      return float(value_str) if value_str is not None else None

    # ints
    if field_name in ['heart_rate', 'cadence']:
      return float(value_str) if value_str is not None else None

    # timestamp. Garmin has specified a format for .tcx datetimes
    # that does not easily lend itself to datetime.strptime.
    if field_name == 'timestamp':
      return parser.isoparse(value_str) if value_str is not None else None

    # Every field should be caught before this point.
    return value_str 
