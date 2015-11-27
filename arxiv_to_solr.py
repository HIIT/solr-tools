#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
# Copyright (c) 2015 University of Helsinki
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#------------------------------------------------------------------------------


from __future__ import print_function
from __future__ import division

import lxml.etree as ET
import sys
from datetime import datetime

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

def log(text):
    print("[" + str(datetime.now()) + "]", text, file=sys.stderr)

#------------------------------------------------------------------------------

def process_file(filename, solr_update):
    log("Processing file {} ...".format(filename))
    tree = ET.parse(filename)
    root = tree.getroot()

    import_warning = False

    for record in root.iterfind('./oai:ListRecords/oai:record', namespaces):
        doc_node = ET.SubElement(solr_update, 'doc')

        def field_node(name, text):
            n = ET.SubElement(doc_node, 'field', attrib = { 'name': name })
            n.text = text
            if text == '':
                print('ERROR: empty text for '+ name, file=sys.stderr)
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
            print('ERROR [{0}]: desc_nodes length {1}'.format(rid, ldn), file=sys.stderr)
            sys.exit(1)

        abstract = ''
        for dn in desc_nodes:
            txt = dn.text
            if txt.startswith('Comment: '):
                txt = txt.replace('Comment: ', '')
                field_node('comment', txt)
            else:
                field_node('abstract', txt)
                abstract = txt

        try:
            from topia.termextract import extract

            if abstract != '':
                extractor = extract.TermExtractor()
                res = extractor(abstract)
                for kw_triple in res:
                    kw = kw_triple[0]
                    if len(kw) > 3:
                        field_node('keyword', kw)

        except ImportError:
            if not import_warning:
                print('WARNING: Unable to import topia.termextract for keyword extraction!', 
                      file=sys.stderr)
                import_warning = True
        
        field_node('url', get_text(mdns + '/dc:identifier'))

#------------------------------------------------------------------------------

if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print("Usage: {0} XML_FILE(S)".format(sys.argv[0]))
        sys.exit(1)

    solr_update = ET.Element('add')

    for f in sys.argv[1:]:
        process_file(f, solr_update)

    log("Generating solr.xml ...")
    tree = ET.ElementTree(solr_update)
    tree.write('solr.xml', pretty_print=True)
