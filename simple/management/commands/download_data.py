# -*- coding: utf-8 -*-

import gzip
import logging
import os
import re

import time

import urllib
import urllib2

from django.conf import settings

from okscraper_django.management.base_commands import NoArgsDbLogCommand

from simple.constants import SECOND_AND_THIRD_READING_LAWS_URL

from simple.parsers import mk_info_html_parser as mk_parser

ENCODING = 'utf8'

DATA_ROOT = getattr(settings, 'DATA_ROOT',
                    os.path.join(settings.PROJECT_ROOT, os.path.pardir, os.path.pardir, 'data'))

logger = logging.getLogger(__name__)


class Command(NoArgsDbLogCommand):
    help = "Downloads data from sources"

    requires_model_validation = False

    BASE_LOGGER_NAME = 'open-knesset'

    last_downloaded_vote_id = 0
    last_downloaded_member_id = 0

    def _handle_noargs(self, **options):
        global logger
        logger = self._logger

        logger.info("beginning download phase")
        self.download_all()

    def download_all(self):
        self.get_members_data()
        self.get_votes_data()
        self.get_laws_data()

    def read_laws_page(self, index):

        url = '%s' % SECOND_AND_THIRD_READING_LAWS_URL
        data = urllib.urlencode({'RowStart': index})
        urlData = urllib2.urlopen(url, data)
        page = urlData.read().decode('windows-1255').encode('utf-8')
        return page

    def parse_laws_page(self, page):
        names = []
        exps = []
        links = []
        count = -1
        lines = page.split('\n')
        for line in lines:

            r = re.search("""Href=\"(.*?)\">""", line)
            if r is not None:
                link = 'http://www.knesset.gov.il/privatelaw/' + r.group(1)
            r = re.search("""<td class="LawText1">(.*)""", line)
            if r is not None:
                name = r.group(1).replace("</td>", "").strip()
                if len(name) > 1 and name.find('span') < 0:
                    names.append(name)
                    links.append(link)
                    exps.append('')
                    count += 1
            if re.search("""arrResume\[\d*\]""", line) is not None:
                r = re.search('"(.*)"', line)
                if r is not None:
                    try:
                        exps[count] += r.group(1).replace('\t', ' ')
                    except:
                        pass

        return names, exps, links

    def get_laws_data(self):
        f = gzip.open(os.path.join(DATA_ROOT, 'laws.tsv.gz'), "wb")
        for x in range(0, 910, 26):  # TODO: find limits of download
            # for x in range(0,50,26): # for debug
            page = self.read_laws_page(x)
            (names, exps, links) = self.parse_laws_page(page)
            for (name, exp, link) in zip(names, exps, links):
                f.write("%s\t%s\t%s\n" % (name, exp, link))
        f.close()

    def get_votes_data(self):
        # TODO: is this ever used?
        self.update_last_downloaded_vote_id()
        pages_ids = range(self.last_downloaded_vote_id + 1,
                          17000)  # this is the range of page ids to go over. currently its set manually.
        for page_id in pages_ids:
            f = gzip.open(os.path.join(DATA_ROOT, 'results.tsv.gz'), "ab")
            f2 = gzip.open(os.path.join(DATA_ROOT, 'votes.tsv.gz'), "ab")
            (page, src_url) = self.read_votes_page(page_id)
            title = self.get_page_title(page)
            if title == """הצבעות במליאה-חיפוש""":  # found no vote with this id
                logger.debug("no vote found at id %d" % page_id)
            else:
                count_for = 0
                count_against = 0
                count_abstain = 0
                count_no_vote = 0
                (name, meeting_num, vote_num, date) = self.get_vote_data(page)
                results = self.read_member_votes(page)
                for (voter, party, vote) in results:
                    f.write("%d\t%s\t%s\t%s\n" % (page_id, voter, party, vote))
                    if vote == "for":
                        count_for += 1
                    if vote == "against":
                        count_against += 1
                    if vote == "abstain":
                        count_abstain += 1
                    if vote == "no-vote":
                        count_no_vote += 1
                f2.write("%d\t%s\t%s\t%s\t%s\t%s\t%d\t%d\t%d\t%d\n" % (
                    page_id, src_url, name, meeting_num, vote_num, date, count_for, count_against, count_abstain,
                    count_no_vote))
                logger.debug("downloaded data with vote id %d" % page_id)

            f.close()
            f2.close()

    def get_members_data(self, max_mk_id=1000, min_mk_id=1):
        """downloads members data to local files
        """
        # TODO - find max member id in knesset website and use for max_mk_id

        f = gzip.open(os.path.join(DATA_ROOT, 'members.tsv.gz'), "wb")

        fields = ['img_link', 'טלפון', 'פקס', 'אתר נוסף',
                  'דואר אלקטרוני', 'מצב משפחתי',
                  'מספר ילדים', 'תאריך לידה', 'שנת לידה',
                  'מקום לידה', 'תאריך פטירה', 'שנת עלייה',
                  'כנסת 18', 'כנסת 19', 'כנסת 20']
        # note that hebrew strings order is right-to-left
        # so output file order is id, name, img_link, phone, ...

        fields = [unicode(field.decode('utf8')) for field in fields]

        for mk_id in range(min_mk_id, max_mk_id):
            logger.debug('mk %s' % mk_id)
            try:
                m = mk_parser.MKHtmlParser(mk_id).Dict
            except UnicodeDecodeError as e:
                logger.error('unicode decode error at mk id %s' % mk_id)
                m = {}
            if m.get('name'):
                name = m['name'].replace(u'\xa0', u' ').encode(ENCODING).replace('&nbsp;', ' ')
            else:
                continue
            f.write("%d\t%s\t" % (mk_id, name))
            for field in fields:
                value = ''
                if m.get(field):
                    value = m[field].encode(ENCODING)
                f.write("%s\t" % value)
            f.write("\n")
        f.close()

    def update_last_downloaded_vote_id(self):
        """
        Reads local votes file, and sets self.last_downloaded_id to the highest id found in the file.
        This is later used to skip downloading of data alreay downloaded.
        """
        try:
            f = gzip.open(os.path.join(DATA_ROOT, 'votes.tsv.gz'))
        except:
            self.last_downloaded_vote_id = 0
            logger.debug("votes file does not exist. setting last_downloaded_vote_id to 0")
            return
        content = f.read().split('\n')
        for line in content:
            if (len(line) < 2):
                continue
            s = line.split('\t')
            vote_id = int(s[0])
            if vote_id > self.last_downloaded_vote_id:
                self.last_downloaded_vote_id = vote_id
        logger.debug("last id found in local files is %d. " % self.last_downloaded_vote_id)
        f.close()

    def get_search_string(self, s):
        if isinstance(s, unicode):
            s = s.replace(u'\u201d', '').replace(u'\u2013', '')
        else:
            s = s.replace('\xe2\x80\x9d', '').replace('\xe2\x80\x93', '')
        return re.sub(r'["\(\) ,-]', '', s)

    heb_months = ['ינואר', 'פברואר', 'מרץ', 'אפריל', 'מאי', 'יוני', 'יולי', 'אוגוסט', 'ספטמבר', 'אוקטובר', 'נובמבר',
                  'דצמבר']

    def read_votes_page(self, voteId, retry=0):
        """
        Gets a votes page from the knesset website.
        returns a string (utf encoded)
        """
        url = "http://www.knesset.gov.il/vote/heb/Vote_Res_Map.asp?vote_id_t=%d" % voteId
        try:
            urlData = urllib2.urlopen(url)
            page = urlData.read().decode('windows-1255').encode('utf-8')
            time.sleep(2)
        except Exception as e:
            logger.warn(e)
            if retry < 5:
                logger.warn("waiting some time and trying again... (# of retries = %d)" % (retry + 1))
                page = self.read_votes_page(voteId, retry + 1)
            else:
                logger.exception("read votes page failed too many times")
                return None
        return page, url

    def read_member_votes(self, page, return_ids=False):
        """
        Returns a tuple of (name, party, vote) describing the vote found in page, where:
         name is a member name
         party is the member's party
         vote is 'for','against','abstain' or 'no-vote'
         if return_ids = True, it will return member id, and not name as first element.
        """
        results = []
        pattern = re.compile("""Vote_Bord""")
        match = pattern.split(page)
        last_party = None
        for i in match:
            vote = ""
            if re.match("""_R1""", i):
                vote = "for"
            if re.match("""_R2""", i):
                vote = "against"
            if re.match("""_R3""", i):
                vote = "abstain"
            if re.match("""_R4""", i):
                vote = "no-vote"
            if vote != "":
                name = re.search("""DataText4>([^<]*)</a>""", i).group(1)
                name = re.sub("""&nbsp;""", " ", name)
                m_id = re.search("""mk_individual_id_t=(\d+)""", i).group(1)
                party = re.search("""DataText4>([^<]*)</td>""", i).group(1)
                party = re.sub("""&nbsp;""", " ", party)
                if party == """ " """:
                    party = last_party
                else:
                    last_party = party
                if return_ids:
                    results.append((m_id, party, vote))
                else:
                    results.append((name, party, vote))

        return results

    def get_page_title(self, page):
        """
        Returns the title of a vote page
        """
        title = re.search("""<TITLE>([^<]*)</TITLE>""", page)
        return title.group(1)

    def get_vote_data(self, page):
        """
        Returns name, meeting number, vote number and date from a vote page
        """
        meeting_num = re.search("""מספר ישיבה: </td>[^<]*<[^>]*>([^<]*)<""", page).group(1)
        vote_num = re.search("""מספר הצבעה: </td>[^<]*<[^>]*>([^<]*)<""", page).group(1)
        name = re.search("""שם החוק: </td>[^<]*<[^>]*>([^<]*)<""", page).group(1)
        name = name.replace("\t", " ")
        name = name.replace("\n", " ")
        name = name.replace("\r", " ")
        name = name.replace("&nbsp;", " ")
        date = re.search("""תאריך: </td>[^<]*<[^>]*>([^<]*)<""", page).group(1)
        return \
            name, meeting_num, vote_num, date
