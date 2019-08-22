import datetime
import math
import numpy as np
import pandas
import googlemaps

from geopy.distance import great_circle as distance
import fitparse

import fitanalysis.util
import config

class Elevation(object):
  """Object to get elevations from lat-lon coordinates.

  Construction of an Elevation object reads in the latlon coords and
  calculates the cumulative distance from the start of the latlon
  sequence.
  """

  def __init__(self, latlon_list):
    """Creates an Elevation from a list of latlon coords.

    Args:
      latlon_list: An array-like object representing pairs of [lon, lat].
    """
    self.data = pandas.DataFrame(data=latlon_list,
                                 columns=['lon', 'lat'])

    self._clean_up_coordinates()

    # Build a new column for the DataFrame representing cumulative
    # distance to each point, with an initial zero value because 
    # no movement has occurred at first.
    distances_cum = [0.0]
    for i in range(1, len(self.data)):
      # Calculate cumulative distance up to this point by adding
      # the distance between the previous and current point 
      # to the cumulative distance to the previous point.
      row_prev = self.data.iloc[i-1]
      row_curr = self.data.iloc[i]
      distance_cum = distances_cum[i-1] +  \
          distance((row_prev['lat'], row_prev['lon']),
                   (row_curr['lat'], row_curr['lon'])).meters

      distances_cum.append(distance_cum)

    self.data['distance'] = distances_cum

  def _clean_up_coordinates(self):
    """Infers missing lat/lon coordinates in simple cases."""
    self.data.fillna(method='bfill', inplace=True)

  @property
  def distances(self):
    return self.data['distance']

  @property
  def google(self):
    """TODO (aschroeder): Doc."""
    if 'google' not in self.data.columns:
      gmaps = googlemaps.Client(key=config.gmaps_api_key)

      # Google maps elevation api allows 500 elevation values
      # per request. Break latlon coordinates into 500-piece chunks
      # and pass to the api, then assemble returned elevations into one
      # consolidated list, and add to dataframe as a new column.
      elevs = []
      for _, chunk in self.data.groupby(np.arange(len(self.data)) // 500):

        # Format coordinates for google maps api request
        locations = [(float(row['lat']), float(row['lon'])) 
            for _, row in chunk.iterrows()]

        elevs.extend([round(elevobj['elevation'], 1) 
            for elevobj in gmaps.elevation(locations)])
      self.data['google'] = elevs

    return self.data['google']

  @property
  def lidar(self):
    raise NotImplementedError

  @property
  def elev_gain_google(self):
    raise NotImplementedError

  @property
  def elev_gain_lidar(self):
    raise NotImplementedError
