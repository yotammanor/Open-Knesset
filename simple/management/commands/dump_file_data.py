# -*- coding: utf-8 -*-

import datetime

import logging
import os

from django.conf import settings

from okscraper_django.management.base_commands import NoArgsDbLogCommand

from laws.models import Vote

from mks.models import Member

ENCODING = 'utf8'

DATA_ROOT = getattr(settings, 'DATA_ROOT',
                    os.path.join(settings.PROJECT_ROOT, os.path.pardir, os.path.pardir, 'data'))

logger = logging.getLogger(__name__)


class Command(NoArgsDbLogCommand):
    help = "dump data to tsv files"

    requires_model_validation = False

    BASE_LOGGER_NAME = 'open-knesset'

    last_downloaded_vote_id = 0
    last_downloaded_member_id = 0

    def _handle_noargs(self, **options):
        global logger
        logger = self._logger

        logger.info("beginning to dump data to files")
        self.dump()

    def dump(self):
        self.dump_to_file()

    def dump_to_file(self):
        # TODO: find out if anyone is really using this strange code, and if so, do we need to update the dates
        f = open('votes.tsv', 'wt')
        for v in Vote.objects.filter(time__gte=datetime.date(2009, 2, 24)):
            if v.full_text_url is not None:
                link = v.full_text_url.encode('utf-8')
            else:
                link = ''
            if v.summary is not None:
                summary = v.summary.encode('utf-8')
            else:
                summary = ''

            f.write("%d\t%s\t%s\t%s\t%s\n" % (v.id, str(v.time), v.title.encode('utf-8'), summary, link))
        f.close()

        f = open('votings.tsv', 'wt')
        for v in Vote.objects.filter(time__gte=datetime.date(2009, 2, 24)):
            for va in v.actions.all():
                f.write("%d\t%d\t%s\n" % (v.id, va.member.id, va.type))
        f.close()

        f = open('members.tsv', 'wt')
        for m in Member.objects.filter(end_date__gte=datetime.date(2009, 2, 24)):
            f.write("%d\t%s\t%s\n" % (m.id, m.name.encode('utf-8'),
                                      m.current_party.__unicode__().encode(
                                          'utf-8') if m.current_party is not None else ''))
        f.close()
