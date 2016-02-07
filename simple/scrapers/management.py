# encoding: utf-8
from okscraper_django.management.base_commands import NoArgsDbLogCommand
from optparse import make_option


class BaseKnessetDataserviceCommand(NoArgsDbLogCommand):

    DATASERVICE_CLASS = None

    def _has_existing_object(self, dataservice_object):
        raise NotImplementedError()

    def _create_new_object(self, dataservice_object):
        raise NotImplementedError()



class BaseKnessetDataserviceCollectionCommand(BaseKnessetDataserviceCommand):

    option_list = BaseKnessetDataserviceCommand.option_list + (
        make_option('--page-range', dest='pagerange', default='1-10', help="range of page number to scrape (e.g. --page-range=5-12), default is 1-10"),
    )

    def _handle_page(self, page_num):
        for dataservice_object in self.DATASERVICE_CLASS.get_page(page_num=page_num):
            if not self._has_existing_object(dataservice_object):
                object = self._create_new_object(dataservice_object)
                self._log_debug(u'created new %s'%object)

    def _handle_noargs(self, **options):
        page_range = options['pagerange']
        first, last = map(int, page_range.split('-'))
        for page_num in range(first, last+1):
            self._log_debug('page %s'%page_num)
            self._handle_page(page_num)
