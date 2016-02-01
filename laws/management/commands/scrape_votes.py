# encoding: utf-8
from knesset_data.dataservice.votes import Vote as DataserviceVote
from laws.models import Vote
from simple.scrapers import hebrew_strftime
from simple.scrapers.management import BaseKnessetDataserviceCommand


class Command(BaseKnessetDataserviceCommand):

    DATASERVICE_CLASS = DataserviceVote

    help = "Scrape latest votes data from the knesset"

    def _has_existing_object(self, dataservice_vote):
        qs = Vote.objects.filter(src_id=dataservice_vote.id)
        return qs.exists()

    def _create_new_object(self, dataservice_vote):
        return Vote.objects.create(
            src_id=dataservice_vote.id,
            title=u'{vote} - {sess}'.format(vote=dataservice_vote.item_dscr, sess=dataservice_vote.sess_item_dscr),
            time_string = u'יום '+hebrew_strftime(dataservice_vote.datetime),
            importance = 1,
            time = dataservice_vote.datetime,
            meeting_number = dataservice_vote.session_num,
            vote_number = dataservice_vote.nbr_in_sess,
            src_url = dataservice_vote.id
        )
        # TODO: find the related data for the vote, preferably from API
        # TODO: here, we reparse the votes, so we should probably limit the parser according to last time we accessed this vote or something like that
        # if v.full_text_url != None:
        #     l = Link(title=u'מסמך הצעת החוק באתר הכנסת', url=v.full_text_url, content_type=ContentType.objects.get_for_model(v), object_pk=str(v.id))
        #     l.save()
        # v.reparse_members_from_votes_page(page)
        # v.update_vote_properties()
        # self.find_synced_protocol(v)
