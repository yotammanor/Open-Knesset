# encoding: utf-8
from knesset_data.dataservice.committees import CommitteeMeeting as DataserviceCommitteeMeeting, Committee as DataserviceCommittee
from committees.models import CommitteeMeeting, Committee
from simple.scrapers import hebrew_strftime
from mks.utils import get_all_mk_names
from simple.scrapers.management import BaseKnessetDataserviceCommand
from django.utils.timezone import now, timedelta
from optparse import make_option


def get_committee(id):
    qs = Committee.objects.filter(knesset_id=id)
    if qs.count() > 0:
        return qs.first()
    else:
        dataservice_committee = DataserviceCommittee.get(id)
        qs = Committee.objects.filter(name=dataservice_committee.name)
        if qs.count() > 0:
            qs.update(knesset_id=id)
            return qs.first()
        else:
            return Committee.objects.create(
                name=dataservice_committee.name, knesset_id=dataservice_committee.id, hide=True,
                knesset_type_id = dataservice_committee.type_id,
                knesset_parent_id = dataservice_committee.parent_id,
                name_eng = dataservice_committee.name_eng,
                name_arb = dataservice_committee.name_arb,
                start_date = dataservice_committee.begin_date,
                end_date = dataservice_committee.end_date,
                knesset_description = dataservice_committee.description,
                knesset_description_eng = dataservice_committee.description_eng,
                knesset_description_arb = dataservice_committee.description_arb,
                knesset_note = dataservice_committee.note,
                knesset_note_eng = dataservice_committee.note_eng,
                knesset_portal_link = dataservice_committee.portal_link,
            )


class Command(BaseKnessetDataserviceCommand):

    DATASERVICE_CLASS = DataserviceCommitteeMeeting

    option_list = BaseKnessetDataserviceCommand.option_list + (
        make_option('--from_days', dest='fromdays', default='5', help="scrape meetings with dates from today minus X days"),
        make_option('--to_days', dest='todays', default='0', help="scrape meetings with dates until today minut X days"),
    )

    help = "Scrape latest votes data from the knesset"

    def _has_existing_object(self, dataservice_meeting):
        has_meeting = False
        qs = CommitteeMeeting.objects.filter(knesset_id=dataservice_meeting.id, committee__knesset_id=dataservice_meeting.committee_id)
        if qs.count() > 0:
            has_meeting = True
        else:
            # couldn't find meeting by id, let's try by date
            # if we find meetings for the same committee on same date - we assume meeting already exists
            # this case is mostly for old meetings that we don't have their knesset id - so we want to prevent duplicate meetings
            qs = CommitteeMeeting.objects.filter(date=dataservice_meeting.datetime, committee__knesset_id=dataservice_meeting.committee_id)
            if qs.count() > 0:
                has_meeting = True
        return has_meeting

    def _create_new_object(self, dataservice_meeting):
        meeting = CommitteeMeeting.objects.create(
            committee=get_committee(dataservice_meeting.committee_id),
            date_string=hebrew_strftime(dataservice_meeting.datetime, u'%d/%m/%Y'),
            date=dataservice_meeting.datetime,
            topics=dataservice_meeting.title,
            datetime=dataservice_meeting.datetime,
            knesset_id=dataservice_meeting.id,
            src_url=dataservice_meeting.url,
        )
        meeting.reparse_protocol(mks=self.mks, mk_names=self.mk_names)
        return meeting

    def __init__(self):
        super(Command, self).__init__()
        self.mks, self.mk_names = get_all_mk_names()

    def _get_committee_knesset_ids(self):
        return [c.id for c in DataserviceCommittee.get_all_active_committees()]

    def _handle_noargs(self, **options):
        from_date = now()-timedelta(days=int(options['fromdays']))
        to_date = now()-timedelta(days=int(options['todays'])) if int(options['todays']) > 0 else now()
        self._log_info('scraping from %s to %s'%(from_date, to_date))
        for committee_src_id in self._get_committee_knesset_ids():
            self._log_info('processing committee id %s'%committee_src_id)
            meetings = []
            try:
                meetings = DataserviceCommitteeMeeting.get(committee_src_id, from_date, to_date)
            except Exception, e:
                DataserviceCommitteeMeeting.error_report(
                    "failed to get meetings for committee %s"%committee_src_id,
                    "Unexpected exception received while trying to get meetings of committee %s: %s"%(committee_src_id, str(e))
                )
                self._log_error('failed to get meetings for committee %s'%committee_src_id)
            for dataservice_meeting in meetings:
                if dataservice_meeting.url and not self._has_existing_object(dataservice_meeting):
                    self._log_debug('creating meeting %s'%dataservice_meeting.id)
                    meeting = self._create_new_object(dataservice_meeting)
                    self._log_debug('created meeting %s - %s'%(meeting.pk, meeting))
