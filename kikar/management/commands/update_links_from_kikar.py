# coding=utf-8
from django.core.management.base import BaseCommand, CommandError

from optparse import make_option
import requests
from links.models import Link, LinkType
from mks.models import Member

SUCSESS_STATUS_CODE = 200

KIKAR_BASE_URL = 'http://www.kikar.org'
FACEBOOK_LINK_TYPE_TITLE = u'\u05e4\u05d9\u05d9\u05e1\u05d1\u05d5\u05e7'
KIKAR_LINK_TYPE_TITLE = u'\u05db\u05d9\u05db\u05e8 \u05d4\u05de\u05d3\u05d9\u05e0\u05d4'


class Command(BaseCommand):
    args = '<member_id>'
    help = 'Update mks data from source through api'

    option_list = BaseCommand.option_list + (
        make_option('-f',
                    '--force-update',
                    action='store_true',
                    dest='force-update',
                    default=False,
                    help='Force update of member.'),
        make_option('-n',
                    '--noinput',
                    action='store_true',
                    dest='noinput',
                    default=False,
                    help='no input from user requested. runs in safe-mode unless flagged otherwise.'),
    )

    def handle(self, *args, **options):
        """

        """
        members = Member.current_knesset.all()
        kikar_url = KIKAR_BASE_URL + '/api/v1/member/'
        for i, member in enumerate(members):
            print('working on member: {}, {} of {}'.format(member.id, i, len(members)))
            res = requests.get('{}{}'.format(kikar_url, member))
            if res.status_code != SUCSESS_STATUS_CODE:
                print ('bad response satatus code:', res.status_code)
                continue
            res_json = res.json()
            if res_json.get('facebook_link'):
                link_type = LinkType.objects.get(title=FACEBOOK_LINK_TYPE_TITLE)
                link, created = Link.objects.get_or_create(object_pk=member.id, link_type=link_type)
                link.url = res_json.get('facebook_link')
                link.title = u'{} ב{}'.format(member.name, link_type.title)
                link.active = True
                link.save()
            if res_json.get('kikar_link'):
                link_type, created = LinkType.objects.get_or_create(title=KIKAR_LINK_TYPE_TITLE)
                if created:  # Assuming it was added manually.
                    continue
                link, created = Link.objects.get_or_create(object_pk=member.id, link_type=link_type)
                link.url = res_json.get('kikar_link')
                link.title = u'{} ב{}'.format(member.name, link_type.title)
                link.active = True
                link.save()
        print('done.')
