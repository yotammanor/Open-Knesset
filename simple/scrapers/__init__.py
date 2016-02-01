import locale


def hebrew_strftime(dt, fmt=u'%A %m %B %Y  %H:%M'):
    locale.setlocale(locale.LC_ALL, 'he_IL.utf8')
    return dt.strftime(fmt).decode('utf8')
