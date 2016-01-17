from okscraper.sources import UrlSource
from bs4 import BeautifulSoup, Tag
import datetime


class BaseKnessetDataServiceSource(UrlSource):
    """
    base class for the knesset data service

    you probably want to use either KnessetDataServiceSingleEntrySource or KnessetDataServiceListSource instead
    """

    def __init__(self, service_name, method_name):
        super(BaseKnessetDataServiceSource, self).__init__(
            u'http://online.knesset.gov.il/WsinternetSps/KnessetDataService/{service_name}.svc/{method_name}'.format(service_name=service_name, method_name=method_name)
        )

    def _parse_entry(self, entry):
        entry_id = entry.id.string
        entry_links = []
        for link in entry.find_all('link'):
            entry_links.append({'href': link.attrs['href'], 'rel': link.attrs['rel'][0], 'title': link.attrs['title']})
        data = {}
        for prop in entry.content.find('m:properties').children:
            if isinstance(prop, Tag):
                prop_tagtype, prop_name = prop.name.split(':')
                prop_type = prop.attrs.get('m:type', '')
                prop_null = (prop.attrs.get('m:null', '') == 'true')
                if prop_null:
                    prop_val = None
                elif prop_type == '':
                    prop_val = prop.string
                elif prop_type in ('Edm.Int32', 'Edm.Int16', 'Edm.Byte'):
                    prop_val = int(prop.string)
                elif prop_type == 'Edm.Decimal':
                    prop_val = float(prop.string)
                elif prop_type == 'Edm.DateTime':
                    prop_val = datetime.datetime.strptime(prop.string, "%Y-%m-%dT%H:%M:%S")
                else:
                    raise Exception('unknown prop type: %s'%prop_type)
                data[prop_name] = prop_val
        return {
            'id': entry_id,
            'links': entry_links,
            'data': data,
        }

    def _get_soup(self, page):
        return BeautifulSoup(page, 'html.parser')


class KnessetDataServiceSingleEntrySource(BaseKnessetDataServiceSource):
    """
    okscraper source for the knesset data service - for a single entry

    list of available services can be found here: http://online.knesset.gov.il/WsinternetSps/KnessetDataService/
    If you enter into a service you can see the list of methods (in the href attribute)

    This source accepts a single require parameter:
        entry_id:
            the id of an entry form the service/method which you want to retrieve
    """

    def get_source_string(self, entry_id):
        return "{url}({entry_id})".format(
            url=super(KnessetDataServiceSingleEntrySource, self).get_source_string(),
            entry_id=entry_id
        )

    def _fetch(self, url):
        soup = self._get_soup(super(KnessetDataServiceSingleEntrySource, self)._fetch(url))
        return self._parse_entry(soup.entry)


class KnessetDataServiceListSource(BaseKnessetDataServiceSource):
    """
    okscraper source for the knesset data service - for a list of entries

    list of available services can be found here: http://online.knesset.gov.il/WsinternetSps/KnessetDataService/
    If you enter into a service you can see the list of methods (in the href attribute)

    This source accepts the following parameters:
        order_by:
            either the name of the field to order by ascending
            or a tuple containing for example ('vote_id', 'desc') if you want descending
        results_per_page:
            default = 50 (pay attention that if you ask more then 50 knesset might ignore that request
        page_num:
            deafult = 1 (first page)
    """

    def get_source_string(self, order_by=None, results_per_page=50, page_num=1):
        url = super(KnessetDataServiceListSource, self).get_source_string()
        if isinstance(order_by, (list, tuple)):
            order_by = '%s%%20%s'%order_by
        url += '?$top=%s&$skip=%s'%(results_per_page, (page_num-1)*results_per_page)
        if order_by:
            url += '&$orderby=%s'%order_by
        return url

    def _fetch(self, url):
        soup = self._get_soup(super(KnessetDataServiceListSource, self)._fetch(url))
        if len(soup.feed.find_all('link', attrs={'rel':'next'})) > 0:
            raise Exception('looks like you asked for too much results per page, 50 results per page usually works')
        else:
            return [self._parse_entry(entry) for entry in soup.feed.find_all('entry')]
