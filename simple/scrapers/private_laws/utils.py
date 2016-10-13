# -*- coding: utf-8 -*
import re


def parse_title(unparsed_title):
    return re.match(u'הצעת ([^\(,]*)(.*?\((.*?)\))?(.*?\((.*?)\))?(.*?,(.*))?', unparsed_title)


def clean_line(a_line_str):
    return a_line_str.strip().replace('\n', '').replace('&nbsp;', ' ')