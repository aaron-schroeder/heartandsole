from heartandsole.core.fields.base import ActivityField


class CadenceField(ActivityField):
  
  _field_name = 'cadence'

  def _convert_units(self):
    """Convert the units of any data used by this accessor.
    
    Most activity files convert running cadence in cycling terms of 
    RPM (revolutions per minute). In running, cadence is typically dealt
    with in strides per minute (SPM).
  
    """

    if self.record_stream_label in self.activity.records.columns:
      self.activity.records[self.record_stream_label] *= 2
    
    for lap_col in self.lap_cols:
      self.activity.laps[lap_col] *= 2
    
    for summary_row in self.summary_rows:
      self.activity.summary[summary_row] *= 2
