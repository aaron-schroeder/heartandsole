from heartandsole.core.fields.base import ActivityField
from heartandsole.compat._optional import import_optional_dependency


class DistanceField(ActivityField):
  
  _field_name = 'distance'

  def total(self, source='records'):
    """Return total distance in meters.

    Args:
      source (str): Source from which to obtain total distance.
      
        - ``records`` (default): last cumulative distance value in the 
          records DataFrame.
        - ``summary``: ``total`` value in the summary Series.
        - ``laps``: sum of ``total`` column in the laps DataFrame.
        - ``position``: last cumulative distance value in the Series
          calculated by :meth:`Activity.distance.records_from_position`.
    
    Returns:
      float or None: Total distance according to the requested source. 
      If the Activity does not possess the requested data source, return None.

    Raises:
      ValueError: If source is not a valid option.

    See also:
      :meth:`Activity.distance.records_from_position`
        Calculate cumulative distance from GPS coordinates.
    
    """
    if source == 'records':
      if self.stream is not None:
        return self.stream.iloc[-1]
    elif source == 'summary':
      if 'total' in self.summary.index:
        return self.summary['total']
    elif source == 'laps':
      if 'total' in self.laps.columns:
        return self.laps['total'].sum()
    elif source == 'position':
      if self.activity.has_position:
        return self.records_from_position().iloc[-1]
    else:
      raise ValueError('Arg must be one of: "records", "summary", "laps", "position"')
    

  # @property
  def records_from_position(self, inplace=False):
    """Cumulative distance records calculated from GPS coordinate records.

    Args:
      inplace (bool): Whether to add the Series result as a column to the
        records DataFrame. Default False.

    Returns:
      pandas.Series or None: The Series result or None if ``inplace=True``
      or if the records DataFrame does not contain ``lat`` and ``lon`` columns.

    Examples:

      When called with ``inplace=False``, this method returns a Series:
 
      >>> records = pd.DataFrame({
      ...   'lat': [40.0, 40.0001, 40.0002],
      ...   'lon': [-105.2, -105.2, -105.2]
      ... })
      >>> act = Activity(records)
      >>> act.distance.records_from_position()
      0     0.000000
      1    11.119493
      2    22.238985
      dtype: float64

      When called with ``inplace=True``, this method updates the records
      DataFrame:

      >>> act.distance.records_from_position(inplace=True)
      >>> act.records
             lat     lon   distance
      0  40.0000  -105.2   0.000000
      1  40.0001  -105.2  11.119493
      2  40.0002  -105.2  22.238985

    See also:

      :meth:`pandas.DataFrame.xyz.s_from_xy`
        Custom DataFrame accessor method for calculating cumulative distance
        from GPS coordinates. From the ``pandas-xyz`` package.

    """

    if self.activity.has_position:

      # Option 1 (untested, might need work):
      # pxyz = import_optional_dependency('pandas_xyz')
      # return pxyz.algorithms.s_from_xy(
      #   self.activity.lat.stream,
      #   self.activity.lon.stream
      # )

      # Option 2:
      import_optional_dependency('pandas_xyz')

      # If no kwargs, assumes stream names are 'lat' and 'lon'
      distance_stream = self.activity.records.xyz.s_from_xy(
        lat=self.activity.lat.record_stream_label,  # or ._field_name
        lon=self.activity.lon.record_stream_label,
      )

      if not inplace:
        return distance_stream

      self.activity.records[self.record_stream_label] = distance_stream