# Copyright (c) 2017 App Annie Inc. All rights reserved.

import datetime
import time

import iso8601
import pytz

STD_TIMEZONE = pytz.timezone('US/Pacific')
ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%f%z"
YYYY_MM_DD = "%Y-%m-%d"


def current_date(utc=True):
    cd = current_datetime(utc)
    return datetime.date(cd.year, cd.month, cd.day)


def current_datetime(utc=True):
    if utc:
        cd = datetime.datetime.utcfromtimestamp(time.time())
    else:
        cd = datetime.datetime.now(STD_TIMEZONE)
    return cd


def utc_to_local(utc_dt, local_tz):
    local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
    return local_tz.normalize(local_dt)  # .normalize might be unnecessary


def local_to_utc(local_dt, local_tz):
    local_dt = local_tz.localize(local_dt, is_dst=None)
    return local_dt.astimezone(pytz.utc)


def to_timestamp(dt, utc=True, tz=STD_TIMEZONE):
    if not utc:
        dt = local_to_utc(dt, tz)
    return (dt - datetime.datetime(1970, 1, 1)).total_seconds()


def from_timestamp(timestamp, utc=True, tz=None):
    utc = datetime.datetime.utcfromtimestamp(timestamp)
    if utc:
        return utc
    if tz:
        return utc_to_local(utc, tz)


def to_iso_date_str(dt):
    return dt.strftime(ISO_FORMAT)


def parse_date(dt_string):
    """
    >>> iso8601.parse_date("2007-01-25T12:00:00Z")
    datetime.datetime(2007, 1, 25, 12, 0, tzinfo=<iso8601.Utc>)
    :param dt_string:
    :return:
    """
    try:
        return iso8601.parse_date(dt_string)
    except iso8601.iso8601.ParseError:
        raise TypeError('%s is not correct type' % dt_string)


def string_to_date(dt_string, format=YYYY_MM_DD):
    return datetime.datetime.strptime(dt_string, format).date()


def date_to_string(date, format=YYYY_MM_DD):
    return date.strftime(format)


if __name__ == '__main__':
    print parse_date('2001-01-01').date()
    print date_to_string(string_to_date('2001-01-01'))
