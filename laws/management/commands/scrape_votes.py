# encoding: utf-8
from knesset_data.dataservice.votes import Vote as DataserviceVote, VoteMember as DataserviceVoteMember
from knesset_data.html_scrapers.votes import HtmlVote
from laws.models import Vote, VoteAction
from simple.scrapers import hebrew_strftime
from simple.scrapers.management import BaseKnessetDataserviceCollectionCommand
from mks.models import Member
from simple.management.commands.syncdata import Command as SyncdataCommand
from links.models import Link
from django.contrib.contenttypes.models import ContentType
from optparse import make_option
from sys import stdout
import csv


class VoteScraperException(Exception):
    def __init__(self, *args, **kwargs):
        super(VoteScraperException, self).__init__(*args, **kwargs)


class Command(BaseKnessetDataserviceCollectionCommand):
    DATASERVICE_CLASS = DataserviceVote

    option_list = BaseKnessetDataserviceCollectionCommand.option_list + (
        make_option('--validate-votes-pages', dest='validatevotepages',
                    help="validate votes between (and including) given page range\npages in this case are based on vote id ascending, so you'll have the same page number each time"),
        make_option('--validate-skip-to', dest='validateskipto',
                    help="skip to the given vote id (for use with --validate-votes-pages)"),
        make_option('--create-vote-src-id', dest='createvotesrcid',
                    help="create the given vote/s from the comma-separated src ids (assuming they don't already exist in DB)"),
        make_option('--validate-output-file', dest='validateoutputfile',
                    help="where to write the validation results to (defaults to stdout)"),
        make_option('--validate-fix', dest='validatefix', action='store_true',
                    help="try to fix some problems directly in DB which are safe to automatically fix")
    )

    help = "Scrape votes data from the knesset"

    dataservice_model_map = {
        # model attribute name | dataservice attribute name, or lambda to get the value
        'src_id': 'id',
        'title': lambda vote: u'{vote} - {sess}'.format(vote=vote.item_dscr, sess=vote.sess_item_dscr),
        'time_string': lambda vote: u'יום %s'%hebrew_strftime(vote.datetime),
        'importance': lambda vote: 1,
        'time': 'datetime',
        'meeting_number': "session_num",
        'vote_number': 'nbr_in_sess',
        'src_url': lambda vote: "http://www.knesset.gov.il/vote/heb/Vote_Res_Map.asp?vote_id_t=%s"%vote.id
    }

    def _get_dataservice_model_kwargs(self, dataservice_vote):
        return {
            k: getattr(dataservice_vote, v) if isinstance(v, str) else v(dataservice_vote)
            for k,v in self.dataservice_model_map.iteritems()
        }

    def _update_or_create_vote(self, dataservice_vote, oknesset_vote=None):
        vote_kwargs = self._get_dataservice_model_kwargs(dataservice_vote)
        if oknesset_vote:
            [setattr(oknesset_vote, k, v) for k,v in vote_kwargs.iteritems()]
            oknesset_vote.save()
        else:
            oknesset_vote = Vote.objects.create(**vote_kwargs)
        self._add_vote_actions(dataservice_vote, oknesset_vote)
        oknesset_vote.update_vote_properties()
        SyncdataCommand().find_synced_protocol(oknesset_vote)
        Link.objects.create(
                title=u'ההצבעה באתר הכנסת',
                url='http://www.knesset.gov.il/vote/heb/Vote_Res_Map.asp?vote_id_t=%s' % oknesset_vote.src_id,
                content_type=ContentType.objects.get_for_model(oknesset_vote), object_pk=str(oknesset_vote.id)
        )
        return oknesset_vote
        # if v.full_text_url != None:
        #     l = Link(title=u'מסמך הצעת החוק באתר הכנסת', url=v.full_text_url, content_type=ContentType.objects.get_for_model(v), object_pk=str(v.id))
        #     l.save()

    def _add_vote_actions(self, dataservice_vote, oknesset_vote):
        for member_id, vote_result_code in HtmlVote.get_from_vote_id(dataservice_vote.id).member_votes:
            member_qs = Member.objects.filter(pk=member_id)
            if member_qs.exists():
                member = member_qs.first()
                vote_type = self._resolve_vote_type(vote_result_code)
                vote_action, created = VoteAction.objects.get_or_create(vote=oknesset_vote, member=member,
                                                                        defaults={'type': vote_type,
                                                                                  'party': member.current_party})
                if created:
                    vote_action.save()
            else:
                raise VoteScraperException('vote %s: could not find member id %s' % (dataservice_vote.id, member_id))

    def _has_existing_object(self, dataservice_vote):
        qs = Vote.objects.filter(src_id=dataservice_vote.id)
        return qs.exists()

    def _create_new_object(self, dataservice_vote):
        return self._update_or_create_vote(dataservice_vote)

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
            oknesset_vote = Vote.objects.get(id=int(vote_id))
            vote_src_id = oknesset_vote.src_id
            dataservice_vote = self.DATASERVICE_CLASS.get(vote_src_id)
            VoteAction.objects.filter(vote=oknesset_vote).delete()
            Link.objects.filter(content_type=ContentType.objects.get_for_model(oknesset_vote), object_pk=oknesset_vote.id).delete()
            recreated_votes.append(self._update_or_create_vote(dataservice_vote, oknesset_vote))
        return recreated_votes

    def _validate_vote(self, dataservice_vote, csv_writer, fix=False):
        # check the basic metadata
        qs = Vote.objects.filter(src_id=dataservice_vote.id)
        if qs.count() != 1:
            error = 'could not find corresponding vote in DB (qs.count=%s)'%(qs.count(),)
            self._log_warn(error)
            csv_writer.writerow([dataservice_vote.id, '', error.encode('utf-8')])
        else:
            oknesset_vote = qs.first()
            for attr_name, expected_value in self._get_dataservice_model_kwargs(dataservice_vote).iteritems():
                actual_value = getattr(oknesset_vote, attr_name)
                if attr_name == 'time_string':
                    # remove some unprintable artifacts which for some reason are in the old scraper's votes
                    actual_value = actual_value.replace(u"\u200f", "").replace(u"\xa0"," ")
                if attr_name == 'title' and actual_value != expected_value:
                    # try a slightly different format which exists in DB in some cases
                    actual_value = actual_value.replace(u" - הצעת חוק", u" - חוק")
                if actual_value != expected_value:
                    if fix and attr_name in ['title', 'src_url']:
                        self._log_info('fixing mismatch in %s attribute'%(attr_name,))
                        setattr(oknesset_vote, attr_name, expected_value)
                        oknesset_vote.save()
                    else:
                        error = 'value mismatch for %s (expected="%s", actual="%s")'%(attr_name, expected_value, actual_value)
                        self._log_warn(error)
                        csv_writer.writerow([dataservice_vote.id, oknesset_vote.id, error.encode('utf-8')])
            # validate the vote counts
            for type_title, oknesset_count, dataservice_count in zip(
                ('for', 'against', 'abstain'),
                [oknesset_vote.actions.filter(type=t).count() for t in 'for', 'against', 'abstain'],
                [int(getattr(dataservice_vote, t)) for t in 'total_for', 'total_against', 'total_abstain']
            ):
                if oknesset_count != dataservice_count:
                    error = 'mismatch in %s count (expected=%s, actual=%s)'%(type_title, dataservice_count, oknesset_count)
                    self._log_warn(error)
                    csv_writer.writerow([dataservice_vote.id, oknesset_vote.id, error.encode('utf-8')])

    def _validate_vote_pages(self, out, pages, skip_to_vote_id, try_to_fix):
        writer = csv.writer(out)
        writer.writerow(['knesset vote id', 'open knesset vote id', 'error'])
        for page in pages:
            self._log_info('downloading page %s'%page)
            votes = DataserviceVote.get_page(order_by=('id', 'asc'), page_num=page)
            self._log_info('downloaded %s votes'%len(votes))
            self._log_info('  first vote date: %s'%votes[0].datetime)
            for vote in votes:
                if not skip_to_vote_id or int(vote.id) >= int(skip_to_vote_id):
                    self._log_info('validating vote %s'%vote.id)
                    self._validate_vote(vote, writer, fix=try_to_fix)

    def _handle_noargs(self, **options):
        if options.get('createvotesrcid'):
            src_ids = [int(i) for i in options['createvotesrcid'].split(',')]
            self._log_info('downloading %s votes'%len(src_ids))
            dataservice_votes = []
            for src_id in src_ids:
                self._log_info('downloading vote %s'%src_id)
                dataservice_vote = DataserviceVote.get(src_id)
                dataservice_votes.append(dataservice_vote)
            self._log_info('downloaded all votes data, will create them now')
            oknesset_votes = []
            for dataservice_vote in dataservice_votes:
                if self._has_existing_object(dataservice_vote):
                    raise VoteScraperException('vote already exists in DB: %s'%dataservice_vote.id)
                else:
                    oknesset_vote = self._create_new_object(dataservice_vote)
                    oknesset_votes.append(oknesset_vote)
                    self._log_info('created vote %s (%s)'%(oknesset_vote, oknesset_vote.pk))
            self._log_info('done, created %s votes'%len(oknesset_votes))
        elif options.get('validatevotepages'):
            from_page, to_page = [int(p) for p in options['validatevotepages'].split('-')]
            skip_to_vote_id = options.get('validateskipto', None)
            output_file_name = options.get('validateoutputfile', None)
            try_to_fix = options.get('validatefix', False);
            if from_page > to_page:
                # we support reverse pages as well!
                pages = reversed(range(to_page, from_page+1))
            else:
                pages = range(from_page, to_page+1)
            if output_file_name:
                out = open(output_file_name, 'wb')
            else:
                out = stdout
            self._validate_vote_pages(out, pages, skip_to_vote_id, try_to_fix)
            if output_file_name:
                out.close()
            self._log_info('done')
        else:
            return super(Command, self)._handle_noargs(**options)