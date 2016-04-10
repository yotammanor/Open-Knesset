from collections import namedtuple

from django.core.management.base import NoArgsCommand
from logging import getLogger

from knesset.technical_services.csv_writer import UnicodeCsvWriter
from mks.models import Member

logger = getLogger(__name__)

MemberAttendance = namedtuple('committee_attendance',
                              ['mk_pk', 'mk_name', 'is_current', 'current_party', 'total_count', 'monthly_average'])


class Command(NoArgsCommand):
    help = "Get a csv report for committee attendance for current knesset"

    def handle_noargs(self, **options):
        csv_writer = UnicodeCsvWriter()
        report_data = [['mk_pk', 'mk_name', 'is_current', 'current_party', 'total_count', 'monthly_average']]
        for mk in Member.current_knesset.all():
            mk_attendance = MemberAttendance(mk_pk=mk.pk, mk_name=mk.name, is_current=mk.is_current,
                                             current_party=mk.current_party.name,
                                             total_count=mk.committee_meeting_count_current_knesset,
                                             monthly_average=mk.committee_meetings_per_month())

            logger.info(u'attendance for {0} {1}'.format(mk.pk, mk.name))
            report_data.append(mk_attendance)

        csv_writer.write(report_data, 'attendance_report.csv', mode='w')




        #     self._invalidate_cache()
        #
        # def _invalidate_cache(self):
        #     for info_type in self.info_types:
        #         if cache.get('object_list_by_%s' % info_type):
        #             cache.delete('object_list_by_%s' % info_type)
