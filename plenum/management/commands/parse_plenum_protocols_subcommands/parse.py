# encoding: utf-8
from django.db.models import Count
from committees.models import Committee, CommitteeMeeting
from plenum import create_protocol_parts
import logging

def Parse(reparse, logger, meeting_pks=None):
    logger.debug('Parse (reparse=%s, meeting_pks=%s)'%(reparse, meeting_pks))
    if meeting_pks is not None:
        meetings = CommitteeMeeting.objects.filter(pk__in=meeting_pks)
    else:
        plenum=Committee.objects.filter(type='plenum')[0]
        meetings=CommitteeMeeting.objects.filter(committee=plenum).exclude(protocol_text='')
    (mks,mk_names)=create_protocol_parts.get_all_mk_names()
    logger.debug('got mk names: %s, %s'%(mks, mk_names))
    for meeting in meetings:
        if reparse or meeting.parts.count() == 0:
            logger.debug('creating protocol parts for meeting %s'%(meeting,))
            meeting.create_protocol_parts(delete_existing=reparse,mks=mks,mk_names=mk_names)

def parse_for_existing_meeting(meeting):
    logger = logging.getLogger('open-knesset')
    Parse(True, logger, [meeting.pk])
