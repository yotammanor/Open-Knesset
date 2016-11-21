# -*- coding: utf-8 -*
from laws.enums import VOTE_TYPES


def resolve_vote_type_by_title(title):
    if type(title) == str:
        transform_func = str.decode
    else:  # its already unicode, do nothing
        transform_func = lambda x, y: x
    for vtype, vtype_prefix in VOTE_TYPES.items():
        if transform_func(title, 'utf8').startswith(vtype_prefix):
            return vtype
    return ''


class MissingVotePartyException(Exception):
    pass


def party_at_or_error(member, vote_date, vote_id):
    party = member.party_at(vote_date)
    if party:
        return party
    else:
        raise MissingVotePartyException(
            'could not find which party member %s belonged to during vote %s' % (member.pk, vote_id))