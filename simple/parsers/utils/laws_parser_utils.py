# -*- coding: utf-8 -*
import re


def normalize_correction_title_dashes(raw_title):
    """returns s with normalized spaces before and after the dash"""
    if not raw_title:
        return None
    m = re.match(r'(תיקון)( ?)(-)( ?)(.*)'.decode('utf8'), raw_title)
    if not m:
        return raw_title
    return ' '.join(m.groups()[0:5:2])


def parse_title(unparsed_title):
    return re.match(u'הצע[תה] ([^\(,]*)(.*?\((.*?)\))?(.*?\((.*?)\))?(.*?,(.*))?', unparsed_title)


def clean_line(a_line_str):
    return a_line_str.strip().replace('\n', '').replace('&nbsp;', ' ')
