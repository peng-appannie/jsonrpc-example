# Copyright (c) 2017 App Annie Inc. All rights reserved.
import inspect
import urllib

import requests
from simplejson.scanner import JSONDecodeError

import pingpong
import signature
from fields import String

FORCE_POST = '_FORCE_POST'


class EntryPoint(object):
    """
    the entry both used in server & client

    on server mode:

    on client mode


    in server mode, it invokes by request
    in client mode, invoke this wrapper will send the request call the shadow
    method in remote server
    """
    default_path_template = '/invoke/%s'

    # only used for client
    host = 'http://127.0.0.1:5000'

    def __init__(self, function, arg_fields, path=None, methods=None, key=None,
                 retype=None, client_mode=False, on_class=False):
        """
        :param function:
        :param arg_fields:
        :param path:
        :param methods:
        :param key:
        :param retype:
        :param client_mode:
        :param on_class: if open this flag, will ignore first argument (cls/self)
        :return:
        """
        self.methods = methods
        self.signature = signature.Signature(function, {})
        self.arg_fields = arg_fields
        self.support_get = self.signature.in_base_type
        self.original_callable = function
        self.key = key or self.signature.full_name
        arg_spec = inspect.getargspec(function)
        self.args = set(arg_spec.args)
        self.path = path or (self.default_path_template % self.key)
        self.retype = retype
        self.client_mode = client_mode
        self.on_class = on_class
        self.path_args = set([fname for _, fname, _, _ in self.url._formatter_parser() if fname])

    def __str__(self):
        if self.client_mode:
            return '<(Remote)EntryPoint %s => %s() >' % (self.path, self.signature.full_name)
        else:
            return '<EntryPoint %s => %s() >' % (self.path, self.signature.full_name)

    def __call__(self, *args, **kwargs):
        if self.client_mode:
            return self.call_remote(*args, **kwargs)
        else:
            return self.call_original(*args, **kwargs)

    def call_from_request(self, **kwargs):
        """
        :param kwargs: kwargs restores from request
        :return:
        """
        kwargs = self.convert_arg_dict(kwargs, direction='from_string')
        print ">>> Call From request", kwargs
        return self.original_callable(**kwargs)

    def call_remote(self, *args, **kwargs):
        arg_dict = self.build_arg_dict(args, kwargs)
        force_post = kwargs.pop(FORCE_POST, False)
        path_arg_dict = {}
        for path_arg in self.path_args:
            path_arg_dict[path_arg] = arg_dict.pop(path_arg)
        url = self.url.format(**path_arg_dict)
        if force_post or not self.support_get:
            print '>>> Call Remote :', arg_dict, url
            response = requests.post(url, json=arg_dict)
        else:
            print '>>> Call Remote :', arg_dict, url
            url = url + '?' + urllib.urlencode(arg_dict)
            response = requests.get(url)
        status_code = response.status_code
        if isinstance(self.retype, String):
            return response.content
        try:
            data = response.json()
            return pingpong.unpack_result(data, dto_type=self.retype)
        except JSONDecodeError:
            raise Exception('Not Json Data: %s' % response.content)

    def call_original(self, *args, **kwargs):
        return self.original_callable(*args, **kwargs)

    def build_arg_dict(self, args, kwargs):
        if self.on_class:
            args = ('place_holder_for_implicit_arg_of_class',) + args
            arg_dict = self.signature.convert_to_dict(args, kwargs)
            arg_dict.pop(self.signature.get_arg_name_by_index(0))
        else:
            arg_dict = self.signature.convert_to_dict(args, kwargs)
        return self.convert_arg_dict(arg_dict)

    def convert_arg_dict(self, arg_dict, direction='to_string'):
        """
        convert and validate the value of arg_dict
        the format of value can be string or other type
        field instance in self.arg_fields will do validation and transform
        :param arg_dict:
        :param direction:
        :return: dict
        """
        converted_kwargs = {}
        for key, value in arg_dict.items():
            field = self.arg_fields.get(key)
            if field:
                if direction == 'to_string':
                    value = field.to_string(value)
                elif direction == 'from_string':
                    value = field.from_string(value)
                else:
                    raise Exception('direction should be `to_string` or `from_string`')
            converted_kwargs[key] = value
        return converted_kwargs

    @property
    def url(self):
        return self.host + self.path

    def show_annotation(self):
        """
        :return:
        """
        args = [
            ('path', self.path),
            ('methods', self.methods),
            ('key', self.key),
            ('retype', self.retype.__class__.__name__),
        ]
        args_types = self.arg_fields
        args.extend(args_types.items())
        return ', '.join(['%s=%r' % (k, v) for (k, v) in args if v is not None])

    @property
    def retype_is_string(self):
        return isinstance(self.retype, String)
