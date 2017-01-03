# -*- coding: utf-8 -*-

import datetime
import gzip
import logging
import os
import re

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import Max
from okscraper_django.management.base_commands import NoArgsDbLogCommand

from laws.models import Vote, VoteAction
from links.models import Link
from mks.models import Member, Party, Membership

from simple.constants import CANONICAL_PARTY_ALIASES

ENCODING = 'utf8'

DATA_ROOT = getattr(settings, 'DATA_ROOT',
                    os.path.join(settings.PROJECT_ROOT, os.path.pardir, os.path.pardir, 'data'))

logger = logging.getLogger(__name__)


class Command(NoArgsDbLogCommand):
    help = "loading pre existing files to db"

    requires_model_validation = False

    BASE_LOGGER_NAME = 'open-knesset'

    last_downloaded_vote_id = 0
    last_downloaded_member_id = 0

    def _handle_noargs(self, **options):
        global logger
        logger = self._logger

        logger.info("beginning to load data from pre existing files")
        self.load()

    def load(self):
        self.update_members_from_file()
        self.update_db_from_files()

    def update_members_from_file(self):
        logger.debug('update_members_from_file')
        f = gzip.open(os.path.join(DATA_ROOT, 'members.tsv.gz'))
        content = f.read().split('\n')
        for line in content:
            if len(line) <= 1:
                continue
            (member_id, name, img_url, phone, fax, website, email,
             family_status, number_of_children, date_of_birth,
             year_of_birth, place_of_birth, date_of_death,
             year_of_aliyah, k18, k19, _) = line.split('\t')
            if email != '':
                email = email.split(':')[1]
            try:
                if date_of_birth.find(',') >= 0:
                    date_of_birth = date_of_birth.split(',')[1].strip(' ')
                date_of_birth = datetime.datetime.strptime(date_of_birth, "%d/%m/%Y")
            except:
                date_of_birth = None
            try:
                if date_of_birth.find(',') >= 0:
                    date_of_death = date_of_birth.split(',')[1].strip(' ')
                date_of_death = datetime.datetime.strptime(date_of_death, "%d/%m/%Y")
            except:
                date_of_death = None
            try:
                year_of_birth = int(year_of_birth)
            except:
                year_of_birth = None
            try:
                year_of_aliyah = int(year_of_aliyah)
            except:
                year_of_aliyah = None
            try:
                number_of_children = int(number_of_children)
            except:
                number_of_children = None

            try:
                m = Member.objects.get(id=member_id)
                m.phone = phone
                m.fax = fax
                m.email = email
                m.family_status = family_status
                m.number_of_children = number_of_children
                m.date_of_death = date_of_death
                m.save()
                logger.debug('updated member %d' % m.id)
            except Member.DoesNotExist:  # member_id not found. create new
                m = Member(id=member_id, name=name, img_url=img_url, phone=phone, fax=fax, website=None, email=email,
                           family_status=family_status,
                           number_of_children=number_of_children, date_of_birth=date_of_birth,
                           place_of_birth=place_of_birth,
                           date_of_death=date_of_death, year_of_aliyah=year_of_aliyah)
                m.save()
                m = Member.objects.get(pk=member_id)  # make sure we are are
                # working on the db object. e.g m.id is a number.
                logger.debug('created member %d' % m.id)
                if len(website) > 0:
                    l = Link(title='אתר האינטרנט של %s' % name, url=website,
                             content_type=ContentType.objects.get_for_model(m), object_pk=str(m.id))
                    l.save()

            if k19:  # KNESSET 19 specific
                parties = Party.objects.filter(knesset_id=19).values_list('name', 'id')
                k19 = k19.decode(ENCODING)
                for k, v in parties:
                    if k in k19:
                        m.current_party_id = int(v)
                        logger.debug('member %s, k19 %s, party %s'
                                     % (m.name,
                                        k19,
                                        k))
                        m.save()
                if m.current_party is None:
                    logger.debug('member %s, k19 %s not found' %
                                 (m.name,
                                  k19))

    def get_search_string(self, s):
        if isinstance(s, unicode):
            s = s.replace(u'\u201d', '').replace(u'\u2013', '')
        else:
            s = s.replace('\xe2\x80\x9d', '').replace('\xe2\x80\x93', '')
        return re.sub(r'["\(\) ,-]', '', s)

    heb_months = ['ינואר', 'פברואר', 'מרץ', 'אפריל', 'מאי', 'יוני', 'יולי', 'אוגוסט', 'ספטמבר', 'אוקטובר', 'נובמבר',
                  'דצמבר']

    def update_db_from_files(self):
        logger.debug("Update DB From Files")

        try:
            laws = []  # of lists: [name,name_for_search,explanation,link]
            f = gzip.open(os.path.join(DATA_ROOT, 'laws.tsv.gz'))
            content = f.read().split('\n')
            for line in content:
                law = line.split('\t')
                if len(law) == 3:
                    name_for_search = self.get_search_string(law[0])
                    law.insert(1, name_for_search)
                    laws.append(law)
            f.close()

            parties = dict()  # key: party-name; value: Party
            members = dict()  # key: member-name; value: Member
            votes = dict()  # key: id; value: Vote
            memberships = dict()  # key: (member.id,party.id)
            current_max_src_id = Vote.objects.aggregate(Max('src_id'))['src_id__max']
            if current_max_src_id == None:  # the db contains no votes, meaning its empty
                current_max_src_id = 0

            logger.debug("processing votes data")
            f = gzip.open(os.path.join(DATA_ROOT, 'votes.tsv.gz'))
            content = f.read().split('\n')
            for line in content:
                if len(line) <= 1:
                    continue
                (vote_id, vote_src_url, vote_label, vote_meeting_num, vote_num, vote_time_string, _, _, _,
                 _) = line.split('\t')
                # if vote_id < current_max_src_id: # skip votes already parsed.
                #    continue
                vote_time_string = vote_time_string.replace('&nbsp;', ' ')
                for i in self.heb_months:
                    if i in vote_time_string:
                        month = self.heb_months.index(i) + 1
                day = re.search("""(\d\d?)""", vote_time_string).group(1)
                year = re.search("""(\d\d\d\d)""", vote_time_string).group(1)
                vote_hm = datetime.datetime.strptime(vote_time_string.split(' ')[-1], "%H:%M")
                vote_date = datetime.date(int(year), int(month), int(day))
                vote_time = datetime.datetime(int(year), int(month), int(day), vote_hm.hour, vote_hm.minute)
                vote_label_for_search = self.get_search_string(vote_label)

                # if vote_date < datetime.date(2009, 02, 24): # vote before 18th knesset
                #    continue

                try:
                    v = Vote.objects.get(src_id=vote_id)
                    created = False
                except:
                    v = Vote(title=vote_label, time_string=vote_time_string, importance=1, src_id=vote_id,
                             time=vote_time)
                    try:
                        vote_meeting_num = int(vote_meeting_num)
                        v.meeting_number = vote_meeting_num
                    except:
                        pass
                    try:
                        vote_num = int(vote_num)
                        v.vote_number = vote_num
                    except:
                        pass
                    v.src_url = vote_src_url
                    for law in laws:
                        (_, law_name_for_search, law_exp, law_link) = law
                        if vote_label_for_search.find(law_name_for_search) >= 0:
                            v.summary = law_exp
                            v.full_text_url = law_link
                    v.save()
                    if v.full_text_url != None:
                        l = Link(title=u'מסמך הצעת החוק באתר הכנסת', url=v.full_text_url,
                                 content_type=ContentType.objects.get_for_model(v), object_pk=str(v.id))
                        l.save()
                votes[int(vote_id)] = v
            f.close()

            logger.debug("processing member votes data")
            f = gzip.open(os.path.join(DATA_ROOT, 'results.tsv.gz'))
            content = f.read().split('\n')
            for line in content:
                if len(line) < 2:
                    continue
                s = line.split('\t')  # (id,voter,party,vote)

                vote_id = int(s[0])
                voter = s[1]
                voter_party = s[2]

                # transform party names to canonical form
                if voter_party in CANONICAL_PARTY_ALIASES:
                    voter_party = CANONICAL_PARTY_ALIASES[voter_party]

                vote = s[3]

                try:
                    v = votes[vote_id]
                except KeyError:  # this vote was skipped in this read, also skip voteactions and members
                    continue
                vote_date = v.time.date()

                # create/get the party appearing in this vote
                if voter_party in parties:
                    party = parties[voter_party]
                    created = False
                else:
                    party, created = Party.objects.get_or_create(name=voter_party)
                    parties[voter_party] = party
                    # if created: # this is magic needed because of unicode chars. if you don't do this, the object p will have gibrish as its name.
                    # only when it comes back from the db it has valid unicode chars.

                # use this vote's time to update the party's start date and end date
                if (party.start_date is None) or (party.start_date > vote_date):
                    party.start_date = vote_date
                if (party.end_date is None) or (party.end_date < vote_date):
                    party.end_date = vote_date
                if created:  # save on first time, so it would have an id, be able to link, etc. all other updates are saved in the end
                    party.save()

                # create/get the member voting
                if voter in members:
                    member = members[voter]
                    created = False
                else:
                    try:
                        member = Member.objects.get(name=voter)
                    except:  # if there are several people with same age,
                        member = Member.objects.filter(name=voter).order_by('-date_of_birth')[
                            0]  # choose the younger. TODO: fix this
                    members[voter] = member

                # use this vote's date to update the member's dates.
                if (member.start_date is None) or (member.start_date > vote_date):
                    member.start_date = vote_date
                if (member.end_date is None) or (member.end_date < vote_date):
                    member.end_date = vote_date
                # if created: # save on first time, so it would have an id, be able to link, etc. all other updates are saved in the end
                #    m.save()


                # create/get the membership (connection between member and party)
                if ((member.id, party.id) in memberships):
                    ms = memberships[(member.id, party.id)]
                    created = False
                else:
                    ms, created = Membership.objects.get_or_create(member=member, party=party)
                    memberships[(member.id, party.id)] = ms
                # if created: # again, unicode magic
                #    ms = Membership.objects.get(member=m,party=p)
                # again, update the dates on the membership
                if (ms.start_date is None) or (ms.start_date > vote_date):
                    ms.start_date = vote_date
                if (ms.end_date is None) or (ms.end_date < vote_date):
                    ms.end_date = vote_date
                if created:  # save on first time, so it would have an id, be able to link, etc. all other updates are saved in the end
                    ms.save()

                # add the current member's vote

                va, created = VoteAction.objects.get_or_create(vote=v, member=member, type=vote,
                                                               party=member.current_party)
                if created:
                    va.save()

            logger.debug("done")
            logger.debug(
                "saving data: %d parties, %d members, %d memberships " % (len(parties), len(members), len(memberships)))
            for party in parties:
                parties[party].save()
            for member in members:
                members[member].save()
            for ms in memberships:
                memberships[ms].save()

            logger.debug("done")
            f.close()
        except Exception:

            logger.exception('Update db from file exception')
