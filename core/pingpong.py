# Copyright (c) 2017 App Annie Inc. All rights reserved.

import traceback

import utils
from base import BaseDTO, Serializable
from fields import String
from http_code import *


class Error(BaseDTO):
    msg = String()
    traceback = String()

    def reraise(self):
        raise Exception('%s' % self.msg)


def handle_error(error):
    return Error(msg=str(error), traceback='\n'.join(traceback.format_exception_only(type(error), error)))


def pack_result(callback):
    """
    get the packer which could
    convert entry result to plain dict, add code and error information
    :param entry:
    :return: response dict
    """

    response = utils.ObjectDict()
    response.code = OK
    try:
        result = callback()
        response.data = to_dict(result)
    except Exception, error:
        traceback.print_exc()
        response.code = getattr(error, 'code', INTERNAL_ERROR)
        response.error = handle_error(error).to_dict()
    finally:
        return response


def unpack_result(response_dict, dto_type=None):
    error = response_dict.get('error')

    if error:
        error = Error.from_dict(error)
        error.reraise()
    data = response_dict['data']
    return from_dict(data)


def to_dict(something):
    if isinstance(something, (list, set)):
        return [to_dict(thing) for thing in something]
    elif isinstance(something, dict):
        return {k: to_dict(v) for k, v in something.items()}
    elif isinstance(something, Serializable):
        return something.to_dto().to_dict()
    elif isinstance(something, BaseDTO):
        return something.to_dict()
    else:
        return something


def from_dict(something):
    if isinstance(something, (list, set)):
        return [from_dict(thing) for thing in something]
    elif isinstance(something, dict):
        __cls__ = something.get('__cls__')
        if __cls__:
            cls = BaseDTO.find(__cls__)
            return cls.from_dict(something)
        else:
            return {k: from_dict(v) for k, v in something.items()}
    else:
        return something
