# encoding: utf-8
from functools import partial
from optparse import make_option

from django.db.models import Q
from django.utils.timezone import now, timedelta

from committees.models import CommitteeMeeting, Committee
from knesset_data.dataservice.committees import CommitteeMeeting as DataserviceCommitteeMeeting
from mks.utils import get_all_mk_names
from simple.scrapers import hebrew_strftime
from simple.scrapers.management import BaseKnessetDataserviceCommand

ERR_MSG = 'failed to get meetings for committee {}'

ERR_MSG_REPORT = 'Unexpected exception received while trying to get meetings of committee {}: {}'

_DS_TO_APP_KEY_MAPPING = (
    ('date_string', 'datetime'),
    ('date', 'datetime'),
    ('topics', 'title'),
    ('datetime', 'datetime'),
    ('knesset_id', 'id'),
    ('src_url', 'url')
)

_DS_CONVERSIONS = {
    'date_string': partial(hebrew_strftime, fmt=u'%d/%m/%Y')
}


class Command(BaseKnessetDataserviceCommand):
    help = "Scrape latest committee meetings data from the knesset"

    _DS_TO_APP_KEY_MAPPING = _DS_TO_APP_KEY_MAPPING
    _DS_CONVERSIONS = _DS_CONVERSIONS

    option_list = BaseKnessetDataserviceCommand.option_list + (
        make_option('--from_days', dest='fromdays', default=5, type=int,
                    help="scrape meetings with dates from today minus X days"),
        make_option('--to_days', dest='todays', default=0, type=int,
                    help="scrape meetings with dates until today minus X days"),
    )

    @staticmethod
    def _reparse_protocol(meeting):
        mks, mk_names = get_all_mk_names()
        meeting.reparse_protocol(mks=mks, mk_names=mk_names)

    def _create_object(self, dataservice_meeting, committee):
        meeting_transformed = dict(self._translate_ds_to_model(dataservice_meeting))
        meeting = CommitteeMeeting.objects.create(committee=committee, **meeting_transformed)
        self._log_info('creating meeting %s'%meeting.pk)
        self._reparse_protocol(meeting)
        return meeting

    def _has_existing_object(self, ds_meeting):
        # if we find meetings for the same committee on same date - we assume meeting already exists
        # this case is mostly for old meetings that we don't have their knesset id - so we want to
        # prevent duplicate meetings
        qs = CommitteeMeeting.objects.filter(
            Q(knesset_id=ds_meeting.id) | Q(date=ds_meeting.datetime),
            committee__knesset_id=ds_meeting.committee_id
        )
        return bool(qs)

    def _update_meetings(self, committee, ds_meeting):
        if not ds_meeting.url:
            self._log_debug(u'Meeting {} lacks URL'.format(ds_meeting.id))
            return
        if self._has_existing_object(ds_meeting):
            self._log_debug(u'Meeting {} exists in DB'.format(ds_meeting.id))
            return

        self._log_debug(u'Creating meeting {}'.format(ds_meeting.id))
        self._create_object(ds_meeting, committee)

    def _get_meetings(self, committee_id, from_date, to_date):
        try:
            meetings = DataserviceCommitteeMeeting.get(committee_id, from_date, to_date)
            return meetings
        except Exception as e:
            err_msg = ERR_MSG.format(committee_id)
            err_msg_report = ERR_MSG_REPORT.format(committee_id, str(e))
            DataserviceCommitteeMeeting.error_report(err_msg, err_msg_report)
            self._log_error(err_msg)

        return []

    @staticmethod
    def _extract_cmd_args(from_days, to_days):
        from_date = now() - timedelta(days=from_days)
        to_date = now() - timedelta(days=to_days) if to_days else now()
        return from_date, to_date

    def _handle_noargs(self, **options):
        from_date, to_date = self._extract_cmd_args(options['fromdays'], options['todays'])
        self._log_info('Scraping from {} to {}'.format(from_date, to_date))

        # filter is used to discard plenum and invalid knesset_id's
        for committee in Committee.objects.filter(knesset_id__gt=0):
            c_name, c_knesset_id = committee.name, committee.knesset_id

            self._log_info(u'Processing {} committee (knesset ID {})'.format(c_name, c_knesset_id))
            for ds_meeting in self._get_meetings(c_knesset_id, from_date, to_date):
                self._update_meetings(committee, ds_meeting)
