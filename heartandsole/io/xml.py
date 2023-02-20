import datetime
import re
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import warnings

from lxml import etree
from lxml.builder import ElementMaker

import pandas as pd


XSD_TYPES = {
  'xsd:dateTime': datetime.datetime,
  'xsd:double': float,
  'xsd:unsignedByte': int,
  'xsd:token': str,
}


def xml_to_df(file_location, row_tag=None, parse_dates=[], flatten=False):
  """
  Flatten options:
    - False or None: do not flatten any elements in the row using XSLT.
    - True: flatten all possible elements in the row using XSLT.
    - fields: dict of element tags to try to expand/flatten.
  """
  doc_parser = DocParser(etree.parse(file_location).getroot())

  return pd.read_xml(
    etree.tostring(doc_parser.root),
    xpath=f'//{doc_parser.get_tag_prefixed(row_tag)}',
    namespaces=doc_parser.nsmap_default,
    stylesheet=etree.tostring(
      doc_parser.generate_xslt(row_tag, flatten)
    ) if flatten else None,
    parse_dates=parse_dates
  )


def purty_print(node):
  out = etree.tostring(
    node,
    encoding='unicode',
    pretty_print=True
  )
  print(out)
  return out


class NamespaceParser:
  def __init__(self, root, default_prefix='default'):
    self.root = root
    self._prefix_default = default_prefix

  def get_ns_prefix(self, namespace, default=False):
    nsmap = self.nsmap_default if default else self.root.nsmap
    for prefix, uri in nsmap.items():
      if namespace == uri:
        return prefix
    raise KeyError(f'{namespace} not found in nsmap')

  def get_tag_prefixed(self, tag):
    smart_tag = etree.QName(tag)
    if smart_tag.namespace is None:
      prefix = self._prefix_default
    else:
      prefix = self.get_ns_prefix(smart_tag.namespace, default=True)
    return f'{prefix}:{smart_tag.localname}'

  @property
  def nsmap_default(self):
    nsmap = self.root.nsmap.copy()
    ns_default = nsmap.pop(None)
    if ns_default is not None:
      nsmap[self._prefix_default] = ns_default
    return nsmap

  def xpath(self, *args, **kwargs):
    if 'namespaces' in kwargs:
      warnings.warn(
        'The kwarg "namespaces" will be ignored. '
        'Unlike etree\'s Element.xpath, NamespaceParser\'s version '
        'assumes a default value for the "namespaces" kwarg.'
      )
    kwargs['namespaces'] = self.nsmap_default

    return self.root.xpath(*args, **kwargs)

  def get(self, *args, **kwargs):
    return self.root.get(*args, **kwargs)

  def find(self, path, namespaces=None):
    """
    The following also works, but would be unnecessarily difficult
    to wield because it would require sophisticated string building
    based on path expression rules:
    ```
    self.root.find(f'.//{{{self.nsmap_default["xs"]}}}documentation')
    ```
    """
    self.root.find(path, namespaces=self.nsmap_default)

  def iter(self, tag=None, *tags):
    def _process_tag(t):
      if tag is None:
        return

      re_prefix = '[a-z]+'
      # "Element names can contain letters, digits, hyphens, underscores,
      # and periods"
      re_tag = '[a-z0-9_.-]+'
      prefix_match = re.match(f'^({re_prefix}):({re_tag})$', t)
      if prefix_match:
        # Convert the namespace from prefix to uri.
        return f'{{{prefix_match.group(1)}}}{prefix_match.group(2)}'
      elif re.match(f'^{{(.+)}}({re_tag})$', t):  # valid curly form
        return t
      elif re.match(f'^{re_tag}$'):  # valid default-ns form
        return t
      else:
        raise ValueError(f'invalid tag provided to iter: {tag}')

    return self.root.iter(
      _process_tag(tag),
      *(_process_tag(t) for t in tags)
    )

  def find_node_by_xpath(self, xpath):
    elems = self.xpath(xpath)
    if len(elems) == 0:
      raise Exception(
        f'No elements found in document for xpath `{xpath}`\n'
        # + purty_print(self.root)
      )
    elif len(elems) > 1:
      raise Exception(f'Multiple elements found in document for xpath `{xpath}`')
    return elems[0]

  @classmethod
  def from_url(cls, schema_uri):
    req = Request(schema_uri, headers={'User-Agent' : "Magic Browser"}) 
    try:
      response = urlopen(req)
    except HTTPError:
      warnings.warn(
        f'There was an error loading the .xsd file at URL "{schema_uri}". '
        'If this document contains elements associated with this namespace, '
        'you will probably not be able to parse them.'
      )
    else:
      return cls(etree.parse(response).getroot())


class DocParser(NamespaceParser):
  
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self._schema_parser = None  # memoize

  def get_node_tag_list(self, node):
    tag_path = [self.get_tag_prefixed(node.tag)] + [
      self.get_tag_prefixed(a.tag) for a in node.iterancestors()]
    return tuple(tag_path[::-1])

  def build_structure_recursive(self, node, struct_node):
    for child in node:
      # TODO: accomplish w/o xpath
      child_struct_nodes = struct_node.xpath(f'./*[@name="{child.tag}"]')
      if not len(child_struct_nodes):
        # Found a previously-untracked structural element.
        child_struct_node = etree.SubElement(struct_node, 
          'NodeStructure',
          attrib={'name': child.tag}
        )
      else:
        child_struct_node = child_struct_nodes[0]
      self.build_structure_recursive(child, child_struct_node)

  def build_row_structure(self, row_node_tag, element_maker=None):
    """
    I have a feeling I am creating a bespoke cryptic schema for
    each file, but that's what is necessary to actually explore the
    file contents IMO. I'm thinking about elements that conform
    to the schema of the base document (like Trackpoint/Extensions),
    but are derived from a schema that I don't have access to
    (like some stupid activity file schema that isn't documented).
    """
    element_maker = element_maker or ElementMaker()

    struct_node = etree.Element('NodeStructure')
    for row_node in self.root.iter('{*}' + row_node_tag):
      # happens on first loop only, then into the meat
      if struct_node.get('name') is None:
        # This attr value is the longhand namespaced version.
        # I believe this is what I need and can be handled with
        # namespace definitions elsewhere (or here).
        struct_node.set('name', row_node.tag)
      self.build_structure_recursive(row_node, struct_node)      
    return struct_node

  def generate_xslt(self, row_node_tag, fields='all'):
    xsl_uri = 'http://www.w3.org/1999/XSL/Transform'
    
    xsl_nsmap = self.nsmap_default
    del xsl_nsmap['xsi']
    xsl_nsmap['xsl'] = xsl_uri

    # TODO: Check out lxml.html.builder for ideas
    E = ElementMaker(namespace=xsl_uri, nsmap=xsl_nsmap)
    xsl_root = E('stylesheet',
      E('output', **{
        'method': 'xml',
        'omit-xml-declaration': 'no',
        'indent':'yes'
      }),
      E('template',
        E('copy',
          E('apply-templates',
            select='node()|@*')
          ),
        match='node()|@*',
      ),
      version='1.0'
    )

    # Assume every Trackpoint has an identical ancestor structure.
    # Try and impose a uniform column structure for Trackpoints.
    
    # Build an Element representing the possible structures in a row
    row_structure = self.build_row_structure(row_node_tag, element_maker=E)

    for struct_node in row_structure:
      if len(struct_node):
        # Found a nested element
        xsl_root.append(
          E(
            'template',
            *self._build_select_structures(struct_node, element_maker=E),
            match=f'//{self.get_tag_prefixed(row_structure.get("name"))}'
                  f'/{self.get_tag_prefixed(struct_node.get("name"))}'))

    return xsl_root

  def _build_select_structures(
    self,
    struct_node,
    wrapper_tag='',
    select_str='.',
    element_maker=None
  ):
    element_maker = element_maker or ElementMaker()
    wrapper_tag += etree.QName(struct_node.get('name')).localname

    if not len(struct_node):
      element_maker_blank = ElementMaker()
      yield element_maker_blank(
        wrapper_tag,
        element_maker(
          'value-of',
          select=select_str))
    else:
      for child in struct_node:
        select_str_child = select_str + '/'  \
                          + self.get_tag_prefixed(child.get('name'))
        for o in self._build_select_structures(
          child, 
          wrapper_tag=wrapper_tag,
          select_str=select_str_child,
          element_maker=element_maker          
        ):
          yield o

  @property
  def schema_parser(self):
    if self._schema_parser is None:
      self._schema_parser = self._load_schema_parser()
    return self._schema_parser

  def _load_schema_parser(self):  
    # TODO: handle wonky files by assuming a default schema like below.
    # schema_root = load_schema_root('https://www8.garmin.com/xmlschemas/TrainingCenterDatabasev2.xsd')
    return SchemaParser.from_url(self._get_default_schema_url())

  def _get_default_schema_url(self):
    schema_location = self.get(
      f'{{{self.root.nsmap.get("xsi")}}}schemaLocation')
    if schema_location:
      schema_location_list = schema_location.split(' ')
      return schema_location_list[
        schema_location_list.index(self.root.nsmap[None]) + 1]

  def func(self, 
    full_tag_tuple
    # full_node_list
  ):
    def print_node(node):
      print(f'{node.tag}: {node.get("name")}')

    # Prepare the top-level element to be used in the for-loop
    smart_tag = etree.QName(full_tag_tuple[0])
    node_namespace = smart_tag.namespace
    node_localname = smart_tag.localname
    # schema_parser = self.get_schema_parser_by_namespace(node_namespace)
    prefix = self.get_ns_prefix(node_namespace)
    schema_parser = self.schema_parsers[prefix]
    xsd_elem = schema_parser.find_element_by_xpath(f'*[@name="{node_localname}"]')
    for tag_next in full_tag_tuple[1:]:
      # search for the next tag-as-name exclusively within the xsd_type element

      smart_tag = etree.QName(tag_next)
      node_namespace = smart_tag.namespace
      node_localname = smart_tag.localname
      
      # Explicitly what I'm looking for, but unnecessarily descriptive:
      # xpath = f'*[@name="{xsd_elem_top.get("type")}"]/xsd:sequence/xsd:element[@name="{tags_ordered[1]}"]'

      prefix = self.get_ns_prefix(node_namespace)
      schema_parser = self.schema_parsers[prefix]
      
      xsd_elem_type = xsd_elem.get("type")

      xpath = (
        f'*[@name="{xsd_elem_type}"]'
        f'//*[@name="{smart_tag.localname}"]'
      )
      
      try:
        xsd_elem = schema_parser.find_element_by_xpath(xpath)
      except:
        try:
          xpath = (
            f'*[@name="{xsd_elem_type}"]'
            f'/xsd:sequence/xsd:any'
          )
          _ = schema_parser.find_element_by_xpath(xpath)

        except Exception as e:
          print(e)
          print(f'Unable to locate {tag_next}')
        else:
          # That means we've got an <xsd:any> element description.
          # Skip this tag.
          pass


class GarminDocParser(DocParser):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.schema_urls = self._infer_schema_urls()
    # self.schema_parsers = {
    #   prefix: SchemaParser.from_url(self.schema_urls[prefix])
    #   for prefix in self.root.nsmap.keys()
    # }

  @staticmethod
  def _infer_schema_url(namespace):
    s = re.search('^(.*)\/([^\/]*)$', namespace)
    return f'{s.group(1)}{s.group(2)}.xsd'

  def _infer_schema_urls(self):
    nsmap = self.root.nsmap
    default_ns = nsmap[None]

    # If this isn't true, namespace inferences will fail.
    default_ns_url = self._get_default_schema_url()
    assert self._infer_schema_url(default_ns) == default_ns_url

    return {
      prefix: self._infer_schema_url(ns)
      for prefix, ns in nsmap.items()
    }


class SchemaParser(NamespaceParser):

  def get_type_def(self, node_tag):
    elem_def = self.find_element_by_xpath(f'//xsd:element[@name="{node_tag}"]')
    elem_type = elem_def.get('type')
    return self.find_element_by_xpath(f'//xsd:complexType[@name="{elem_type}"]')
  
  @property
  def xml_schema(self):
    return etree.XMLSchema(self.root)

  def get_types_recursive(self, unit_type):
    if unit_type in XSD_TYPES.keys():
      # print(unit_type)
      return unit_type
    
    unit_def = self.find_element_by_xpath(f'//*[@name="{unit_type}"]')
    p = NamespaceParser(unit_def)

    out = {}
    if 'complexType' in unit_def.tag:
      for e in p.xpath('.//xsd:element'):
        out[e.get('name')] = self.get_types_recursive(e.get('type'))
    elif 'simpleType' in unit_def.tag:
      e = p.find_element_by_xpath('.//xsd:restriction')
      # out[p.root.get('name')] = self.get_types_recursive(p.root.get('base'))
      return self.get_types_recursive(e.get('base'))

    return out