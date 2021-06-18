class ActivityField(object):
  _field_name = ''

  def __init__(self, activity):
    self.activity = activity
    
    # Convert dtypes if necessary. This method is only called when
    # the accessor is accessed.
    self._ensure_dtype()
    
    # TODO: 
    #   * Provide some check that the column exists in the record DF?
    #     Otherwise raise an error or something? Idk if this makes sense.
    #   * Provide some way to convert records on read-in?

  def _ensure_dtype(self):
    """To be implemented by subclasses if needed."""
    pass

  @property
  def record_stream_label(self):
    """Alias of ``_field_name`` (for now)"""
    return self._field_name

  @property
  def stream(self):
    """pandas.Series: The column of the record DataFrame for this field.

    Examples:
    
      >>> records = pd.DataFrame(data={'elevation': [1690.0, 1690.5, 1692.0]})
      >>> act = Activity(records)
      >>> act.elevation.stream
      0    1690.0
      1    1690.5
      2    1692.0
      Name: elevation, dtype: float64

    """
    if self.activity.has_streams(self.record_stream_label):
      return self.activity.records[self.record_stream_label]

  @property
  def lap_cols(self):
    # Find any columns that match the pattern "{_field_name}_*" or 
    # "*_{_field_name}".
    regex = fr'{self.record_stream_label}_.+|.+_{self.record_stream_label}'
    
    return self.activity.laps.columns[self.activity.laps.columns.str.contains(regex)]

  @property
  def laps(self):
    """pandas.DataFrame: A subset of the laps DataFrame for the field.

    Looks for any column labels matching the pattern: {field}_{xxx} or 
    {xxx}_{field}.

    Examples:
    
      >>> records = pd.DataFrame([])
      >>> laps = pd.DataFrame({'speed_max': [5.0, 5.5], 'speed_avg': [3.0, 2.9]})
      >>> act = Activity(records, laps=laps)
      >>> act.speed.laps
         max  avg
      0  5.0  3.0
      1  5.5  2.9
    """
    # Find any columns that match the pattern "{_field_name}_*" or 
    # "*_{_field_name}" and use the remainder of matching strings as 
    # column labels.
    regex = fr'{self.record_stream_label}_(.+)|(.+)_{self.record_stream_label}'
    lap_col_df = self.activity.laps.columns.str.extract(regex)
    lap_col_series = lap_col_df[0].combine_first(lap_col_df[1])
    lap_indexer = lap_col_series.notnull().to_list()

    lap_df = self.activity.laps.loc(axis=1)[lap_indexer]
    lap_df.columns = lap_col_series[lap_indexer].to_list()

    return lap_df

  @property
  def summary_rows(self):
    # Find any columns that match the pattern "{_field_name}_*" or 
    # "*_{_field_name}".
    regex = fr'{self.record_stream_label}_.+|.+_{self.record_stream_label}'
    
    return self.activity.summary.index[self.activity.summary.index.str.contains(regex)]

  @property
  def summary(self):
    """pandas.Series: A subset of the summary Series for the field.

    Looks for any row labels matching the pattern: {field}_{xxx} or 
    {xxx}_{field}.

    Examples:
    
      >>> records = pd.DataFrame([])
      >>> summary = pd.Series({'speed_max': 5.0, 'speed_avg': 3.0})
      >>> act = Activity(records, summary=summary)
      >>> act.speed.summary
      max    5.0
      avg    3.0
      dtype: float64
    """
    # Find any row labels that match the pattern "{_field_name}_*" or 
    # "*_{_field_name}" and use the remainder of matching strings as 
    # row labels.
    regex = fr'{self.record_stream_label}_(.+)|(.+)_{self.record_stream_label}'
    summary_row_df = self.activity.summary.index.str.extract(regex)
    summary_row_series = summary_row_df[0].combine_first(summary_row_df[1])
    summary_indexer = summary_row_series.notnull().to_list()

    summary_series = self.activity.summary[summary_indexer]
    summary_series.index = summary_row_series[summary_indexer].to_list()

    return summary_series
