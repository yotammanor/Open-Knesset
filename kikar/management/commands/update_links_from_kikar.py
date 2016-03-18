# coding=utf-8
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError

from optparse import make_option
import requests
from links.models import Link, LinkType
from mks.models import Member, Party

SUCSESS_STATUS_CODE = 200

KIKAR_BASE_URL = 'http://www.kikar.org'
FACEBOOK_LINK_TYPE_TITLE = u'\u05e4\u05d9\u05d9\u05e1\u05d1\u05d5\u05e7'
KIKAR_LINK_TYPE_TITLE = u'\u05db\u05d9\u05db\u05e8 \u05d4\u05de\u05d3\u05d9\u05e0\u05d4'


class Command(BaseCommand):
    help = 'Update mks data from source through api'

    option_list = BaseCommand.option_list + (
        make_option('-p',
                    '--exclude-parties',
                    action='store_true',
                    dest='exclude_parties',
                    default=False,
                    help='Exclude update of parties.'),
        make_option('-m',
                    '--exclude-members',
                    action='store_true',
                    dest='exclude_members',
                    default=False,
                    help='Exclude update of members.'),
    )

    def update_for_model(self, obj, kikar_url):
        res = requests.get('{}{}'.format(kikar_url, obj.id))
        if res.status_code != SUCSESS_STATUS_CODE:
            print ('bad response satatus code:', res.status_code)
            return False
        res_json = res.json()
        if res_json.get('facebook_link'):
            link_type = LinkType.objects.get(title=FACEBOOK_LINK_TYPE_TITLE)
            link, created = Link.objects.get_or_create(object_pk=obj.id, link_type=link_type,
                                                       content_type=ContentType.objects.get_for_model(obj))
            link.url = res_json.get('facebook_link')
            link.title = u'{} ב{}'.format(obj.name, link_type.title)
            link.active = True
            link.save()
        if res_json.get('kikar_link'):
            link_type, created = LinkType.objects.get_or_create(title=KIKAR_LINK_TYPE_TITLE)
            if created:  # Assuming it was added manually.
                return False
            link, created = Link.objects.get_or_create(object_pk=obj.id, link_type=link_type,
                                                       content_type=ContentType.objects.get_for_model(obj))
            link.url = res_json.get('kikar_link')
            link.title = u'{} ב{}'.format(obj.name, link_type.title)
            link.active = True
            link.save()

    def handle(self, *args, **options):
        """
        main function of this script - iterates over all current Knesset's Members and parties,
        and updates from kikar.org data the current facebook link and kikar link for given object.

        Assumes that a LinkType for kikar and facebook pre-exists.
        """

        if not options['exclude_members']:
            print ('working on MKs.')
            members = Member.current_knesset.all()
            kikar_url = KIKAR_BASE_URL + '/api/v1/member/'
            for i, member in enumerate(members):
                print('working on member: {}, {} of {}'.format(member.id, i + 1, len(members)))
                self.update_for_model(member, kikar_url)
        else:
            print ('Skipping MKs.')

        if not options['exclude_parties']:
            print ('working on Parties.')
            parties = Party.current_knesset.all()
            kikar_url = KIKAR_BASE_URL + '/api/v1/party/'
            for i, party in enumerate(parties):
                print('working on party: {}, {} of {}'.format(party.id, i + 1, len(parties)))
                self.update_for_model(party, kikar_url)
        else:
            print ('Skipping Parties.')

        print('done.')
