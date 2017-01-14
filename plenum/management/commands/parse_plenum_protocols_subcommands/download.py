# encoding: utf-8

import datetime
import logging
import os
import re
import urllib
import urllib2

from BeautifulSoup import BeautifulSoup
from django.conf import settings

from committees.models import Committee, CommitteeMeeting
from knesset.utils import send_chat_notification
from simple.utils import doc_to_xml

PLENUM_URL = "http://www.knesset.gov.il/plenum/heb/plenum_queue.aspx"

FULL_URL = "http://www.knesset.gov.il/plenum/heb/display_full.asp"
FILE_BASE_URL = "http://www.knesset.gov.il/plenum/heb/"
WORDS_OF_THE_KNESSET = u"דברי הכנסת"
WORDS_OF_THE_KNESSET_FULL = u"כל הפרוטוקול"
DISCUSSIONS_ON_DATE = u"הדיונים בתאריך"

logger = logging.getLogger('open-knesset')


def _get_committees_index_page(full):
    if full:
        url = FULL_URL
        encoding = 'iso_8859_8'
    else:
        url = PLENUM_URL
        # encoding='utf8'
        # the encoding of this page used to be utf-8 but looks like they reverted back to iso-8859-8
        encoding = 'iso_8859_8'
    logger.info('getting index page html from %s' % url)
    try:
        return unicode(urllib2.urlopen(url).read(), encoding)
    except:
        logger.exception(u'could not fetch committees_index_page for url %s' % url)
        send_chat_notification(__name__, "could not fetch committees index page", {'url': url})
        return ''


def _copy(url, to, recopy=False):
    # logger.debug("copying from "+url+" to "+to)
    d = os.path.dirname(to)
    if not os.path.exists(d):
        os.makedirs(d)
    if not os.path.exists(to) or recopy:
        urllib.urlretrieve(url, to + ".tmp")
        os.rename(to + '.tmp', to)
    else:
        logger.debug(u'already downloaded url %s' % url)


def _antiword(filename):
    try:
        return doc_to_xml(filename, logger)
    except:
        logger.exception(u'antiword failure with file: %s' % filename)
        return ''


def _urlAlreadyDownloaded(url):
    plenum = Committee.objects.filter(type='plenum')[0]
    if CommitteeMeeting.objects.filter(committee=plenum, src_url=url).count() > 0:
        return True
    else:
        return False


def _updateDb(xmlData, url, year, mon, day):
    logger.debug('update db %s, %s, %s, %s, %s' % (len(xmlData), url, year, mon, day))
    plenum = Committee.objects.filter(type='plenum')[0]
    cms = CommitteeMeeting.objects.filter(committee=plenum, src_url=url)
    if cms.count() > 0:
        meeting = cms[0]
    else:
        meeting = CommitteeMeeting(
            committee=plenum,
            date=datetime.datetime(int(year), int(mon), int(day)),
            src_url=url,
            topics=u'ישיבת מליאה מתאריך ' + day + '/' + mon + '/' + year,
            date_string='' + day + '/' + mon + '/' + year
        )
    meeting.protocol_text = xmlData
    meeting.save()


def _downloadLatest(full, redownload):
    html = _get_committees_index_page(full)
    soup = BeautifulSoup(html)
    if full:
        words_of_the_knesset = WORDS_OF_THE_KNESSET_FULL
    else:
        words_of_the_knesset = WORDS_OF_THE_KNESSET
    aelts = soup('a', text=words_of_the_knesset)
    for aelt in aelts:
        selt = aelt.findPrevious('span', text=re.compile(DISCUSSIONS_ON_DATE))
        href = aelt.parent.get('href')
        if href.startswith('http'):
            url = href
        else:
            url = FILE_BASE_URL + href
        filename = re.search(r"[^/]*$", url).group()
        logger.debug(filename)
        m = re.search(r"\((.*)/(.*)/(.*)\)", selt)
        if m is None:
            selt = selt.findNext()
            m = re.search(r"\((.*)/(.*)/(.*)\)", unicode(selt))
        if m is not None:
            day = m.group(1)
            mon = m.group(2)
            year = m.group(3)
            url = url.replace('/heb/..', '')
            logger.debug(url)
            if not redownload and _urlAlreadyDownloaded(url):
                logger.debug('url already downloaded')
            else:
                DATA_ROOT = getattr(settings, 'DATA_ROOT')
                _copy(url.replace('/heb/..', ''),
                      DATA_ROOT + 'plenum_protocols/' + year + '_' + mon + '_' + day + '_' + filename,
                      recopy=redownload)
                xmlData = _antiword(DATA_ROOT + 'plenum_protocols/' + year + '_' + mon + '_' + day + '_' + filename)
                os.remove(DATA_ROOT + 'plenum_protocols/' + year + '_' + mon + '_' + day + '_' + filename)
                if xmlData != '':
                    _updateDb(xmlData, url, year, mon, day)


def Download(redownload, _logger):
    global logger
    logger = _logger
    _downloadLatest(False, redownload)
    _downloadLatest(True, redownload)


def download_for_existing_meeting(meeting):
    DATA_ROOT = getattr(settings, 'DATA_ROOT')
    _copy(meeting.src_url, DATA_ROOT + 'plenum_protocols/tmp')
    xmlData = _antiword(DATA_ROOT + 'plenum_protocols/tmp')
    os.remove(DATA_ROOT + 'plenum_protocols/tmp')
    meeting.protocol_text = xmlData
    meeting.save()
