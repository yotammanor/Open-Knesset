# encoding: utf-8
from __future__ import print_function

from django.core.management.base import BaseCommand
from optparse import make_option

from laws.models import Vote
from mks.models import Knesset
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Recalculate vote properties for current knesset"

    option_list = BaseCommand.option_list + (
        make_option(
            '-n', action='store_true', dest="dryrun", default=False,
            help='Dry run, changes nothing in the db, just display results'
        ),
    )

    def handle(self, *args, **options):

        start_date = Knesset.objects.current_knesset().start_date

        votes_to_update = Vote.objects.filter(time__gte=start_date)
        logger.info('Found {0} votes to update since {1}'.format(votes_to_update.count(), start_date))
        if options['dryrun']:
            logger.info("Not updating the db, dry run was specified")
            return

        for vote in votes_to_update:

            vote.update_vote_properties()
            logger.info(u'Recalculated vote properties for {0}'.format(vote))
