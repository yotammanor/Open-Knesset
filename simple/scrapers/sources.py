from okscraper.sources import UrlSource
from bs4 import BeautifulSoup, Tag
import datetime


def parse_entry(entry):
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


class KnessetDataServiceSingleEntrySource(UrlSource):

    def __init__(self, service_name, method_name):
        super(KnessetDataServiceSingleEntrySource, self).__init__(
            u'http://online.knesset.gov.il/WsinternetSps/KnessetDataService/{service_name}.svc/{method_name}'.format(service_name=service_name, method_name=method_name)
        )

    def get_source_string(self, id):
        url = super(KnessetDataServiceSingleEntrySource, self).get_source_string()
        return "{url}({id})".format(url=url, id=id)

    def _fetch(self, url):
        soup = BeautifulSoup(super(KnessetDataServiceSingleEntrySource, self)._fetch(url), 'html.parser')
        return parse_entry(soup.entry)


class KnessetDataServiceListSource(UrlSource):

    def __init__(self, service_name, method_name):
        super(KnessetDataServiceListSource, self).__init__(
            u'http://online.knesset.gov.il/WsinternetSps/KnessetDataService/{service_name}.svc/{method_name}'.format(service_name=service_name, method_name=method_name)
        )

    def get_source_string(self, order_by=None, results_per_page=50, page_num=1):
        url = super(KnessetDataServiceListSource, self).get_source_string()
        if isinstance(order_by, (list, tuple)):
            order_by = '%s%%20%s'%order_by
        url += '?$top=%s&$skip=%s'%(results_per_page, (page_num-1)*results_per_page)
        if order_by:
            url += '&$orderby=%s'%order_by
        return url

    def _fetch(self, url):
        soup = BeautifulSoup(super(KnessetDataServiceListSource, self)._fetch(url), 'html.parser')
        if len(soup.feed.find_all('link', attrs={'rel':'next'})) > 0:
            raise Exception('looks like you asked for too much results per page, 50 results per page usually works')
        else:
            return [parse_entry(entry) for entry in soup.feed.find_all('entry')]
