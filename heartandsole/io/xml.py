from lxml import etree
from lxml.builder import ElementMaker
import pandas as pd


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


class DocParser(NamespaceParser):
  
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
