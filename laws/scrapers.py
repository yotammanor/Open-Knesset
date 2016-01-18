# encoding: utf-8
from okscraper.base import BaseScraper
from okscraper import sources
from okscraper import storages
from laws.models import Vote
from simple import scrapers


class VoteScraperHtml(BaseScraper):
    """
    scrapes the html page of a specific vote
    hopefully, we won't need to use this and get everything from API..
    """

    def __init__(self):
        super(VoteScraperHtml, self).__init__()
        self.source = sources.UrlSource('http://www.knesset.gov.il/vote/heb/Vote_Res_Map.asp?vote_id_t=<<vote_src_id>>')
        self.storage = storages.DictStorage()

    def _scrape(self, vote_src_id):
        page = self.source.fetch(vote_src_id)
        # TODO: scrape some data we can only get from html..
        self.storage.store('page', page)


class VotesScraper(scrapers.KnessetDataServiceListScraper):

    SERVICE_NAME = "VotesData"
    METHOD_NAME = "View_vote_rslts_hdr_Approved"
    ORDERBY_FIELD = "vote_id"

    def _handle_entry(self, entry):
        data = entry['data']
        vote_id = data['vote_id']
        vote_label = u'{vote} - {sess}'.format(vote=data['vote_item_dscr'], sess=data['sess_item_dscr'])
        vote_meeting_num = data['session_num']
        vote_num = data['vote_nbr_in_sess']
        vote_datetime = scrapers.parse_combined_datetime(data['vote_date'], data['vote_time'])
        vote_datetime_string = u'יום '+scrapers.hebrew_strftime(vote_datetime)
        v, created = Vote.objects.get_or_create(src_id=vote_id, defaults={
            'title': vote_label, 'time_string': vote_datetime_string, 'importance': 1, 'time': vote_datetime,
            'meeting_number': vote_meeting_num, 'vote_number': vote_num, 'src_url': entry['id']
        })

        # TODO: find the related data for the vote, preferably from API
        # TODO: here, we reparse the votes, so we should probably limit the parser according to last time we accessed this vote or something like that
        # if v.full_text_url != None:
        #     l = Link(title=u'מסמך הצעת החוק באתר הכנסת', url=v.full_text_url, content_type=ContentType.objects.get_for_model(v), object_pk=str(v.id))
        #     l.save()
        # v.reparse_members_from_votes_page(page)
        # v.update_vote_properties()
        # self.find_synced_protocol(v)

        return v
