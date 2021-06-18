import pandas as pd

from heartandsole.core.fields.base import ActivityField


def _ensure_aware(series, tz_local):
  """Convert naive datetimes to timezone-aware, or return them as-is.
  
  Args:
    tz_local (str, pytz.timezone, dateutil.tz.tzfile): 
      Time zone for time which timestamps will be converted to.
      If the series already has local timezone info, it is returned as-is.
  
  """
  if pd.api.types.is_datetime64tz_dtype(series):
    return series

  return series.dt.tz_localize(tz=tz_local)


class TimestampField(ActivityField):
    
  _field_name = 'timestamp'

  def _ensure_dtype(self):
    """Convert record DataFrame column from str to datetime.

    Reads the ``timestamp`` records column using :meth:`pandas.to_datetime`
    and replaces the values in-place.

    If the column's data type is already datetime, it is unaffected.

    Returns:
      None

    TODO:
      * Implement a test in ``test_fields.py``

    """
    if self.stream is not None:
      stream_dt = pd.to_datetime(self.stream)
      self.activity.records[self.record_stream_label] = stream_dt

  def elapsed(self, source='records'):
    """Return elapsed time as a timedelta.

    Args:
      source (str): Source from which to obtain elapsed time.
      
        - ``records`` (default): difference between first and last timestamps
          in the records DataFrame.
        - ``summary``: difference between ``start`` and ``end`` timestamps in
          the summary Series.
        - ``laps``: sum of the differences between each lap's ``start`` and 
          ``end`` timestamps in the laps DataFrame.
    
    Returns:
      pandas.Timedelta or None: Elapsed time according to the requested source.
      If the Activity does not possess the requested data source,
      return None.

    Raises:
      ValueError: If source is not a valid option.

    """

    if source == 'records':
      if self.activity.has_streams(self.record_stream_label):
        return self.end(source='records') - self.start(source='records')
    elif source == 'summary':
      if 'end' in self.summary.index and 'start' in self.summary.index:
        return self.summary['end'] - self.summary['start']
    elif source == 'laps':
      if 'end' in self.laps.columns and 'start' in self.laps.columns:
        return (self.laps['end'] - self.laps['start']).sum()
    else:
      raise ValueError('source must be one of: {records, summary, laps}')

  def start(self, source='records'):
    """Return start time as a datetime.

    Args:
      source (str): Source from which to obtain start time.
      
        - ``records`` (default): first timestamp in the records DataFrame.
        - ``summary``: first ``start`` timestamp in the summary Series.
        - ``laps``: first ``start`` timestamp in the laps DataFrame.
    
    Returns:
      pandas.Timestamp, datetime.datetime, or None: Start time according to the
      requested source. If the Activity does not possess the requested data 
      source, return None.

    Raises:
      ValueError: If source is not a valid option.
    
    """
    if source == 'records':
      if self.activity.has_streams(self.record_stream_label):
        return self.stream.iloc[0]
    elif source == 'summary':
      if 'start' in self.summary.index:
        return self.summary['start']
    elif source == 'laps':
      if 'start' in self.laps.columns:
        return self.laps['start'].iloc[0]
    else:
      raise ValueError('source must be one of: {records, summary, laps}')

  def end(self, source='records'):
    """Return end time as a datetime.

    Args:
      source (str): Source from which to obtain end time.
      
        - ``records`` (default): last timestamp in the records DataFrame.
        - ``summary``: last ``end`` timestamp in the summary Series.
        - ``laps``: last ``end`` timestamp in the laps DataFrame.
    
    Returns:
      pandas.Timestamp, datetime.datetime, or None: End time according to the
      requested source. If the Activity does not possess the requested data 
      source, return None.

    Raises:
      ValueError: If source is not a valid option.
    
    """
    if source == 'records':
      if self.activity.has_streams(self.record_stream_label):
        return self.stream.iloc[-1]
    elif source == 'summary':
      if 'end' in self.summary.index:
        return self.summary['end']
    elif source == 'laps':
      if 'end' in self.laps.columns:
        return self.laps['end'].iloc[-1]
    else:
      raise ValueError('source must be one of: {records, summary, laps}')

  def ensure_aware(self, tz_local='UTC'):
    """Ensure all recognized timestamp data is timezone-aware.
    
    This alters (in-place) the Activity's ``records``, ``laps``, and
    ``summary`` entries that are recognized by this field accessor.

    There's nothing wrong with having timezone-naive timestamps and 
    assuming the dates are in a particular timezone. However, if the local
    date matters (eg evening activities recorded in the US will show up 
    with the next day's UTC timestamp), timestamps must be made 
    timezone-aware.

    Args:
      tz_local (str, pytz.timezone, dateutil.tz.tzfile): 
        Time zone for time which timestamps will be converted to.
        Default 'UTC'.

    Returns:
      None
  
    """

    if self.stream is not None:
      self.activity.records[self.record_stream_label] = _ensure_aware(
        self.stream,
        tz_local
      )

    for lap_col in self.lap_cols:
      self.activity.laps[lap_col] = _ensure_aware(
        self.activity.laps[lap_col],
        tz_local
      )
    
    # Ensure all Timestamps in summary Series are tz-aware.
    for summary_row in self.summary_rows:
      timestamp = self.activity.summary[summary_row]

      if not isinstance(timestamp, pd.Timestamp):
        self.activity.summary[summary_row] = pd.Timestamp(
          self.activity.summary[summary_row],
          tz=tz_local
        )
      elif timestamp.tz is None:
        self.activity.summary[summary_row] = self.activity.summary[
          summary_row].tz_localize(tz_local)