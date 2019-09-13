import datetime
import math

import numpy as np
import pandas
from scipy.signal import savgol_filter
from scipy.interpolate import interp1d
import googlemaps
import matplotlib.pyplot as plt

from geopy.distance import great_circle as distance
import fitparse

import fitanalysis.util
import config


class Elevation(object):
  """Object to get elevations from lat-lon coordinates.

  Construction of an Elevation object reads in the latlon coords and
  calculates the cumulative distance to each point from the start 
  of the latlon sequence.
  """

  def __init__(self, latlon_list):
    """Creates an Elevation from a list of latlon coords.

    Args:
      latlon_list: An array-like object of [lon, lat] pairs.
    """
    if type(latlon_list) == pandas.DataFrame:
      latlon_list = latlon_list.values.squeeze()

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
    return self.data['distance'].to_numpy().squeeze()

  @property
  def google(self):
    """Queries google maps' elevation api at each point."""
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

    return self.data['google'].to_numpy().squeeze()

  @property
  def lidar(self):
    raise NotImplementedError

  @property
  def elev_gain_google(self):
    raise NotImplementedError

  @property
  def elev_gain_lidar(self):
    raise NotImplementedError

class Grade(object):
  """Object to perform operations related to path slope.

  Construction of a Grade object [blah blah]
  TODO(aschroeder) doc.
  """

  def __init__(self, distances, elevations):
    """Constructor for the Grade object.

    Args:
      distances: Array-like object of cumulative distances along a path. 
      elevations: Array-like object of elevations above sea level
                  corresponding to the same path.
    """
    if type(distances) == pandas.DataFrame:
      distances = distances.to_numpy().squeeze()

    if type(elevations) == pandas.DataFrame:
      elevations = elevations.to_numpy().squeeze()

    rows = [[dist, elev] for dist, elev in zip(distances, elevations)]
    self.data = pandas.DataFrame(data=rows,
                                 columns=['distance', 'elevation'])

  @property
  def distance(self):
    return self.data['distance']

  @property
  def elevation(self):
    return self.data['elevation']

  @property
  def elevation_smooth(self, window_length=3, polyorder=2):
    """Smooths noisy elevation data for use in grade calculations.

    Because of GPS and DEM inaccuracy, elevation data is not smooth.
    Calculations involving terrain slope (the derivative of elevation
    with respect to distance, d_elevation/d_x) will not yield reasonable
    values unless the data is smoothed. 

    This method's approach follows the overview outlined in the 
    NREL paper found in the Resources section and cited in README.
    The noisy elevation data is downsampled and passed through a dual
    filter, consisting of a Savitzy-Golay (SG) filter and a binomial
    filter. Parameters for the filters were not described in the paper,
    so they must be tuned to yield intended results when applied
    to the data.

    Args:
      window_length: An integer describing the length of the window used
                     in the SG filter. Must be positive odd integer.
      polyorder: An integer describing the order of the polynomial used
                 in the SG filter, must be less than window_length.
      TODO(aschroeder) n: An integer describing the complexity of 
                          the binomial filter, must be 1 or greater.

    TODO(aschroeder) Combine a binomial filter with existing SG filter
                     and test effects on algorithm performance.
    """
    if 'elevation_smooth' not in self.data.columns:
      # Subsample elevation data in evenly-spaced intervals, with each
      # point representing the median value.
      len_sample = 30.0  # meters
      n_sample = math.ceil(self.distance.iloc[-1] / len_sample)
      idx = pandas.cut(self.distance, n_sample)
      data_ds = self.elevation.groupby(idx).apply(np.median).to_frame()
      data_ds['distance'] = pandas.IntervalIndex(
          data_ds.index.get_level_values('distance')).mid

      # Pass downsampled data through a Savitzky-Golay filter (attenuating
      # high-frequency noise). 
      # Then throw out any points where the elevation difference resulting
      # from filtration, and backfill via interpolation.
      # TODO (aschroeder): Add a second, binomial filter.
      data_ds['sg'] = savgol_filter(
          data_ds['elevation'], window_length, polyorder)  
      elevation_diff = np.abs(data_ds['elevation'] 
                            - data_ds['sg'])
      data_ds['elevation'][elevation_diff > 5.0] = np.nan
      data_ds['interp'] = data_ds['elevation'].interpolate()

      # Pass backfilled elevation profile through the Savitzky-Golay
      # filter to eliminate noise from the distance derivative. 
      # Calculate elevations at the original distance values
      # via interpolation.
      # TODO (aschroeder): Add a second, binomial filter.
      data_ds['sg_final'] = savgol_filter(
          data_ds['interp'], window_length, polyorder)
      interp_function = interp1d(
          data_ds['distance'], data_ds['sg_final'], 
          fill_value='extrapolate', kind='slinear')
      self.data['elevation_smooth'] = interp_function(self.data['distance'])

    # Calculate grade before and after using the algorithm.
    grade = pandas.DataFrame(self.data['distance'])
    dx = self.data['distance'].diff()
    grade['raw'] = self.data['elevation'].diff() / dx 
    grade['filtered'] = self.data['elevation_smooth'].diff() / dx

    # Plot the downsampled elevation data atop the full data.
    # This is temporary while debugging.
    fig, axs = plt.subplots(1, 1)
    self.data.plot(kind='line', x='distance', y='elevation', style='k-',
        label='Raw Data', ax=axs)
    data_ds.plot(kind='line', x='distance', y='sg',
        style='m-', label='Smoothed (Round 1)', ax=axs)
    self.data.plot(kind='line', x='distance', y='elevation_smooth',
        style='r-', label='Smoothed (Round 2)', ax=axs)
    data_ds.plot(kind='line', x='distance', y='interp',
        style='mo', label='Interpolated', ax=axs)
    data_ds.plot(kind='line', x='distance', y='elevation',
        style='co', label='Uniformly Sampled', ax=axs)

    # Plot grade before and after filtration.
    _, axs_g = plt.subplots(2, 1)
    self.data.plot(kind='line', x='distance', y='elevation', style='k-',
        label='Raw Data', ax=axs_g[0])
    #data_ds.plot(kind='line', x='distance', y='sg_final', 
    self.data.plot(kind='line', x='distance', y='elevation_smooth',
        style='r-', label='Filtered Data', ax=axs_g[0])
    grade.plot(kind='line', x='distance', y='raw', style='k-',  
        label='Raw Data', ax=axs_g[1])
    grade.plot(kind='line', x='distance', y='filtered', style='r-',  
        label='Filtered Data', ax=axs_g[1])
    axs_g[1].set_ylim(-1.0, 1.0)

    plt.show()

    return self.data['elevation_smooth']

  @property
  def raw(self):
    """Calculates unsmoothed point-to-point grades."""
    if 'raw' not in self.data.columns:
      self.data['raw'] = self.elevation.diff() / self.distance.diff() 

    return self.data['raw'].to_numpy().squeeze()

  @property
  def smooth(self):
    """Calculates smoothed point-to-point grades."""
    if 'smooth' not in self.data.columns:
      self.data['smooth'] = self.elevation_smooth.diff() / self.distance.diff()

    return self.data['smooth'].to_numpy().squeeze()
