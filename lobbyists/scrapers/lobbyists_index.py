# encoding: utf-8

from bs4 import BeautifulSoup
from okscraper.base import BaseScraper
from okscraper.sources import UrlSource, ScraperSource
from okscraper.storages import ListStorage, DictStorage
from lobbyists.models import LobbyistHistory, Lobbyist, LobbyistData, LobbyistRepresent, LobbyistRepresentData
from persons.models import Person
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime
from knesset.utils import send_chat_notification


class LobbyistsIndexScraper(BaseScraper):
    """
    This scraper gets the list of lobbyist ids from the knesset lobbyists page html
    returns a list of lobbyist ids - doesn't store anything in db
    """
    LOBBYISTS_INDEX_PAGE_URL = 'http://www.knesset.gov.il/lobbyist/heb/lobbyist.aspx'

    def __init__(self):
        super(LobbyistsIndexScraper, self).__init__(self)
        self.source = UrlSource(self.LOBBYISTS_INDEX_PAGE_URL)
        self.storage = ListStorage()

    def _storeLobbyistIdsFromSoup(self, soup):
        elts = soup.findAll(lobbyist_id=True)
        counter = 0
        for elt in elts:
            lobbyist_id = elt.get('lobbyist_id')
            if lobbyist_id.isdigit():
                self.storage.store(lobbyist_id)
                self._getLogger().debug(lobbyist_id)
                counter = counter + 1
        self._getLogger().info('got %s lobbyists', str(counter))

    def _scrape(self):
        try:
            html = self.source.fetch()
            soup = BeautifulSoup(html)
        except Exception, e:
            send_chat_notification(__file__, 'failed to fetch or parse the lobbyists index page', {'url': self.LOBBYISTS_INDEX_PAGE_URL})
            raise e
        return self._storeLobbyistIdsFromSoup(soup)
