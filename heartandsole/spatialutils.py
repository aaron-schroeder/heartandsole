import datetime
import math
import warnings

import numpy as np
import pandas
from scipy.signal import savgol_filter
from scipy.interpolate import interp1d
import googlemaps
import matplotlib.pyplot as plt

from geopy.distance import great_circle as distance

import heartandsole.util
import config


class Elevation(object):
  """Class to get elevations from lat-lon coordinates.

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
  def distance(self):
    return np.array(self.data['distance']).squeeze()

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

    return np.array(self.data['google']).squeeze()

  @property
  def lidar(self):
    raise NotImplementedError


def elevation_gain(distances, elevations):
  raise NotImplementedError

def elevation_smooth(distances, elevations, window_length=3, polyorder=2):
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
    distances: Array-like object of cumulative distances along a path. 
    elevations: Array-like object of elevations above sea level
                  corresponding to the same path.
    window_length: An integer describing the length of the window used
                   in the SG filter. Must be positive odd integer.
    polyorder: An integer describing the order of the polynomial used
               in the SG filter, must be less than window_length.
    TODO(aschroeder) n: An integer describing the complexity of 
                        the binomial filter, must be 1 or greater.

  TODO(aschroeder) Combine a binomial filter with existing SG filter
                   and test effects on algorithm performance.
  """
  distances = pandas.Series(distances, name='distance')
  elevations = pandas.Series(elevations, name='elevation')

  # Subsample elevation data in evenly-spaced intervals, with each
  # point representing the median elevation value. If data is spaced
  # further than the subsampling interval, suppress warnings about 
  # taking the mean of empty slices and just interpolate between points.
  len_sample = 30.0  # meters
  n_sample = math.ceil(distances.iloc[-1] / len_sample)
  idx = pandas.cut(distances, n_sample)
  with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=RuntimeWarning)
    data_ds = elevations.groupby(idx).apply(np.median).interpolate(
        limit_direction='both').to_frame()
  data_ds['distance'] = pandas.IntervalIndex(
      data_ds.index.get_level_values('distance')).mid

  # Pass downsampled data through a Savitzky-Golay filter (attenuating
  # high-frequency noise). 
  # Then throw out any points where the elevation difference resulting
  # from filtration exceeds a threshold, and backfill via interpolation.
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
      fill_value='extrapolate', kind='linear')
      #fill_value='extrapolate', kind='quadratic')
  smooth = interp_function(distances)

  ## Calculate grade before and after using the algorithm.
  #grade = pandas.DataFrame(distances)
  #dx = distances.diff()
  #grade['raw'] = elevations.diff() / dx 
  #grade['filtered'] = pandas.Series(smooth).diff() / dx

  ## Plot the downsampled elevation data atop the full data.
  ## This is temporary while debugging.
  #fig, axs = plt.subplots(1, 1)
  #axs.plot(distances, elevations, 'k-', label='Raw Data')
  #data_ds.plot(kind='line', x='distance', y='sg',
  #    style='m-', label='Smoothed (Round 1)', ax=axs)
  #axs.plot(distances, smooth, 'r-', label='Smoothed (Round 2)')
  #data_ds.plot(kind='line', x='distance', y='interp',
  #    style='mo', label='Interpolated', ax=axs)
  #data_ds.plot(kind='line', x='distance', y='elevation',
  #    style='co', label='Uniformly Sampled', ax=axs)
  #axs.legend()

  ## Plot grade before and after filtration.
  #_, axs_g = plt.subplots(2, 1)
  #axs_g[0].plot(distances, elevations, 'k-', label='Raw Data')
  ##data_ds.plot(kind='line', x='distance', y='sg_final', 
  #axs_g[0].plot(distances, smooth, 'r-', label='Filtered Data')
  #grade.plot(kind='line', x='distance', y='raw', style='k-',  
  #    label='Raw Data', ax=axs_g[1])
  #grade.plot(kind='line', x='distance', y='filtered', style='r-',  
  #    label='Filtered Data', ax=axs_g[1])
  #axs_g[1].set_ylim(-1.0, 1.0)

  #plt.show()

  return smooth

def grade_smooth(distances, elevations):
  """Calculates smoothed point-to-point grades.

  TODO(aschroeder): check if distances and elevations are same length.
  Args:
    distances: Array-like object of cumulative distances along a path. 
    elevations: Array-like object of elevations above sea level
                corresponding to the same path.
  """
  distances = pandas.Series(distances).reset_index(drop=True)
  elevations = pandas.Series(elevations).reset_index(drop=True)
  elevations_smooth = pandas.Series(elevation_smooth(distances, elevations))
 
  return np.array(elevations_smooth.diff() / distances.diff())

def grade_raw(distances, elevations):
  """Calculates unsmoothed point-to-point grades.

  TODO(aschroeder): check if distances and elevations are same length.
  Args:
    distances: Array-like object of cumulative distances along a path. 
    elevations: Array-like object of elevations above sea level
                corresponding to the same path.
  """
  distances = pandas.Series(distances).reset_index(drop=True)
  elevations = pandas.Series(elevations).reset_index(drop=True)

  return np.array(elevations.diff() / distances.diff())
