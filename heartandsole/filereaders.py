import datetime
import sys

import fitparse
import numpy as np
import pandas

import heartandsole.util


# Set to True to add a column to the DataFrame indicating whether a row would
# have been removed if removal of stopped periods were enabled, but don't
# actually remove it.
DEBUG_EXCISE = False


class FitActivity(fitparse.FitFile):
  """Represents an activity recorded as a .fit file.

  Construction of an Activity parses the .fit file and detects periods of
  inactivity, as such periods must be removed from the data for certain
  calculations.
  """

  EVENT_TYPE_START = 'start'
  EVENT_TYPE_STOP = 'stop'

  TIMER_TRIGGER_DETECTED = 'detected'

  # Speeds less than or equal to this value (in m/s) are
  # considered to be stopped
  STOPPED_THRESHOLD = 0.3

  def __init__(self, file_obj, remove_stopped_periods=False):
    """Creates a FitActivity from a .fit file.

    Args:
      file_obj: A file-like object representing a .fit file.
      remove_stopped_periods: If True, regions of data with speed below
                              a threshold will be removed from the data.
                              Default is False.
    """
    super(FitActivity, self).__init__(file_obj)

    self._remove_stopped_periods = remove_stopped_periods or DEBUG_EXCISE

    records = list(self.get_messages('record'))

    # Get elapsed time before modifying the data
    self.start_time = records[0].get('timestamp').value
    self.end_time = records[-1].get('timestamp').value
    self.elapsed_time = self.end_time - self.start_time

    self.events = self._df_from_messages(
        self.get_messages('event'),
        ['event', 'event_type', 'event_group', 'timer_trigger', 'data'],
        timestamp_index=True)

    # We will build a DataFrame with these fields as columns. Values for each
    # of these fields will be extracted from each record from the .fit file.
    fields = ['timestamp', 'distance', 'enhanced_speed', 'enhanced_altitude',
              'position_lat', 'position_long', 'heart_rate', 'cadence',
              'running_smoothness', 'stance_time', 'vertical_oscillation']

    # The primary index of the DataFrame is the "block". A block is defined as
    # a period of movement. Blocks may be defined by start/stop event messages
    # from the .fit file, or they may be detected based on speed in the case
    # that the recording device did not automatically pause recording when
    # stopped.
    blocks = []
    curr_block = -1

    # The secondary index is the duration from the start of the activity
    time_offsets = []

    # Get start/stop events from .fit file and combine with the events detected
    # from speed data, keeping the event from the .fit file if timestamps are
    # identical
    timer_events = self.events[self.events['event'] == 'timer']

    if self._remove_stopped_periods:
      # Detect start/stop events based on stopped threshold speed. If the
      # recording device did not have autopause enabled then this is the only
      # way periods of no movement can be detected and removed.
      detected_events = self._detect_start_stop_events(records)
      timer_events = timer_events.combine_first(detected_events)

    # Build the rows and indices of the DataFrame
    excise = False
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
          trigger = timer_events.iloc[event_index]['timer_trigger']

          if event_type == self.EVENT_TYPE_START:
            curr_block += 1

            # If we've seen a start event we should not be excising data
            # TODO(mtraver) Do I care if the start event is detected or from
            # the .fit file? I don't think so.
            excise = False
          elif event_type.startswith(self.EVENT_TYPE_STOP):
            # If the stop event was detected based on speed, excise the region
            # until the next start event, because we know that it's a region of
            # data with speed under the stopped threshold.
            if trigger == self.TIMER_TRIGGER_DETECTED:
              excise = True

          event_index += 1

          # Once the event timestamp is ahead of the data timestamp we can
          # continue processing data; the next event will be processed as the
          # data timestamps catch up with it.
          if event_index >= len(timer_events) or (
              curr_timestamp < timer_events.iloc[event_index].name):
            break

      if not excise or DEBUG_EXCISE:
        # Build indices
        time_offsets.append(curr_timestamp - self.start_time)
        blocks.append(curr_block)

        row = []
        for field_name in fields:
          field = record.get(field_name)
          if field is not None:
            row.append(field.value if field.units != 'semicircles'
                                   or field.value is None
                  else field.value*180/2**31)
          else:
            row.append(None)

        if DEBUG_EXCISE:
          row.append(excise)

        rows.append(row)

    assert len(blocks) == len(time_offsets)

    if DEBUG_EXCISE:
      fields += ['excise']

    self.data = pandas.DataFrame(rows, columns=fields,
                                 index=[blocks, time_offsets])
    self.data.index.names = ['block', 'offset']

    # Fields may not exist in all .fit files (except timestamp),
    # so drop the columns if they're not present.
    for field in fields:
      if self.data[self.data[field].notnull()].empty:
        self.data.drop(field, axis=1, inplace=True)

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

  def _detect_start_stop_events(self, records):
    """Detects periods of inactivity by comparing speed to a threshold value.

    Args:
      records: Iterable of fitparse messages. They must contain a 'speed' field.

    Returns:
      A DataFrame indexed by timestamp with these columns:
        - 'event_type': value is one of {'start','stop'}
        - 'timer_trigger': always the string 'detected', so that these
          start/stop events can be distinguished from those present in the
          .fit file.

      Each row is one event, and its timestamp is guaranteed to be that of a
      record in the given iterable of messages.

      When the speed of a record drops below the threshold speed a 'stop' event
      is created with its timestamp, and when the speed rises above the
      threshold speed a 'start' event is created with its timestamp.
    """
    stopped = False
    timestamps = []
    events = []
    for i, record in enumerate(records):
      ts = record.get('timestamp').value

      if i == 0:
        timestamps.append(ts)
        events.append([self.EVENT_TYPE_START, self.TIMER_TRIGGER_DETECTED])
      elif record.get('enhanced_speed') is not None:
        speed = record.get('enhanced_speed').value
        if speed <= self.STOPPED_THRESHOLD:
          if not stopped:
            timestamps.append(ts)
            events.append([self.EVENT_TYPE_STOP, self.TIMER_TRIGGER_DETECTED])

          stopped = True
        else:
          if stopped:
            timestamps.append(ts)
            events.append([self.EVENT_TYPE_START, self.TIMER_TRIGGER_DETECTED])
            stopped = False

    return pandas.DataFrame(events, columns=['event_type', 'timer_trigger'],
                            index=timestamps)

  @property
  def has_position(self):
    return 'position_lat' in self.data.columns and  \
           'position_long' in self.data.columns

  @property
  def has_cadence(self):
    return 'cadence' in self.data.columns

  @property
  def has_heart_rate(self):
    return 'heart_rate' in self.data.columns

  @property
  def has_speed(self):
    return 'enhanced_speed' in self.data.columns

  @property
  def has_elevation(self):
    return 'enhanced_altitude' in self.data.columns

  @property
  def has_distance(self):
    return 'distance' in self.data.columns

  @property
  def lonlats(self):
    if not self.has_position:
      return None

    return self.data[['position_long', 'position_lat']]
