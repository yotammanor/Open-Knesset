import datetime


def date_to_datetime(start_date):
    if start_date:
        timetuple = start_date.timetuple()
        return datetime.datetime(year=timetuple[0], month=timetuple[1], day=timetuple[2])


TRACKBACK_CONTENT_TYPE = 'application/x-www-form-urlencoded; charset=utf-8'
just_id = lambda x: x.id
ten_days_ago = datetime.datetime.today() - datetime.timedelta(days=10)
two_days_ago = datetime.datetime.today() - datetime.timedelta(days=2)