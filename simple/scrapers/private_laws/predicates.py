# -*- coding: utf-8 -*
import re


def proposal_has_joiners(name_str):
    return re.search('ONMOUSEOUT', name_str) > 0