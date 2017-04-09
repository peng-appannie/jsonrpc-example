# Copyright (c) 2017 App Annie Inc. All rights reserved.

import re

import flask

import pingpong
from http_code import *


class UnknownResponseObject(Exception):
    code = INTERNAL_ERROR


class NotFoundError(Exception):
    code = NOT_FOUND


class WebInterface(object):
    """
    Abstract wrapper for web frameworks, concrete implement should
    depends on each platform (Django,Flask, Tornado .etc)
    """

    def register(self, entry):
        pass

    def render_response_to_client(self, response):
        """
        this method can return response to WebFrame
        :param response:
        :return:
        """
        pass


class FlaskInterface(WebInterface):
    def __init__(self, flask_app):
        self.app = flask_app
        self.request = flask.request

    def register(self, entry):
        """
        :param entry: EntryPoint
        :return:
        """
        if entry.support_get:
            default_method = ['GET', 'POST']
        else:
            default_method = ['POST']
        path = self.convert_path(entry.path)
        decorator = self.app.route(path, methods=default_method)
        print '>> FlaskInterface connected @', path, default_method
        if entry.retype_is_string:
            render_resp = lambda resp: resp.data or resp.error
        else:
            render_resp = self.render_response_to_client

        def flask_entry(**path_args):
            args = self.input_args(path_args)
            response = pingpong.pack_result(callback=lambda: entry.call_from_request(**args))
            return render_resp(response)

        flask_entry.func_name = entry.key
        decorator(flask_entry)

    def input_args(self, path_args):
        entry_point_arg_dict = {k: v for k, v in self.request.args.items()}
        entry_point_arg_dict.update(path_args)
        if self.request.method == 'POST':
            entry_point_arg_dict.update(self.request.json)
        print '>>> [%s]Path Args:%s, Query Args:%s' % (self.request.method, path_args, entry_point_arg_dict)
        return entry_point_arg_dict

    def render_response_to_client(self, response):
        return flask.jsonify(response), response.code

    def convert_path(self, url_path):
        return re.sub(r"(\{[A-Za-z0-9_]+\})", lambda x: '<string:%s>' % x.group()[1:-1], url_path)
