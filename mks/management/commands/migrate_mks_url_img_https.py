import urllib2, re, logging

from django.core.management.base import NoArgsCommand

from mks.models import Member

logger = logging.getLogger("open-knesset.mks.update_mks_url_img")


class Command(NoArgsCommand):
    help = "update all members url_img to https"

    def handle_noargs(self, **options):
        for member in Member.objects.all():
            if member.img_url and not member.img_url.startswith('https'):
                member.img_url = member.img_url.replace('http', 'https')
                member.save()
