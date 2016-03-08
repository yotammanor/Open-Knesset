from django.core.management.base import NoArgsCommand
from logging import getLogger
from mks.models import Member
from django.core.cache import cache
logger = getLogger(__name__)


class Command(NoArgsCommand):
    help = "Recalculates bill statistics for mks of current knesset"
    info_types = ['bills_proposed', 'bills_pre', 'bills_approved', 'bills_first']


    def handle_noargs(self, **options):
        for mk in Member.objects.all(is_current=True):
            logger.info('Recalculate bill statistics For mk: {0}'.format(mk.name))
            mk.recalc_bill_statistics()

        self._invalidate_cache()

    def _invalidate_cache(self):
        for info_type in self.info_types:
            if cache.get('object_list_by_%s' % info_type):
                cache.delete('object_list_by_%s' % info_type)
