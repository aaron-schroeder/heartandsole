from heartandsole.core.fields.base import ActivityField
# from heartandsole.core.field import register_field


def semicircles_to_degrees(semicircles):
  return semicircles * 180 / 2 ** 31


class PositionField(ActivityField):

  def _convert_record_units(self, inplace=False):
    """Convert semicircle units (found in .fit) to lat/lon degrees."""

    series = semicircles_to_degrees(self.stream)
    
    if not inplace:
      return series

    self.activity.records[self.record_stream_label] = series

  # TODO: Add another _convert_units method, which runs this method
  # and converts the summary and lap cols too
  
  @property
  def center(self):
    """The midpoint of the coordinate stream's extents.

    Returns:
      float
    """
    return 0.5 * (self.stream.max() + self.stream.min())


class LatField(PositionField):
  _field_name = 'lat'


class LonField(PositionField):
  _field_name = 'lon'