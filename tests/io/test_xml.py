import unittest

from lxml import etree

from heartandsole.io.xml import DocParser, xml_to_df, purty_print
from tests.common import datapath


class TestXmlToDf(unittest.TestCase):
  # Maybe store a (user-extensible) list of column names to parse 
  # as dates, by file type.

  def assert_no_col_all_na(self, df_point):

    # print(df_point)
    # print(df_point.dtypes)

    for (col_label, field_series) in df_point.iteritems():
      self.assertFalse(
        field_series.isna().all(),
        f'Col `{col_label}` has only NA values.'
      )

  def test_gpx_trkpt(self):
    self.assert_no_col_all_na(
      xml_to_df(
        datapath('io', 'data', 'gpx', 'trk.gpx'),
        'trkpt', 
        flatten=True,
        parse_dates=['time'],
        # 'trk'
      )
    )

  def test_tcx_trackpoint(self):
    self.assert_no_col_all_na(
      xml_to_df(
        datapath('io', 'data', 'tcx', 'activity.tcx'), 
        'Trackpoint',
        flatten=True,
        parse_dates=['Time'],
      )
    )

  def test_tcx_lap(self):
    self.assert_no_col_all_na(
      xml_to_df(
        datapath('io', 'data', 'tcx', 'activity.tcx'), 
        'Lap', 
        parse_dates=['StartTime'],
        # TODO: make the function actually work this way
        flatten=['AverageHeartRateBpm', 'MaximumHeartRateBpm', 'Extensions']
      )
    )


class TestDocParser(unittest.TestCase):
  maxDiff = None

  def setUp(self):
    self.parser = DocParser(
      etree.parse(datapath('io', 'data', 'tcx', 'activity.tcx')).getroot(),
      default_prefix='ns1'
    )

  def test_generate_xslt(self):
    result = etree.tostring(self.parser.generate_xslt('Trackpoint'), encoding='unicode')
    expected = """<xsl:stylesheet 
      version="1.0"
      xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
      xmlns:ns1="http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2"
      xmlns:ns5="http://www.garmin.com/xmlschemas/ActivityGoals/v1"
      xmlns:ns3="http://www.garmin.com/xmlschemas/ActivityExtension/v2"
      xmlns:ns2="http://www.garmin.com/xmlschemas/UserProfile/v2"
      xmlns:ns4="http://www.garmin.com/xmlschemas/ProfileExtension/v1"
    >

      <xsl:output method="xml" omit-xml-declaration="no" indent="yes"/>

      <xsl:template match="node()|@*">
        <xsl:copy>
          <xsl:apply-templates select="node()|@*"/>
        </xsl:copy>
      </xsl:template>

      <xsl:template match="//ns1:Trackpoint/ns1:Position">
        <PositionLatitudeDegrees>
          <xsl:value-of select="./ns1:LatitudeDegrees"/>
        </PositionLatitudeDegrees>
        <PositionLongitudeDegrees>
          <xsl:value-of select="./ns1:LongitudeDegrees"/>
        </PositionLongitudeDegrees>
      </xsl:template>

      <xsl:template match="//ns1:Trackpoint/ns1:HeartRateBpm">
        <HeartRateBpmValue>
          <xsl:value-of select="./ns1:Value"/>
        </HeartRateBpmValue>
      </xsl:template>

      <xsl:template match="//ns1:Trackpoint/ns1:Extensions">
        <ExtensionsTPXSpeed>
          <xsl:value-of select="./ns3:TPX/ns3:Speed"/>
        </ExtensionsTPXSpeed>
        <ExtensionsTPXRunCadence>
          <xsl:value-of select="./ns3:TPX/ns3:RunCadence"/>
        </ExtensionsTPXRunCadence>
      </xsl:template>

    </xsl:stylesheet>"""

    self.assertEqual(
      expected.replace(' ', '').replace('\n', '').replace('>', '>\n'),
      result.replace(' ', '').replace('\n', '').replace('>', '>\n')
    )

  def test_generate_xslt_result(self):
    xsl_root = self.parser.generate_xslt('Trackpoint')
    transform = etree.XSLT(xsl_root)
    xslt_result = transform(self.parser.root)
    # purty_print(xslt_result)