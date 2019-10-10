"""Functions related to calculating power from speed and grade."""

import datetime

import numpy as np
import pandas

import heartandsole.stressutils as su
import heartandsole.util


def air_friction_coefficient(Cd, mass, proj_area, density_air_local):
  """Calculates the coefficient in formula where cost of running = kv^2.

  Based on the aerodynamic drag equation: F_drag = 1/2 (Cd rho A) v^2.
  The air friction coefficient, k, is analagously in the aerodynamic
  cost of running equation: Caero = k v^2, where Caero is in J/kg/m.
  The units of k are m^-1.

  Args:
    Cd: Float representing drag coefficient (unitless). Est 1.4 from
        Hirata 2012.
    mass: Float representing runner's mass in kg.
    proj_area: Float representing runner's projected area in m^2.
               Est 0.65 from Pugh 1970.
    density_air_local: Air density at the location of running in kg/m^3.
                       1.125 at sea level, approx 1.0 in Boulder.

  Returns: 
    Air friction coefficient, k, in m^1.

  TODO: 
    - Implement formula for projected area as function of height
      and mass see where GoldenCheetah got this.
    - Play around and verify 0.1 is a valid estimate for k for me.
  """
  return (1/2) * Cd * density_air_local * proj_area / mass


def run_cost(speed, grade=None):
  """Calculates the metabolic cost of running.

  See the documentation for powerutils.run_power for information
  on the scientific basis for this calculation.

  Args:
    speed: Running speed in meters per second. 
           Either a float or a Series of floats.
    grade: Decimal grade, i.e. 45% = 0.45.
           Either a float or a Series of floats.

  Returns:
    Cost of running, in Joules/kg/m, as a float or
    a series of floats, depending on input type.
  """
  # Calculate cost of running (neglecting air resistance), 
  # per meter per kg, as a function of decimal grade.
  # From (Minetti, 2002). Valid for grades from -45% to 45%.
  is_number = isinstance(grade, float) or isinstance(grade, int)  \
              and not isinstance(grade, bool)
  if isinstance(grade, pandas.Series):
    grade = grade.clip(lower=-0.45, upper=0.45)
  elif is_number:
    grade = max(-0.45, min(grade, 0.45))
  else:
    grade = speed*0.0

  c_i = 155.4*grade**5 - 30.4*grade**4 - 43.3*grade**3  \
      + 46.3*grade**2 + 19.5*grade + 3.6

  # Calculate aerodynamic cost of running, per meter per kg,
  # as a function of speed. From (Pugh, 1971) & (Di Prampero, 1993).
  # eta_aero is the efficiency of conversion of metabolic energy
  # into mechanical energy when working against a headwind. 
  # k is the air friction coefficient, in J s^2 m^-3 kg^-1,
  # which makes inherent assumptions about the local air density
  # and the runner's projected area and mass.
  eta_aero = 0.5
  k = 0.01
  c_aero = k * eta_aero**-1 * speed**2

  return c_i + c_aero


def run_power(speeds, grades=None):
  """Calculates instantaneous running power.

  See (Skiba, 2006) cited in README for details on the 
  Gravity-Ordered Velocity Stress Score (GOVSS), which serves as the
  starting point for the running power model used here.

  There are a number of changes from the run power model described
  in the GOVSS model, mostly having to do with misunderstandings
  of the cited papers as they relate to longer distances.
  
  Change #1: Removed efficiency factor on the cost of running (Cr),
  because the factor has no physiological basis. The source of the 
  equation for the metabolic cost of running as a function of 
  terrain slope is (Minetti, 2002), cited in README. The cost of 
  running was calculated from measurements of O2 consumed, which 
  means metabolic energy consumption was the value being measured.
  The factor nv introduced in equation (7) reflects the increased
  efficiency of the human engine as running speed increases, likely
  because of elastic energy return from the stretching of the 
  muscles, tendons, and ligaments. It would be appropriate to apply
  this nv factor to a mechanical energy equation for the cost 
  of running, but not to a metabolic energy equation. All other terms
  in the running power equation describe metabolic energy consumption.

  Change #2: Removed the kinetic cost of running (Ckin) from Skiba's 
  equation (5). The origin of this term is (DiPrampero, 1993), 
  where it describes the cost of accelerating from a standstill to 
  the steady-state speed of a track race. Even in relatively short
  events, the 800m and the 5000m, the contribution of Ckin to the 
  total cost of running was 10% and 1%, respectively.
  For the longer and less intense runs that make up the bulk of the
  data this running power model will be applied to, Ckin's
  contribution to the total cost of running would be even less. 
  Finally, the GOVSS running power model incorrectly applies Ckin.
  The GOVSS model multiplies the cost of running (J/kg/m) by the
  instantaneous velocity to calculate instantaneous power. Ckin 
  is only incurred at the start of the run, as the runner accelerates
  to steady-state speed. It is therefore inappropriate to carry it 
  forward in power calculations once steady-state speed has been
  achieved. For these reasons, Ckin was neglected from the run power 
  model. The cost of changing speeds during the run is left for future
  work, as it is generally incorrect to assume a constant speed
  during a workout, especially a trail run. However, the relative
  contribution of Ckin is small enough to neglect for now.

  Change #3: Do not use moving averages to calculate cost of running.
  The basis for the length of these averages in (Skiba, 2006) is 
  unclear. In that paper, the stated rationale for calculating cost of 
  running (Cr) over 120-second moving averages is because 
  'the original model was validated to the 800M distance (time of
  slightly less than 2 minutes).' Skiba does not clarify
  which model is being referred to.
    - (Di Prampero, 1986) used a similar running power model to 
      successfully predict subjects' finishing times in a recent
      marathon or half marathon. Subjects' cost of running was
      determined on a treadmill by collecting their respired air
      at steady-state, in the 4th-6th minute of running.
    - (Di Prampero, 1993) used a similar running power model to 
      successfully predict race performances of athletes at 800m and
      5000m distances. This is likely the basis for Skiba's comment.
      To determine cost of running, respired air was collected from 
      the subjects after 4 minutes of steady-state running outdoors 
      on a track.
    - (Minetti, 2002), which provides the equations describing the 
      cost of walking and running, was based on measurements taken
      after 3-4 minutes of steady-state treadmill running or walking.
    - (Pugh, 1971), the study that provides the efficiency of running
      against a headwind, was based on measurements taken after
      5-7 minutes of steady-state treadmill running or walking.
  Considering these studies, there is no clear basis for applying a
  moving average to calculate subjects' instantaneous cost of running.
  For this running power calculation to be comparable to cycling power,
  instantaneous costs of running are required. A moving average is 
  later applied to calculate normalized power.

  Limitation: No sense of time. Each data point is calculated
  totally independently of other data points. Length of time
  between data points is not considered. This limitation will need
  to be overcome if a rolling average is desired in any part of this
  calculation.

  Args:
    distances: Array-like object of speeds at along a path, in m/s. 
    grades: Array-like object of decimal grades along the same path. 

  Returns:
    Instantaneous run power as a ndarray. Watts/kg.
  """
  speeds = pandas.Series(speeds).reset_index(drop=True)
  if grades is not None:
    grades = pandas.Series(grades).reset_index(drop=True)

  # Calculate instantaneous cost of running, per meter per kg, 
  # as a function of speed and decimal grade.
  c_rs = run_cost(speeds, grade=grades)

  # Instantaneous running power is simply cost of running 
  # per meter multiplied by speed in meters per second.
  power = c_rs * speeds

  return power.to_numpy().squeeze()


def flat_run_power(pace):
  """Converts flat-ground pace to running power.

  The running power model is used to convert the pace to
  an equivalent metabolic power.
  TODO(aschroeder): actually handle bad input.

  Args:
    pace: String for running pace in min/mile ('%M:%S'),
          or float for running pace in m/s.
  Returns:
    Power as a float.
  """
  is_num = isinstance(pace, float) or isinstance(pace, int)  \
           and not isinstance(pace, bool)
  if isinstance(pace, str):
    min_mile = datetime.datetime.strptime(pace, '%M:%S')
    speed = 1609.34/(min_mile.minute*60 + min_mile.second)
  elif is_num:
    speed = pace
  else:
    print("Pace must be a string, float, or integer.")
    return None

  return run_cost(speed) * speed


def flat_speed(power):
  """Converts power to flat-ground running speed.

  This function is simply an inversion of the speed-power function.

  Args:
    power: A float or array of floats representing running power,
           in Watts/kg.

  TODO: Find a pythonic way to invert the flat_run_power equation.
  """
  value = (25 * power ** 2 + 8640) ** 0.5 + 5 * power

  return (5 ** (1/3) * value ** (2/3) - 12 * 5 ** (2/3)) / (value ** (1/3))
