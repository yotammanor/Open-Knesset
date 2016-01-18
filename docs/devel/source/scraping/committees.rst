==========
Committees
==========

protocols
---------

./manage.py okscrape committees CommitteeMeetingsMultiPageScraper

accesses the knesset data service API to get latest commitee meetings, also updated committee details it encounters


old / html scrapers
-------------------

Following details the old scrapers which access the html instead of knesset API, they might still be in use, as we are in the process of transioning to the API scrapers

committee protocols data is scraped as part of syncdata --update cronjob

if you want to only run the protocols scraping you can use "manage.py syncdata --update --update-run-only=get_protocols -v3"

the scraper first goes to: http://www.knesset.gov.il/protocols/heb/protocol_search.aspx

it does a search for all protocols since 2009, and only those with protocols

then, it goes over 10 pages of the search result, for each result it processes all the protocols