# Copyright (c) 2017 App Annie Inc. All rights reserved.
import datetime

import tz


class BaseField(object):
    _base_type = (object,)

    def __init__(self, name, can_be_none, default):
        self.name = name
        self._cls = None
        self.can_be_none = can_be_none
        self.default = default

    def bind(self, cls):
        self._cls = cls

    def __repr__(self):
        if self._cls:
            return "<%s.%s>" % (self._cls.__name__, self.name or 'N/A')
        else:
            return "<Field('%s')>" % (self.name or 'N?A')

    def __call__(self, value):
        if value is None:
            if self.default is not None:
                return self.default
            self._accept_none_value(value)
        else:
            if not isinstance(value, self._base_type):
                raise TypeError('%s should be %s, but get %s %s' % (self, self._base_type, value, type(value)))
            self._validate(value)
        return value

    def _accept_none_value(self, value):
        if not self.can_be_none and value is None:
            raise TypeError('%s cannot be None' % self)

    def _validate(self, value):
        return value

    def to_string(self, value):
        self._validate(value)
        return str(value)

    def from_string(self, value):
        types = self._base_type
        error = None
        if not isinstance(self._base_type, tuple):
            types = (self._base_type,)
        for tp in types:
            try:
                return self(tp(value))
            except Exception, error:
                pass
        raise Exception('%s convert from string %s failed: %s' % (self, value, error))


class Number(BaseField):
    _base_type = (long, int, float)


class Int(BaseField):
    _base_type = (int, long)

    def __init__(self, name=None, length=None, min=None, max=None, choices=None, can_be_none=False, default=None):
        super(Int, self).__init__(name, can_be_none, default)


class Float(BaseField):
    _base_type = float


class String(BaseField):
    _base_type = basestring

    def __init__(self, name=None, length=None, min_length=None, max_length=None, choices=None, can_be_none=False,
                 default=None):
        self.length = length
        self.min_length = min_length
        self.max_length = max_length
        self.choices = choices
        super(String, self).__init__(name, can_be_none, default)

    def _validate(self, value):
        if self.choices and value not in self.choices:
            raise TypeError('%s value should be in %s' % (self, self.choices))

    def to_string(self, value):
        return str(value)

    def from_string(self, value):
        return self(value)


class Bool(BaseField):
    _base_type = bool

    def __init__(self, name=None, can_be_none=False, default=None):
        super(Bool, self).__init__(name, can_be_none, default)


class ContainerField(BaseField):
    def __init__(self, name, can_be_none, can_be_empty, default=None):
        super(ContainerField, self).__init__(name, can_be_none, default)
        self.can_be_empty = can_be_empty


class List(ContainerField):
    _base_type = list

    def __init__(self, element_type=None, name=None, can_be_none=False, can_be_empty=False, default=None):
        super(List, self).__init__(name, can_be_none, can_be_empty)
        self.element_type = element_type
        if not isinstance(element_type, BaseField):
            def _element_field(item):
                if not isinstance(item, element_type):
                    raise TypeError('should be %s ' % element_type)

            self._element_field = _element_field
        else:
            self._element_field = element_type

    def _validate(self, value):
        for elem in value:
            try:
                self._element_field(elem)
            except TypeError, e:
                raise TypeError('%s, element type error: %s' % (self, e.message))

    def from_dict(self, dikt):
        return [self.element_type.from_dict(item) for item in dikt['__list__']]

    def to_dict(self):
        pass

    def to_string(self, value):
        for ele in self(value):
            if isinstance(ele, basestring) and ele.find(','):
                raise Exception("Couldn't convert value has `,` inside, please quote it")
        return ','.join(value)

    def from_string(self, value):
        return self(value.split(','))


class Dict(ContainerField):
    _base_type = dict

    def __init__(self, name=None, key=None, value=None, can_be_none=False, can_be_empty=False, default=None):
        super(Dict, self).__init__(name, can_be_none, can_be_empty)
        self.key = key
        self.value = value


class DateField(BaseField):
    _base_type = datetime.date

    def __init__(self, name=None, default=None, format=tz.YYYY_MM_DD, can_be_none=False):
        super(DateField, self).__init__(name, can_be_none, default)
        self.format = format

    def from_string(self, value):
        return self(tz.string_to_date(value, self.format))

    def to_string(self, value):
        return value.date_to_string(self.format)


class DTOField(BaseField):
    _base_type = object

    def __init__(self, name=None, dto_class=None, can_be_none=False, default=None):
        super(DTOField, self).__init__(name, can_be_none, default)
        self.dto_class = dto_class

    def _validate(self, value):
        if not isinstance(value, self.dto_class):
            raise TypeError('%s, should be: %s' % (self, self.dto_class))
