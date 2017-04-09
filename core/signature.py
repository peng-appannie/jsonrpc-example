# Copyright (c) 2017 App Annie Inc. All rights reserved.
# encoding: utf-8
import inspect
import types
from functools import wraps

# defines base types can passing on URL query
BASE_TYPES = {basestring, int, long, float, str, types.NoneType, bool, unicode}
STR_TYPES = {basestring, str, unicode}
PASS = '_pass_check'


def get_signature(function):
    """
    :param function:
    :return: Signature
    """
    if hasattr(function, 'signature'):
        return function.signature


def is_method(i):
    return isinstance(i, types.MethodType)


def is_classmethod(i):
    return isinstance(i, classmethod)


class Signature(object):
    """
    type defines for function/static method/class method/instancemethod
    """
    FUNC = 0
    STC_METHOD = 1
    CLS_METHOD = 2
    INS_METHOD = 3
    UNKNOWN = -1

    @classmethod
    def inspect_staticmethod(cls, sm):
        """
        Returns (class, attribute name) for staticmethod
        which has annotation like `@staticmethod`

        """
        mod = inspect.getmodule(sm)
        sm_name = sm.__name__
        for attr in dir(mod):
            kls = getattr(mod, attr, None)
            if kls is not None:
                try:
                    ca = inspect.classify_class_attrs(kls)
                    for attribute in ca:
                        o = attribute.object
                        if isinstance(o, staticmethod) and getattr(kls, sm_name) == sm:
                            return kls, sm_name
                except AttributeError:
                    pass
        return (None, None)

    def __init__(self, func, args_types):
        code = func.func_code
        self.original_callable = func
        self.type, self.class_def = self.inspect_type(func)

        self.func_name = func.func_name
        if self.class_def:
            self.class_name = self.class_def.__name__
            self.full_name = self.class_def.__name__ + '.' + self.func_name
        else:
            self.class_name = None
            self.full_name = self.func_name

        self.arg_names = code.co_varnames[:code.co_argcount]
        self.arg_spec = inspect.getargspec(func)
        self.magic_kwargs = self.arg_spec.keywords
        defaults = self.arg_spec.defaults or []
        self.args_list = self.arg_spec.args
        self.args = set(self.arg_spec.args)
        self.kwargs = set(defaults)
        self.varargs = self.arg_spec.varargs
        if defaults:
            self.default_values = dict(zip(self.arg_spec.args[-len(defaults):], defaults))
        else:
            self.default_values = {}

        self.type_specs = self.prepare_type_info(args_types)

        self.typed_args = set(self.type_specs.keys())
        self.untyped_args = self.args - self.typed_args
        self.all_support_types = set()
        for arg_name, type_set in self.type_specs.items():
            self.all_support_types = self.all_support_types.union(type_set)

        self.in_base_type = not (self.all_support_types - BASE_TYPES)

    def inspect_type(self, func):
        if inspect.isfunction(func):
            kls, sm_name = self.inspect_staticmethod(func)
            if kls:
                return self.STC_METHOD, kls
            return self.FUNC, None
        elif inspect.ismethod(func):
            if func.__self__ == func.__class__ or func.im_class == func.__self__:
                return self.CLS_METHOD, func.im_self or func.__self__
            else:
                return self.INS_METHOD, func.im_self or func.im_class or func.__self__.__class__
        else:
            raise TypeError('Unknown Type %s, Please check input is method or function' % func)

    def prepare_type_info(self, args_types):
        accept_types = {}
        for arg_name, arg_type in args_types.iteritems():
            if arg_name not in self.args:
                raise KeyError('%s() has no arg:%s' % (self.func_name, arg_name))
            if not isinstance(arg_type, (tuple, set, list)):
                arg_type_set = {arg_type, }
            else:
                arg_type_set = set(arg_type)

            accept_types[arg_name] = arg_type_set
        return accept_types

    def has_arg(self, arg_name):
        return arg_name in self.args

    def get_type_spec(self, arg_name):
        return self.type_specs[arg_name]

    def format_arg(self, arg_name, arg_value):
        """
        convert string like args to original type:
        for example if arg type support int , we'll try
        to convert arg_value from '1' to 1
        :param arg_name:
        :param arg_value:
        :return:
        """
        type_spec = self.get_type_spec(arg_name)
        converted_to = type_spec - STR_TYPES
        if types.NoneType in converted_to and arg_value == 'null':
            return None
        for tp in converted_to:
            try:
                return tp(arg_value)
            except:
                pass
        return arg_value

    def format_kwargs(self, kwargs, ignore_invalid=True):
        _cleaned_args = {}
        for arg_name, arg_value in kwargs.items():
            if arg_name in self.type_specs:
                _cleaned_args[arg_name] = self.format_arg(arg_name, arg_value)
            else:
                if not ignore_invalid:
                    raise TypeError('%s() get unsupported args %s' % (self.func_name, arg_name))
        return _cleaned_args

    def check_arg(self, arg_name, arg_value):
        if not self.has_arg(arg_name):
            raise TypeError('%s() get unsupported args %s' % (self.func_name, arg_name))
        type_spec = self.type_specs[arg_name]
        for t in type_spec:
            if isinstance(arg_value, t):
                break
        else:
            raise TypeError('%s() arg:%s(%s) is not in type %s' % (self.func_name, arg_name, type(arg_name), types))

    def check_args(self, arg_dict):
        for arg_name, arg_value in arg_dict.items():
            self.check_arg(arg_name, arg_value)

    def get_arg_name_by_index(self, index):
        try:
            return self.args_list[index]
        except IndexError:
            raise TabError('get undefined argument on position %d' % index)

    def convert_to_dict(self, arg_tuple, kwargs_dict):
        """
        :param arg_tuple:
        :param kwargs_dict:
        :return:
        """
        args = {}
        for index, arg_value in enumerate(arg_tuple):
            args[self.get_arg_name_by_index(index)] = arg_value
        for k, v in kwargs_dict.items():
            if k in args:
                raise TypeError('duplicate kwargs: %s, already defined in tuple arguments' % k)
            if k not in self.args and not self.magic_kwargs:
                raise TabError('get undefined argument %s=%r' % (k, v))
            args[k] = v
        return args

    @property
    def doc(self):
        return self.original_callable.__doc__

    @property
    def arg_define(self):
        """
        return code like arg define
        eg:
            inspect function below
            def func(a, b, c=2, d='', *ag, **kw):
                pass
        will return str 'a, b, c=2, d='', *ag, **kw'

        :return: str
        """
        arg_list = []
        kwargs_list = []
        for arg in self.args_list:
            if arg in self.default_values:
                kwargs_list.append('%s=%r' % (arg, self.default_values[arg]))
            else:
                arg_list.append(arg)
        arg_list += kwargs_list
        if self.varargs:
            arg_list.append('*' + self.varargs)
        if self.magic_kwargs:
            arg_list.append('**' + self.magic_kwargs)
        return ', '.join(arg_list)

    def replace_original(self, item):
        if self.class_def:
            setattr(self.class_def, self.func_name, item)


def accepts(**args_types):
    """Decorator to check argument types.
    check_args
    Usage:

    @argtype(name=str, text=str)
    def parse_rule(name, text): ...

    @accepts(a=int, v=int, c=int, d=(int, type(None)))
    def tees(a, v=2, c=3, *arg, **kwargs):
        print a, v, c
    tees(a=1, d='')
    """

    def decorator(func):
        signature = Signature(func, args_types)

        @wraps(func)
        def decorated(*args, **kwargs):
            if not kwargs.get(PASS, False):
                for index, arg_value in enumerate(args):
                    arg_name = signature.get_arg_name_by_index(index)
                    signature.check_arg(arg_name, arg_value)
                signature.check_args(kwargs)
            return func(*args, **kwargs)

        func.signature = signature

        return decorated

    return decorator
