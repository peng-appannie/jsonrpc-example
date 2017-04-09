import json

from core.base import BaseDTO
from functools import wraps

from errors import APIError
import traceback

class DTOJsonEncoder(json.JSONEncoder):
    def default(self, dto):
        if isinstance(dto, BaseDTO):
            return dto.to_dict()
        else:
            return super().default(o)


class DTOJsonDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, dto_dict):
        if isinstance(dto_dict, dict) and '__cls__' in dto_dict:
            dto_class = BaseDTO.find(dto_dict['__cls__'])
            return dto_class.from_dict(dto_dict)
        else:
            return dto_dict


def aa_data_api(f):

    @wraps(f)
    def _decorator(*args, **kwargs):
        try:
            result = f(*args, **kwargs)
            return {'data': result, 'errors': {} }
        except APIError, e:
            return {'data': [],
                    'errors': {
                        'code': e.code,
                        'traceback': traceback.format_exc(),
                        'message': e.message
                    }}
        except Exception, e:
            return {'data': [],
                    'errors': {
                        'code': 500,
                        'traceback': traceback.format_exc(),
                        'message': e.message
                    }}
    return _decorator
