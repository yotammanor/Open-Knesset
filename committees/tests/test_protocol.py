from django.test.testcases import TestCase
from knesset_data.dataservice.committees import CommitteeMeetingProtocol as DataserviceCommitteeMeetingProtocol
import os
from mixins import CommitteesTestsMixin


class TestProtocol(TestCase, CommitteesTestsMixin):

    def test(self):
        protocol_text_filename = os.path.join(os.path.dirname(__file__), 'protocol_text.txt')
        if not os.path.exists(protocol_text_filename):
            with open(protocol_text_filename, 'w') as f:
                with DataserviceCommitteeMeetingProtocol.get_from_url('http://fs.knesset.gov.il//20/Committees/20_ptv_322052.doc') as protocol:
                    f.write(protocol.text.encode('utf-8'))
        with open(protocol_text_filename) as f:
            with DataserviceCommitteeMeetingProtocol.get_from_text(f.read().decode('utf-8')) as protocol:
                meeting = self.get_committee_meeting()
                meeting.protocol_text = protocol.text
                meeting.create_protocol_parts(delete_existing=True)
                self.assertEqual(meeting.parts.all()[139].body[-5:], '12:45')  # meeting adjourned at 12:45
