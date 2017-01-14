# encoding: utf-8
from logging import getLogger

from django.db import transaction
from knesset_data.dataservice.votes import Vote as DataserviceVote
from knesset_data.html_scrapers.votes import HtmlVote
from laws.models import Vote, VoteAction
from simple.constants import KNESSET_VOTE_PAGE
from simple.scrapers import hebrew_strftime
from simple.scrapers.base_scraper_commands import BaseKnessetDataserviceCollectionCommand
from mks.models import Member
from simple.management.commands.syncdata import Command as SyncdataCommand
from links.models import Link
from django.contrib.contenttypes.models import ContentType

logger = getLogger(__name__)


class VoteScraperException(Exception):
    def __init__(self, *args, **kwargs):
        super(VoteScraperException, self).__init__(*args, **kwargs)


class Command(BaseKnessetDataserviceCollectionCommand):
    DATASERVICE_CLASS = DataserviceVote

    DATASERVICE_MODEL_MAP = {
        # model attribute name | dataservice attribute name, or lambda to get the value
        'src_id': 'id',
        'title': lambda vote: u'{vote} - {sess}'.format(vote=vote.item_dscr, sess=vote.sess_item_dscr),
        'time_string': lambda vote: u'יום %s' % hebrew_strftime(vote.datetime),
        'importance': lambda vote: 1,
        'time': 'datetime',
        'meeting_number': "session_num",
        'vote_number': 'nbr_in_sess',
        'src_url': lambda vote: KNESSET_VOTE_PAGE % vote.id
    }

    VALIDATE_FIELDS_TO_AUTOFIX = ['title', 'src_url']

    help = "Scrape votes data from the knesset"

    @transaction.atomic
    def _update_or_create_vote(self, dataservice_vote, oknesset_vote=None):
        vote_kwargs = self._get_dataservice_model_kwargs(dataservice_vote)
        if oknesset_vote:
            [setattr(oknesset_vote, k, v) for k, v in vote_kwargs.items()]
            oknesset_vote.save()
        else:
            oknesset_vote = Vote.objects.create(**vote_kwargs)
        self._add_vote_actions(dataservice_vote, oknesset_vote)
        oknesset_vote.update_vote_properties()
        SyncdataCommand().find_synced_protocol(oknesset_vote)

        Link.objects.get_or_create(
            title=u'ההצבעה באתר הכנסת',
            url=KNESSET_VOTE_PAGE % oknesset_vote.src_id,
            content_type=ContentType.objects.get_for_model(oknesset_vote), object_pk=str(oknesset_vote.id)
        )
        return oknesset_vote

    def _add_vote_actions(self, dataservice_vote, oknesset_vote):
        for member_id, vote_result_code in HtmlVote.get_from_vote_id(dataservice_vote.id).member_votes:
            member_qs = Member.objects.filter(pk=member_id)
            if member_qs.exists():
                member = member_qs.first()
                vote_type = self._resolve_vote_type(vote_result_code)  # TODO: Move to static helper
                member_party_at_time = member.party_at(oknesset_vote.time.date())
                vote_action, created = VoteAction.objects.get_or_create(vote=oknesset_vote, member=member,
                                                                        defaults={'type': vote_type,
                                                                                  'party': member_party_at_time})
                if created:
                    vote_action.save()
            else:
                raise VoteScraperException('vote %s: could not find member id %s' % (dataservice_vote.id, member_id))

    def _has_existing_object(self, dataservice_vote):
        qs = Vote.objects.filter(src_id=dataservice_vote.id)
        return qs.exists()

    def _get_existing_object(self, dataservice_object):
        return Vote.objects.get(src_id=dataservice_object.id)

    def _create_new_object(self, dataservice_vote):
        try:
            return self._update_or_create_vote(dataservice_vote)
        except VoteScraperException:
            logger.exception('Vote scraping exception for %s' % dataservice_vote)

    def _resolve_vote_type(cls, vote_result_code):
        return {
            'voted for': u'for',
            'voted against': u'against',
            'abstain': u'abstain',
            'did not vote': u'no-vote',
        }[vote_result_code]

    def recreate_objects(self, vote_ids):
        recreated_votes = []
        for vote_id in vote_ids:
            logger.info('Attempting rescraping for vote id %s' % vote_id)
            try:
                try:
                    oknesset_vote = Vote.objects.get(id=int(vote_id))
                except Vote.DoesNotExist:
                    raise VoteScraperException('Vote to recreate does not exist %s' % vote_id)
                vote_src_id = oknesset_vote.src_id
                try:
                    dataservice_vote = self.DATASERVICE_CLASS.get(vote_src_id)
                except Exception:
                    raise VoteScraperException('Failure to fetch knesset data dto for vote id %s' % vote_id)
                VoteAction.objects.filter(vote=oknesset_vote).delete()
                Link.objects.filter(content_type=ContentType.objects.get_for_model(oknesset_vote),
                                    object_pk=oknesset_vote.id).delete()
                recreated_votes.append(self._update_or_create_vote(dataservice_vote, oknesset_vote))
                logger.info('Success rescraping for vote id %s' % vote_id)
            except VoteScraperException:
                logger.exception('Vote scraper exception for vote %s' % vote_id)
        return recreated_votes

    def _get_validate_first_object_title(self, dataservice_object):
        return 'date: %s' % dataservice_object.datetime

    def _validate_attr_actual_expected(self, attr_name, actual_value, expected_value):
        if attr_name == 'time_string':
            # remove some unprintable artifacts which for some reason are in the old scraper's votes
            actual_value = actual_value.replace(u"\u200f", "").replace(u"\xa0", " ")
        elif attr_name == 'title' and actual_value != expected_value:
            # try a slightly different format which exists in DB in some cases
            actual_value = actual_value.replace(u" - הצעת חוק", u" - חוק")
        return super(Command, self)._validate_attr_actual_expected(attr_name, actual_value, expected_value)

    def _validate_dataservice_oknesset_object(self, dataservice_object, oknesset_object, writer, fix):
        oknesset_object.update_from_knesset_data()
        return None
