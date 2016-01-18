from okscraper.base import BaseScraper
from simple.scrapers.sources import KnessetDataServiceListSource, KnessetDataServiceSingleEntrySource
from okscraper import storages, sources
import datetime
import locale


def parse_time(value):
    return datetime.datetime.strptime(value, '%H:%M')

def parse_combined_datetime( date_value, time_value):
    return datetime.datetime.combine(date_value.date(), parse_time(time_value).time())

def hebrew_strftime(dt, fmt=u'%A %m %B %Y  %H:%M'):
    locale.setlocale(locale.LC_ALL, 'he_IL.utf8')
    return dt.strftime(fmt).decode('utf8')


class BaseKnessetDataServiceScraper(BaseScraper):

    SERVICE_NAME = None
    METHOD_NAME = None

    def _getSource(self):
        if not (self.SERVICE_NAME and self.METHOD_NAME):
            raise Exception('extending classes must define SERVICE_NAME and METHOD_NAME')
        else:
            return self._getSourceClass()(self.SERVICE_NAME, self.METHOD_NAME)

    def _getSourceClass(self):
        raise Exception('_getSourceClass must be implemented by extending classes')

    def _getStorage(self):
        return storages.DictStorage()

    def __init__(self):
        super(BaseKnessetDataServiceScraper, self).__init__()
        self.source = self._getSource()
        self.storage = storages.DictStorage()

    def _handle_entry(self, entry):
        raise Exception('extending classes must implement _handle_entry and return a value for storage')

    def _scrape(self, *args, **kwargs):
        raise Exception('_scrape must be implemented by exntending classes')


class KnessetDataServiceSingleEntryScraper(BaseKnessetDataServiceScraper):

    def _getSourceClass(self):
        return KnessetDataServiceSingleEntrySource

    def _scrape(self, id):
        self.storage.storeDict({
            'entry': self._handle_entry(self.source.fetch(id))
        })


class KnessetDataServiceListScraper(BaseKnessetDataServiceScraper):

    ORDERBY_FIELD = None

    def _getSourceClass(self):
        return KnessetDataServiceListSource

    def _getOrderBy(self):
        if not self.ORDERBY_FIELD:
            raise Exception('extending classes must define ORDERBY_FIELD')
        else:
            return self.ORDERBY_FIELD, 'desc'

    def _scrape(self, page_num=1):
        entries = []
        for entry in self.source.fetch(order_by=self._getOrderBy(), page_num=page_num):
            entries.append(self._handle_entry(entry))
        self.storage.storeDict({
            'entries': entries
        })


class KnessetDataServiceMultiPageScraper(BaseScraper):
    """
    this scraper iteratively calls a list scraper (based on BaseKnessetDataServiceListScraper)
    it starts from page_num=1 and increments the page_num on each iteration
    each iteration, it checks the list of values returned from the list scraper and counts the number of empty values (see _isEmpty function)
    it then uses the class variables to determine when to stop iterating
    """

    LIST_SCRAPER_CLASS = None
    MAX_ITERATIONS = 10  # when this number of iterations are reached - iterations will stop
    MIN_NUM_OF_EMPTY_TO_STOP = 20  # when this number of empty values or more are detected - the iterations will stop

    def _getScraperClass(self):
        if not self.LIST_SCRAPER_CLASS:
            raise Exception('extending classes must define LIST_SCRAPER_CLASS')
        else:
            return self.LIST_SCRAPER_CLASS

    def _getScraper(self):
        return self._getScraperClass()()

    def _isEmpty(self, val):
        return val is None

    def __init__(self):
        super(KnessetDataServiceMultiPageScraper, self).__init__()
        self.source = sources.ScraperSource(self._getScraper())
        self.storage = storages.DictStorage()

    def _scrape(self, *args, **kwargs):
        all_results = []
        num_of_empty = 0
        page_num = 0
        total_num = 0
        while num_of_empty < self.MIN_NUM_OF_EMPTY_TO_STOP and page_num < self.MAX_ITERATIONS:
            page_num += 1
            self._getLogger().debug('page_num=%s'%page_num)
            values = self.source.fetch(page_num)['entries']
            all_results.append(values)
            num_of_empty = len([val for val in values if self._isEmpty(val)])
            total_num += (len(values)-num_of_empty)
            self._getLogger().debug('num_of_empty=%s'%num_of_empty)
        self._getLogger().info('scraped %s entries, stopped on page %s'%(total_num, page_num))
        self.storage.storeDict({
            'stopped_on_page': page_num,
            'all_results': all_results,
        })
