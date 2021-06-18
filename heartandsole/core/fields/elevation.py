from heartandsole.core.fields.base import ActivityField
from heartandsole.compat._optional import import_optional_dependency


class ElevationField(ActivityField):

  _field_name = 'elevation'

  # def _convert_units(self, orig='feet'):
  #   # This is an example - no file reader actually gives us feet units.
  #   if orig == 'feet':
  #     self.activity.records['elevation'] = self.activity.records['elevation'] * 5280 / 1609.34
  #   else:
  #     return ValueError('Can only convert from feet to meters')

  def gain(self, source='records'):
    """Return total elevation gain in meters.

    Args:
      source (str): Source from which to obtain elevation gain.
      
        - ``records`` (default): result when the records DataFrame is
          passed to :meth:`pandas.DataFrame.xyz.z_gain_threshold`.
        - ``summary``: ``gain`` value in the summary Series.
        - ``laps``: sum of ``gain`` column in the laps DataFrame.
    
    Returns:
      float or None: Total elevation gain according to the requested source. 
      If the Activity does not possess the requested data source, return None.

    Raises:
      ValueError: If source is not a valid option.

    See also:
      :meth:`pandas.DataFrame.xyz.z_gain_threshold`
        A 5-meter threshold elevation gain algorithm. From the ``pandas-xyz``
        package.
    
    """
    if source == 'records':
      if self.stream is not None:
        import_optional_dependency('pandas_xyz')
        
        # Option 1:
        return self.activity.records.xyz.z_gain_threshold()  # 5-unit threshold

        # Option 2 (untested, might need work):
        # df_tmp = self.records.copy()
        # df_tmp['smooth'] = self.records.xyz.z_smooth_time()
        # # smooth_series = self.records.xyz.z_smooth_distance()
        # return df_tmp.xyz.z_gain_naive(elevation='smooth')

        # Option 3 (func does not exist in pandas-xyz):
        # series_smooth = self.records.xyz.z_smooth_time()
        # return series_smooth.xyz.z_gain_naive()

    elif source == 'summary':
      if 'gain' in self.summary.index:
        return self.summary['gain']
    elif source == 'laps':
      if 'gain' in self.laps.columns:
        return self.laps['gain'].sum()
    else:
      raise ValueError('source must be one of: {records, summary, laps}')

  def loss(self, source='records'):
    """Return total elevation loss in meters.

    Args:
      source (str): Source from which to obtain elevation loss.
      
        - ``records`` (default): result when the records DataFrame is
          passed `in reverse` to :meth:`pandas.DataFrame.xyz.z_gain_threshold`.
        - ``summary``: ``loss`` value in the summary Series.
        - ``laps``: sum of ``loss`` column in the laps DataFrame.
    
    Returns:
      float or None: Total elevation loss according to the requested source. 
      If the Activity does not possess the requested data source, return None.

    Raises:
      ValueError: If source is not a valid option.

    See also:
      :meth:`pandas.DataFrame.xyz.z_gain_threshold`
        A 5-meter threshold elevation gain algorithm. From the ``pandas-xyz``
        package.
    
    """
    if source == 'records':
      if self.stream is not None:
        import_optional_dependency('pandas_xyz')
        return self.activity.records[::-1].xyz.z_gain_threshold() 
    elif source == 'summary':
      if 'loss' in self.summary.index:
        return self.summary['loss']
    elif source == 'laps':
      if 'loss' in self.laps.columns:
        return self.laps['loss'].sum()
    else:
      raise ValueError('source must be one of: {records, summary, laps}')

  @property
  # def smooth(self, time_source=None, elev_source=None):
  def smooth(self, method='time'):
    raise NotImplementedError

