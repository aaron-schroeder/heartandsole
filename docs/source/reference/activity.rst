.. _api.activity:

========
Activity
========
.. currentmodule:: heartandsole

Constructor
-----------
.. autosummary::
   :toctree: api/

   Activity

Attributes and underlying data
------------------------------
.. autosummary::
   :toctree: api/

   Activity.records
   Activity.laps
   Activity.summary
   Activity.records_unique
   Activity.has_position
   Activity.latlons
   Activity.lonlats
   
Methods
-------
.. autosummary::
   :toctree: api/

   Activity.has_streams

IO / conversion
---------------
.. autosummary::
   :toctree: api/

   Activity.from_fit
   Activity.from_tcx
   Activity.from_gpx
   Activity.from_csv
..   Activity.to_csv

Field accessors
---------------

heartandsole provides field-specific methods under various accessors.
These are separate namespaces within :class:`Activity` that only apply
to specific data types. Each accessor works with Activity data that bears
its name:

  - In the ``records`` DataFrame, column labels must exactly match the 
    corresponding accessor name.
  - In the ``laps`` DataFrame, column labels should be of the form
    `<accessor_name>_<stat_name>` or `<stat_name>_<accessor_name>`.
  - In the ``summary`` Series, row labels should be of the form
    `<accessor_name>_<stat_name>` or `<stat_name>_<accessor_name>`.

=========================== =========================================
Data Type                   Accessor
=========================== =========================================
Datetime                    :ref:`timestamp <api.activity.timestamp>`
Time in Seconds             :ref:`time <api.activity.time>`
GPS Coordinates             :ref:`position <api.activity.position>`
Distance                    :ref:`distance <api.activity.distance>`
Speed                       :ref:`speed <api.activity.speed>`
Elevation                   :ref:`elevation <api.activity.elevation>`
Decimal Grade               :ref:`grade <api.activity.grade>`
Heart Rate                  :ref:`heartrate <api.activity.heartrate>`
Step Cadence                :ref:`cadence <api.activity.cadence>`
=========================== =========================================

Common field accessor methods/properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All field accessors have the following properties at ``Activity.<field>.<property>``

.. autosummary::
   :toctree: api/

   ~core.fields.base.ActivityField.stream
   ~core.fields.base.ActivityField.laps
   ~core.fields.base.ActivityField.summary

.. _api.activity.timestamp:

Timestamp field accessor
~~~~~~~~~~~~~~~~~~~~~~~~

Datetime-specific methods and attributes are provided under the
``Activity.timestamp`` accessor.

.. autosummary::
   :toctree: api/
   :template: autosummary/accessor_method.rst

   Activity.timestamp.start
   Activity.timestamp.end
   Activity.timestamp.elapsed
   Activity.timestamp.ensure_aware

.. _api.activity.time:

Time field accessor
~~~~~~~~~~~~~~~~~~~

Integer time-specific methods and attributes are provided under the
``Activity.time`` accessor.

.. autosummary::
   :toctree: api/
   :template: autosummary/accessor_method.rst

   Activity.time.records_from_timestamps
   Activity.time.elapsed
   Activity.time.timer

.. _api.activity.position:

GPS coordinate field accessors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

GPS coordinate-specific methods and attributes are provided under the
``Activity.lat`` and ``Activity.lon`` accessors.

.. autosummary::
   :toctree: api/
   :template: autosummary/accessor_attribute.rst

   Activity.lat.center
   Activity.lon.center

.. _api.activity.distance:

Distance field accessor
~~~~~~~~~~~~~~~~~~~~~~~

Cumulative distance-specific methods and attributes are provided under the
``Activity.distance`` accessor.

.. autosummary::
   :toctree: api/
   :template: autosummary/accessor_method.rst

   Activity.distance.total
   Activity.distance.records_from_position

.. _api.activity.speed:

Speed field accessor
~~~~~~~~~~~~~~~~~~~~

Speed-specific methods and attributes are provided under the
``Activity.speed`` accessor.

.. autosummary::
   :toctree: api/
   :template: autosummary/accessor_attribute.rst


.. _api.activity.elevation:

Elevation field accessor
~~~~~~~~~~~~~~~~~~~~~~~~

Elevation-specific methods and attributes are provided under the
``Activity.elevation`` accessor.

.. autosummary::
   :toctree: api/
   :template: autosummary/accessor_method.rst

   Activity.elevation.gain
   Activity.elevation.loss

.. _api.activity.grade:

Grade field accessor
~~~~~~~~~~~~~~~~~~~~

Decimal grade-specific methods and attributes are provided under the
``Activity.grade`` accessor.

.. autosummary::
   :toctree: api/
   :template: autosummary/accessor_attribute.rst


.. _api.activity.heartrate:

Heart rate field accessor
~~~~~~~~~~~~~~~~~~~~~~~~~

Heart rate-specific methods and attributes are provided under the
``Activity.heartrate`` accessor.

.. autosummary::
   :toctree: api/
   :template: autosummary/accessor_attribute.rst


.. _api.activity.cadence:

Cadence field accessor
~~~~~~~~~~~~~~~~~~~~~~

Cadence-specific methods and attributes are provided under the
``Activity.cadence`` accessor.

.. autosummary::
   :toctree: api/
   :template: autosummary/accessor_attribute.rst