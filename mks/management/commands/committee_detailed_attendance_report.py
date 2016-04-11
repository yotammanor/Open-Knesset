from collections import namedtuple

from django.core.management.base import NoArgsCommand
from logging import getLogger

from knesset.technical_services.csv_writer import UnicodeCsvWriter
from mks.models import Member

logger = getLogger(__name__)

MemberCommitteeAttendance = namedtuple('committee_detailed_attendance',
                                       ['mk_pk', 'mk_name', 'committee', 'is_current', 'current_party', 'total_count',
                                        ])


class Command(NoArgsCommand):
    help = "Get a csv report for committee attendance for current knesset"

    def handle_noargs(self, **options):
        csv_writer = UnicodeCsvWriter()
        report_data = [
            ['mk_pk', 'mk_name', 'committee', 'is_current', 'current_party', 'total_count']]
        for mk in Member.current_knesset.all():
            member_committees = mk.participated_in_committees_for_current_knesset
            for committee in member_committees:
                mk_attendance = MemberCommitteeAttendance(mk_pk=mk.pk, mk_name=mk.name, is_current=mk.is_current,
                                                          current_party=mk.current_party.name,
                                                          committee=committee,
                                                          total_count=mk.total_meetings_count_for_committee(committee))

                logger.info(u'attendance for {0} {1}'.format(mk.pk, mk.name))
                report_data.append(mk_attendance)

        csv_writer.write(report_data, 'detailed_attendance_report.csv', mode='w')
