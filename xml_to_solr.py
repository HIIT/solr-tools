#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------

import lxml.etree as ET
import sys

#------------------------------------------------------------------------------

namespaces = {
    'oai': 'http://www.openarchives.org/OAI/2.0/',
    'oai_dc' : 'http://www.openarchives.org/OAI/2.0/oai_dc/',
    'dc' : 'http://purl.org/dc/elements/1.1/'
}

# things not parsed yet
#  <dc:date>2007-03-30</dc:date>
#  <dc:date>2008-12-13</dc:date>
#  <dc:type>text</dc:type>

#------------------------------------------------------------------------------

def process_file(filename, solr_update):
    tree = ET.parse(filename)
    root = tree.getroot()

    for record in root.iterfind('./oai:ListRecords/oai:record', namespaces):
        doc_node = ET.SubElement(solr_update, 'doc')

        def field_node(name, text):
            n = ET.SubElement(doc_node, 'field', attrib = { 'name': name })
            n.text = text
            if text == '':
                print('ERROR: empty text for', name)
                sys.exit(1)
        
        def field_nodes(name, text_nodes):
            for tn in text_nodes:
                field_node(name, tn.text)

        def get_text_nodes(path):
            return record.findall('.' + path, namespaces)

        def get_text(path):
            return record.find('.' + path, namespaces).text

        rid = get_text('/oai:header/oai:identifier')
        field_node('id', rid)
        field_node('last_modified', get_text('/oai:header/oai:datestamp') + \
                   'T00:00:00Z')
        field_node('set', get_text('/oai:header/oai:setSpec'))

        mdns = '/oai:metadata/oai_dc:dc'
        field_node('title', get_text(mdns + '/dc:title'))
        field_nodes('author', get_text_nodes(mdns + '/dc:creator'))
        field_nodes('subject', get_text_nodes(mdns + '/dc:subject'))
        
        desc_nodes = get_text_nodes(mdns + '/dc:description')
        ldn = len(desc_nodes)
        if ldn < 1 or ldn > 2:
            print('ERROR [{0}]: desc_nodes length {1}'.format(rid, ldn))
            sys.exit(1)

        for dn in desc_nodes:
            txt = dn.text
            if txt.startswith('Comment: '):
                field_node('comment', txt.replace('Comment: ', ''))
            else:
                field_node('abstract', txt)
        
        field_node('url', get_text(mdns + '/dc:identifier'))

#------------------------------------------------------------------------------

if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print("Usage: {0} XML_FILE(S)".format(sys.argv[0]))
        sys.exit(1)

    solr_update = ET.Element('add')

    for f in sys.argv[1:]:
        process_file(f, solr_update)

    tree = ET.ElementTree(solr_update)
    tree.write('solr.xml', pretty_print=True)
