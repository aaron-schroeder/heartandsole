"""
TODO:
  * Consider combining this file with TimestampField.
"""

from heartandsole.core.fields.base import ActivityField


class TimeField(ActivityField):
    
  _field_name = 'time'

  def records_from_timestamps(self, inplace=False):
    """Time records calculated from timestamp records.

    Args:
      inplace (bool): Whether to add the Series result as a column to the
        records DataFrame. Default False.

    Returns:
      pandas.Series or None: The Series result or None if ``inplace=True``
      or if the records DataFrame does contain a ``timestamp`` column.

    Examples:
  
      This method is automatically called with ``inplace=True`` upon
      creation of an Activity, provided the input records DataFrame
      has a timestamp column but no time column:

      >>> records = pd.DataFrame({
      ...   'timestamp': ['2021-04-16 13:38:54',
      ...                 '2021-04-16 13:38:56',
      ...                 '2021-04-16 13:38:56',
      ...                 '2021-04-16 13:39:01'],
      ... })
      >>> act = Activity(records)
      >>> act.records
                  timestamp  time
      0 2021-04-16 13:38:54     0
      1 2021-04-16 13:38:56     2
      2 2021-04-16 13:38:56     2
      3 2021-04-16 13:39:01     7

      When called with ``inplace=False``, this method returns a Series:

      >>> act.time.records_from_timestamps()
      0    0
      1    2
      2    2
      3    7
      Name: time, dtype: int64

    """
    timestamp_stream = self.activity.timestamp.stream

    if timestamp_stream is not None:

      time_init = timestamp_stream.iloc[0]

      time_stream = (timestamp_stream - time_init).dt.total_seconds().astype('int').rename(self.record_stream_label)

      if not inplace:
        return time_stream

      self.activity.records[self.record_stream_label] = time_stream

  def elapsed(self, source='records'):
    """Return elapsed time in seconds.

    Args:
      source (str): Source from which to obtain elapsed time.
      
        - ``records`` (default): last time record in the records DataFrame.
        - ``summary``: ``elapsed`` value in the summary Series.
        - ``laps``: sum of the laps DataFrame column ``elapsed``.
    
    Returns:
      int or None: Elapsed time according to the requested source.
      If the Activity does not possess the requested data source,
      return None.

    Raises:
      ValueError: If source is not a valid option.

    """
    if source == 'records':
      if self.activity.has_streams(self.record_stream_label):
        return self.stream.iloc[-1] - self.stream.iloc[0]
    elif source == 'summary':
      if 'elapsed' in self.summary.index:
        return self.summary['elapsed']
    elif source == 'laps':
      if 'elapsed' in self.laps.columns:
        return self.laps['elapsed'].sum()
    else:
      raise ValueError('source must be one of: {records, summary, laps}')

  def timer(self, source='summary'):
    """Return total time, in seconds, when the device was active.

    Args:
      source (str): Source from which to obtain timer time.
      
        - ``summary`` (default): ``timer`` value in the summary Series.
        - ``laps``: sum of the ``timer`` column in the laps DataFrame.
    
    Returns:
      int or None: Timer time according to the requested source.
      If the Activity does not possess the requested data source,
      return None.

    Raises:
      ValueError: If source is not a valid option.

    """
    # not sure how I'd want to implement this. Would have to involve bouts.
    # if source == 'records':
    #   if self.activity.has_streams(self.record_stream_label):
    #     return self.stream.iloc[-1] - self.stream.iloc[0]
    if source == 'summary':
      if 'timer' in self.summary.index:
        return self.summary['timer']
    elif source == 'laps':
      if 'timer' in self.laps.columns:
        return self.laps['timer'].sum()
    else:
      raise ValueError('source must be one of: {summary, laps}')