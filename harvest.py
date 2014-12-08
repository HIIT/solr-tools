#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------------
#
# arXiv harvester
#
# Fetches metadata from arXiv for article metadata.
#
#------------------------------------------------------------------------------

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import time
import sys
import os

#------------------------------------------------------------------------------

# Harvest from date YYYY-MM-DD
# harvest_from = "2014-01-01"

# Harvest from set, e.g. cs=computer science
# see http://export.arxiv.org/oai2?verb=ListSets
harvest_set = "cs"

# Harvest result format
# see http://export.arxiv.org/oai2?verb=ListMetadataFormats
harvest_format = "oai_dc"

# Url for getting records,
# see documentation at
# http://www.openarchives.org/OAI/2.0/openarchivesprotocol.htm#ListRecords
harvest_base_url = "http://export.arxiv.org/oai2"

harvest_url = harvest_base_url + "?verb=ListRecords" \
              "&set={0}&metadataPrefix={1}". \
              format(harvest_set, harvest_format)

harvest_url_continue = harvest_base_url + "?verb=ListRecords&resumptionToken={0}"

sleep_time = 20

#------------------------------------------------------------------------------

def fetch(resumptionToken = "", part=0):
    # Set to starting url, or use the resumptionToken if that is set
    get_url = harvest_url
    if resumptionToken:
        get_url = harvest_url_continue.format(urllib.parse.quote(resumptionToken))

    print("GET", get_url)

    try:
        # GET Request
        response = urllib.request.urlopen(harvest_url)
        data = response.read()

        # Parse XML
        root = ET.fromstring(data)

        # Get resumptionToken from the XML
        namespaces = {'oai': 'http://www.openarchives.org/OAI/2.0/'}
        rtNode = root.find('./oai:ListRecords/oai:resumptionToken', namespaces)
        resumptionToken = rtNode.text

        if not resumptionToken:
            print("ERROR: unable to parse resumptionToken, stopping ...")
            return 1

        #print("resumptionToken={0}".format(resumptionToken))

        # Try setting filename until we find one that isn't in use
        filename = ""
        while not filename:
            filename = "arxiv-{0}-{1}-part{2}.xml".format(harvest_set,
                                                          harvest_format,
                                                          part)
            if os.path.exists(filename):
                filename = ""
                part += 1

        # Write to file
        print("Writing to", filename)
        with open(filename, 'wb') as fp:
            fp.write(data)

        print("Sleeping {0} seconds ...".format(sleep_time))
        time.sleep(sleep_time)
        return fetch(resumptionToken, part + 1)

    except urllib.error.HTTPError as error:
        # If we are fetching too fast the server will give an HTTP 503
        # then we just wait the specified time and try again
        if error.code == 503:
            h = error.headers
            if 'retry-after' in h:
                ra = int(h['retry-after'])
                print("Got HTTP 503, Retry-after: {0}".format(ra))
                print("Sleeping {0} seconds ...".format(ra))
                time.sleep(ra)
                return fetch(resumptionToken, part)

        # Any other errors than 503 are fatal.
        print("ERROR: HTTP returned status {0}!".format(rstat))
        return 1

#------------------------------------------------------------------------------

if __name__ == '__main__':
    if len(sys.argv) > 1:
        fetch(sys.argv[1])
    else:
        fetch()
