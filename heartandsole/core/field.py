"""Ideas for how fields could be defined, registered, and used."""
import warnings


class CachedField(object):
  """Custom property-like object.
    
  A descriptor for caching field accessors.

  Based on pd.core.accessor.CachedAccessor

  Args:
    name (str): Namespace that will be accessed under, e.g. ``act.foo``.
    accessor (cls): Class with the extension methods.

  Notes:
    For accessor, The class's __init__ method assumes ``Activity``
    as the single argument ``data``.

  """
  def __init__(self, name, field):
    self._name = name
    self._field = field

  def __get__(self, obj, cls):
    if obj is None:
      # we're accessing the attribute of the class, i.e., Activity.elevation
      return self._field

    field_obj = self._field(obj)
    # Replace the property with the accessor object.
    # This is what enables caching - next call to "get" will return
    # the existing field_obj, rather than redo the read-in process.
    # Inspired by: https://www.pydanny.com/cached-property.html
    setattr(obj, self._name, field_obj)
    return field_obj


def register_field(name):
  """Register a custom accessor on Activity objects.
  
  Based on :func:`pandas.api.extensions.register_dataframe_accessor`.

  Args:
    name (str): Name under which the accessor should be registered. A warning
      is issued if this name conflicts with a preexisting attribute.
  Returns:
    callable: A class decorator.

  See also:

    :func:`pandas.api.extensions.register_dataframe_accessor`
      Register a custom accessor on DataFrame objects.

    `pandas.api.extensions._register_accessor() <https://github.com/pandas-dev/pandas/blob/v1.2.4/pandas/core/accessor.py#L189-L275>`_

  Notes:
    When accessed, your accessor will be initialized with the Activity object
    the user is interacting with. So the signature must be

    .. code-block:: python

      def __init__(self, activity_obj):  # noqa: E999
        ...

  Examples:

    In your library code::
    
      import heartandsole as hns

      @hns.api.extensions.register_field('running_smoothness')
      class SmoothnessAccessor:
          def __init__(self, activity_obj):
              self._obj = activity_obj

          @property
          def avg(self):
              # return the average of the records
              return self._obj.records['running_smoothness'].mean()

    Back in an interactive IPython session:
      
      .. code-block:: ipython

        In [1]: act = hns.Activity(pd.DataFrame({{'running_smoothness': np.linspace(0, 10)}})
        In [2]: act.running_smoothness.avg
        Out[2]: 5.0
  
  TODO:
    * Consider making this a classmethod of Activity.

  """
  from heartandsole import Activity

  def decorator(field):
    if hasattr(Activity, name):
      warnings.warn(
        f"registration of accessor {repr(field)} under name "
        f"{repr(name)} for type {repr(Activity)} is overriding a preexisting "
        f"attribute with the same name.",
        UserWarning,
        stacklevel=2,
      )
    setattr(Activity, name, CachedField(name, field))
    Activity._fields.add(name)
    return field

  return decorator
