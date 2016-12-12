# encoding: utf-8
from __future__ import print_function
from laws.management.commands.scrape_votes import Command as ScrapeVotesCommand
from django.core.management.base import BaseCommand
from optparse import make_option

from django.db.models import Q

from laws.models import Vote

import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Rescrape data for votes missing actual voting data"

    option_list = BaseCommand.option_list + (
        make_option(
            '-n', action='store_true', dest="dryrun", default=False,
            help='Dry run, changes nothing in the db, just display results'
        ),
    )

    def handle(self, *args, **options):
        votes_to_update = Vote.objects.filter(Q(votes_count=0) | Q(votes_count=None))
        logger.info('Found %s votes with missing data' % votes_to_update.count())
        if options['dryrun']:
            logger.info("Not updating the db, dry run was specified")
            return

        votes_ids = votes_to_update.values_list('pk', flat=True)
        ScrapeVotesCommand().recreate_objects(votes_ids)
        logger.info(u'Completed re scraping votes %s' % votes_ids)
