# encoding: utf-8
"""This file contains some util function to help parse the PDF files,
   found in http://www.knesset.gov.il/laws/heb/template.asp?Type=3
"""

import logging
import re
import subprocess
import sys
import traceback
import urllib2
from datetime import date

from knesset.utils import clean_string
from simple.government_bills import pdftools

logger = logging.getLogger("open-knesset.parse_knesset_bill_pdf")


def parse(url):
    """This is the main function that should be used. pass a url of a law PDF to parse
       return value is an array of laws data found
       each law data is a dict with keys 'title', 'references' and 'original_ids'.
       original_ids is an array of original laws ids.
    """
    download_pdf(url)
    pdftotext()
    return parse_pdf_text(url=url)


def pdftotext():
    rc = subprocess.call([pdftools.PDFTOTEXT, '-enc', 'UTF-8', 'tmp.pdf', 'tmp.txt'])
    if rc:
        logger.error('pdftotext returned error code %d' % rc)


def download_pdf(url, filename=None):
    logger.debug('downloading url %s' % url)
    if not filename:
        filename = 'tmp.pdf'
    f = open(filename, 'wb')
    d = urllib2.urlopen(url)
    f.write(d.read())
    f.close()


def parse_pdf_text(filename=None, url=None):
    logger.debug('parse_pdf_text filename=%s url=%s' % (str(filename),
                                                        str(url)))
    if not filename:
        filename = 'tmp.txt'
    f = open(filename, 'rt')
    content = f.read()
    d = None
    result = []
    m = re.search('עמוד(.*?)מתפרסמת בזה', content, re.UNICODE | re.DOTALL)
    if not m:  # couldn't read this file
        logger.warn("can't read this file")
        return None

    m = clean_string(m.group(1).decode('utf8'))
    m2 = re.findall('^(הצעת חוק.*?) \. '.decode('utf8'), m, re.UNICODE | re.DOTALL | re.MULTILINE)
    m3 = re.findall('^(חוק.*?) \. '.decode('utf8'), m, re.UNICODE | re.DOTALL | re.MULTILINE)
    m2.extend(m3)
    for title in m2:
        law = {}
        title = title.replace('\n', ' ')
        s = re.search(r'[^\d]\d{2,3}[^\d]', title + ' ', re.UNICODE)  # find numbers of 2-3 digits
        if s:
            (a, b) = s.span()
            title = title[:a + 1] + title[b - 2:a:-1] + title[b - 1:]  # reverse them
        law['title'] = title
        result.append(law)

    count = 0  # count how many bills we found the original_ids for so far
    lines = content.split('\n')
    for line in lines:
        m = re.search('(\d{4,4})[\.|\s](\d+)[\.|\s](\d+)', line)
        if m:
            d = date(int(m.group(1)[::-1]), int(m.group(2)[::-1]), int(m.group(3)[::-1]))

        m = re.search('[הצעת|הצעות] חוק מס.*?\d+/\d+.*?[הועברה|הועברו]'.decode('utf8'), line.decode('utf8'), re.UNICODE)
        if m:
            try:
                result[count]['references'] = line
                m2 = re.findall('\d+/\d+', line.decode('utf8'), re.UNICODE)  # find IDs of original proposals
                result[count]['original_ids'] = [a[::-1] for a in m2]
                count += 1
            except IndexError:
                logger.exception(u'parse knesset pdf exception with content {0}'.format(content))

    for l in result:
        l['date'] = d
    return result
