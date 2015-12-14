# encoding: utf-8
from okscraper.base import BaseScraper
from okscraper import sources
from okscraper import storages


class VoteScraper(BaseScraper):

    def __init__(self):
        super(VoteScraper, self).__init__()
        self.source = sources.UrlSource('http://www.knesset.gov.il/vote/heb/Vote_Res_Map.asp?vote_id_t=<<vote_src_id>>')
        self.storage = storages.DictStorage()

    def _scrape(self, vote_src_id):
        page = self.source.fetch(vote_src_id)
        from simple.management.commands.syncdata import Command
        syncdata = Command()
        title = syncdata.get_page_title(page)
        if(title == """הצבעות במליאה-חיפוש"""): # found no vote with this id
            self._getLogger().debug("no vote found at id %d" % vote_src_id)
        else:
            syncdata.update_vote_from_page(vote_src_id, self.source.get_source_string(vote_src_id), page)
