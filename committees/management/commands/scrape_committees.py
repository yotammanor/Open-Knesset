# encoding: utf-8

from committees.models import Committee
from knesset_data.dataservice.committees import Committee as DataserviceCommittee
from simple.scrapers.management import BaseKnessetDataserviceCommand

_ds_to_app_key_mapping = (
    ('name', 'name'),
    ('knesset_id', 'id'),
    ('knesset_type_id', 'type_id'),
    ('knesset_parent_id', 'parent_id'),
    ('name_eng', 'name_eng'),
    ('name_arb', 'name_arb'),
    ('start_date', 'begin_date'),
    ('end_date', 'end_date'),
    ('knesset_description', 'description'),
    ('knesset_description_eng', 'description_eng'),
    ('knesset_description_arb', 'description_arb'),
    ('knesset_note', 'note'),
    ('knesset_note_eng', 'note_eng'),
    ('knesset_portal_link', 'portal_link')
)


def _translate_ds_to_model_keys(ds_committee):
    return {model_key: getattr(ds_committee, ds_key) for model_key, ds_key in
            _ds_to_app_key_mapping}


class Command(BaseKnessetDataserviceCommand):
    def _update_or_create(self, fetched_committee):
        """
        If the committee exist merge, and update else create a new entry

        :param fetched_committee: the fetched Committee details
        :return:
        """
        committee = Committee.objects.filter(knesset_id=fetched_committee['knesset_id'])
        if committee:
            self._log_debug(u'Committee {} exist, updating'.format(fetched_committee['name']))
            committee.update(**fetched_committee)
        else:
            self._log_debug(u"Committee {} don't exist, updating".format(fetched_committee['name']))
            Committee.objects.create(**fetched_committee)

    def _update_active_committees(self):
        for ds_committee in DataserviceCommittee.get_all_active_committees():
            committee = _translate_ds_to_model_keys(ds_committee)
            self._update_or_create(committee)

    def _handle_noargs(self, **options):
        self._update_active_committees()
