"""Utility functions."""
import datetime


def time_from_timestring(timestring):
  """Convert TCX- or GPX-formatted time string into a datetime object.
  
  Naively strips any timezone info from the end of the string. An alternative
  would be to use :meth:`dateutil.parser.isoparse` to infer a tz-aware 
  datetime object.

  Based on XML schema,
  `xsd:dateTime <http://books.xmlschemata.org/relaxng/ch19-77049.html>`_.

  Args:
    timestring (str): A timestamp formatted according to ``xsd:dateTime``
  Returns:
    datetime.datetime: The timestamp as a datetime object.
  """
  return datetime.datetime.strptime(timestring[0:19],'%Y-%m-%dT%H:%M:%S')


def timestring_from_time(time):
  """Convert datetime into a TCX- or GPX-formatted timestamp.
  
  Naively assumes a timezone 6 hours behind UTC - corresponds to
  Mountain Daylight Time.

  Based on XML schema,
  `xsd:dateTime <http://books.xmlschemata.org/relaxng/ch19-77049.html>`_.

  Args:
    time (datetime.datetime): The time in MDT.
  Returns:
    str: Timestamp with MDT timezone info.
  """
  return time.strftime('%Y-%m-%dT%H:%M:%S.00-06:00')
