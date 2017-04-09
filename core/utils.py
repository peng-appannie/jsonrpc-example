# Copyright (c) 2017 App Annie Inc. All rights reserved.
import datetime
import json

import tz


class ObjectDict(dict):
    """Makes a dictionary behave like an object, with attribute-style access.
    """

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value

    @classmethod
    def convert(cls, data):
        if isinstance(data, dict):
            for k, v in data.items():
                data[k] = cls.convert(v)
            data = ObjectDict(**data)
        elif isinstance(data, list):
            data[0:] = [cls.convert(_) for _ in data]
        return data


def filter_none(dic):
    return {k: v for k, v in dic.items() if v is not None}


def memoize(f):
    """ Memoization decorator for functions taking one or more arguments. """

    class memodict(dict):
        def __init__(self, f):
            self.f = f

        def __call__(self, *args):
            return self[args]

        def __missing__(self, key):
            ret = self[key] = self.f(*key)
            return ret

    return memodict(f)


class EnhancedEncoder(json.JSONEncoder):
    DATE_FORMAT = '_date:%Y-%m-%d'
    DATE_TIME_FORMAT = '_'

    def default(self, o):
        if isinstance(o, datetime.datetime):
            return '_dt:' + tz.to_iso_date_str(o)
        elif isinstance(o, datetime.date):
            return o.strftime(self.DATE_FORMAT)

        return json.JSONEncoder.default(self, o)


def load_with_datetime(pairs, format=EnhancedEncoder.DATE_FORMAT):
    """Load with dates"""
    d = {}
    for k, v in pairs:
        if isinstance(v, basestring):
            if v.startswith('_date:'):
                # optimize for perf
                try:
                    d[k] = datetime.datetime.strptime(v, format).date()
                except ValueError:
                    d[k] = v
            if v.startswith('_dt:'):
                try:
                    d[k] = tz.parse_date(v[4:])
                except ValueError:
                    d[k] = v
        else:
            d[k] = v
    return d


def json_loads(data):
    return json.loads(data, object_pairs_hook=load_with_datetime)


def json_dumps(obj):
    return json.dumps(obj, cls=EnhancedEncoder)
