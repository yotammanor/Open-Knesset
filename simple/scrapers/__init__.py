from okscraper.base import BaseScraper
from simple.scrapers.sources import KnessetDataServiceListSource, KnessetDataServiceSingleEntrySource
from okscraper import storages, sources
import datetime
import locale


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
        raise Exception('_getStorage must be implemented by extending classes')

    def __init__(self):
        super(BaseKnessetDataServiceScraper, self).__init__()
        self.source = self._getSource()
        self.storage = self._getStorage()

    def _handle_entry(self, entry):
        raise Exception('extending classes must implement _handle_entry and return a value for storage')

    def _scrape(self, *args, **kwargs):
        raise Exception('_scrape must be implemented by exntending classes')

    ## utility functions - useful in _handle_entry

    def _parse_time(self, value):
        return datetime.datetime.strptime(value, '%H:%M')

    def _parse_combined_datetime(self, date_value, time_value):
        return datetime.datetime.combine(date_value.date(), self._parse_time(time_value).time())

    def _hebrew_strftime(self, dt, fmt=u'%A %m %B %Y  %H:%M'):
        locale.setlocale(locale.LC_ALL, 'he_IL.utf8')
        return dt.strftime(fmt).decode('utf8')


class BaseKnessetDataServiceDictScraper(BaseKnessetDataServiceScraper):

    def _getSourceClass(self):
        return KnessetDataServiceSingleEntrySource

    def _getStorage(self):
        return storages.DictStorage()

    def _scrape(self, id):
        self.storage.storeDict(self._handle_entry(self.source.fetch(entry_id=id)))


class BaseKnessetDataServiceListScraper(BaseKnessetDataServiceScraper):

    ORDERBY_FIELD = None

    def _getSourceClass(self):
        return KnessetDataServiceListSource

    def _getStorage(self):
        return storages.ListStorage()

    def _getOrderBy(self):
        if not self.ORDERBY_FIELD:
            raise Exception('extending classes must define ORDERBY_FIELD')
        else:
            return self.ORDERBY_FIELD, 'desc'

    def _scrape(self, page_num=1):
        for entry in self.source.fetch(order_by=self._getOrderBy(), page_num=page_num):
            self.storage.store(self._handle_entry(entry))


class BaseKnessetDataServiceMultiPageScraper(BaseScraper):
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
        super(BaseKnessetDataServiceMultiPageScraper, self).__init__()
        self.source = sources.ScraperSource(self._getScraper())
        self.storage = storages.DictStorage()

    def _scrape(self, *args, **kwargs):
        all_results = []
        num_of_empty = 0
        page_num = 0
        while num_of_empty < self.MIN_NUM_OF_EMPTY_TO_STOP and page_num < self.MAX_ITERATIONS:
            page_num += 1
            self._getLogger().debug('page_num=%s'%page_num)
            values = self.source.fetch(page_num)
            all_results.append(values)
            num_of_empty = len([val for val in values if self._isEmpty(val)])
            self._getLogger().debug('num_of_empty=%s'%num_of_empty)
        self._getLogger().debug('stopped on page %s'%page_num)
        self.storage.storeDict({
            'stopped_on_page': page_num,
            'all_results': all_results,
        })
