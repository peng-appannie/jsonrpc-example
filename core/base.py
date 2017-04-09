# Copyright (c) 2017 App Annie Inc. All rights reserved.
from fields import BaseField

class Serializable(object):
    """
    if one python class has corresponding DTO and inherit this class
    we can convert Serializable instance to dto
    after we get dto, we can get dict with base types which could be use
    to transport on http
    """

    def to_dto(self):
        raise NotImplementedError('should implement in subclass')

    @classmethod
    def from_dto(cls, dikt):
        raise NotImplementedError('should implement in subclass')


class FieldRegisterMeta(type):
    ALL_DTO_CLASS = {}

    def __new__(mcs, name, bases, dct):
        _field_keys = set()
        _fields = set()
        _field_dict = dict()
        for attr, value in dct.items():
            if isinstance(value, BaseField):
                dct.pop(attr)
                dct['_%s' + attr] = value

                if value.name is None:
                    value.name = attr
                if value.name not in _field_keys:
                    _field_keys.add(value.name)
                    _fields.add(value)
                    _field_dict[value.name] = value
                else:
                    raise TypeError('Duplicate define of dto field %s' % value.name)
        dct['_field_keys'] = _field_keys
        dct['_fields'] = _fields
        dct['_field_dict'] = _field_dict
        kls = super(FieldRegisterMeta, mcs).__new__(mcs, name, bases, dct)
        for field in _fields:
            field.bind(kls)
        if name != 'BaseDTO':
            # if change this name with class BaseDTO simultaneous
            FieldRegisterMeta.ALL_DTO_CLASS[name] = kls
        return kls


class BaseDTO(object):
    __metaclass__ = FieldRegisterMeta

    _field_keys = set()
    _fields = set()
    _field_dict = {}

    def __init__(self, **data):
        _data = {}
        for field in self._fields:
            key = field.name
            _data[key] = field(data.get(key))
        self._data = _data

    def repr(self):
        return '\n'.join(['\t%s=%r' % (key, value) for key, value in self._data.items()])

    def __str__(self):
        return '<(DTO)%s \n%s\t>' % (self.__class__.__name__, self.repr())

    def to_dict(self):
        self._data['__cls__'] = self.__class__.__name__
        return self._to_dict()

    def _to_dict(self):
        return self._data

    @classmethod
    def from_dict(cls, dikt):
        return cls(**dikt)

    def _set_field_value(self, field_key, value):
        field = self._get_field(field_key)
        key = field.name
        self._data[key] = field(value)

    def __setattr__(self, key, value):
        if key in self._field_keys:
            self._set_field_value(key, value)
        return super(BaseDTO, self).__setattr__(key, value)

    def __getattr__(self, item):
        if item in self._field_keys:
            return self._data[item]
        return self.__getattribute__(item)

    def _get_field(self, key):
        return self._field_dict.get(key)

    @classmethod
    def find(cls, name):
        return cls.ALL_DTO_CLASS.get(name)


class DTOList(BaseDTO):
    __type__ = None

    def __init__(self, data_list, **kwargs):
        super(DTOList, self).__init__(**kwargs)
        li = []
        for dct in data_list:
            if not isinstance(dct, self.__type__):
                dct = self.__type__.from_dict(dct)
            li.append(dct)
        self._data['__list__'] = li

    @property
    def __list__(self):
        return self._data['__list__']

    def _to_dict(self):
        rdi = {}
        rdi.update(self._data)
        rdi['__list__'] = [i.to_dict() for i in self._data['__list__']]
        return rdi

    def __iter__(self):
        for i in self.__list__:
            yield i

    def __getitem__(self, item):
        return self.__list__[item]


class DTODict(BaseDTO):
    __key__ = None
    __value__ = None
    __type__ = None

    def __init__(self, data_dict, **kwargs):
        super(DTODict, self).__init__(**kwargs)
        di = []
        for key, dct in data_dict.items():
            if not isinstance(dct, self.__type__):
                dct = dct.to_dict()
            di[key] = dct
        self._data['__dict__'] = di

    def _to_dict(self):
        rdi = {}
        rdi.update(self._data)
        rdi['__dict__'] = {k: v.to_dict() for k, v in self._data['__dict__'].items()}
        return rdi


class ServiceBaseMeta(type):
    __LZD__ = 'lazy_decor'

    def __new__(mcs, name, bases, dct):
        kls = super(ServiceBaseMeta, mcs).__new__(mcs, name, bases, dct)
        for attr in dct.keys():
            value = getattr(kls, attr, None)
            lazy_decor = ServiceBaseMeta.get_lazy_decorator(value)
            if lazy_decor:
                print '>>> Bind lazy_decor @', name
                wrapped = lazy_decor(value)
                setattr(kls, attr, wrapped)

        return kls

    @staticmethod
    def append_lazy_decorator(method, decor):
        setattr(method, ServiceBaseMeta.__LZD__, decor)

    @staticmethod
    def get_lazy_decorator(method):
        __func__ = getattr(method, '__func__', None)
        if __func__:
            return getattr(__func__, ServiceBaseMeta.__LZD__, None)


class ServiceBase(object):
    """
    lazy decorated when expose works on class method
    """

    __metaclass__ = ServiceBaseMeta
