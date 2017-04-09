# Copyright (c) 2017 App Annie Inc. All rights reserved.
from application.core.signature import is_classmethod
from base import ServiceBaseMeta
from entry_point import EntryPoint
from signature import is_method


class WebServiceCenter(object):
    _entry_points_ = {}

    @classmethod
    def expose(cls, path=None, methods=None, key=None, retype=None, client_mode=False, on_class=False, **args_types):
        """
        :param path: url patter for this entry
        :param methods: should be GET or POST, some entry can only support POST due to the
            params of entry function
        :param key: the unique name of this entry, if pass None , will auto generate base on name of
            function & class
        :param retype: return type, this type is only used for schema definition, if specified DTO
            of Field type of retype, client can restore it after get response json data.
        :param args_types: input params signature, this is very useful for send & handle request, basically
            every callable entry points has some arguments, and we have many ways to transport it on
            http, here we only support GET and POST method, in GET method, we pack and encode all params
            in URL query string, for example:

                @expose(a=int, b=str, c=float)
                def entry(a, b=None, c=None):
                    pass

                if call entry(122, 'asd', 22.3) from client, we will encoding the query like

                `?a=122&b=asd&c=22.3`

            this requires all arguments defines should be in base types (see: core.signature.BASE_TYPES), and
            one arg should have one type( NoneType always as the optional ), once we defined the unambiguous
            arg type, we will try to convert '22.2' to 22.2, convert 'null' to None, all this procedure can be
            done by signature.

            as for the situation that our entry accepts some complex arguments, dict/list/object, or something
            else, we have POST method to support it, when client get the complex arguments, our frame will
            dump it to json as request body and send to server.
        :return: function
        """

        def decorator(function):
            """
            transparent wrapper, only changes original callable on client_mode=True
            :param function:
            :return:
            """

            def bind_entry(f=function, oc=on_class):
                entry = EntryPoint(f, args_types,
                                   path=path, methods=methods,
                                   key=key, retype=retype,
                                   client_mode=client_mode, on_class=oc)
                cls.add_entry(entry)
                return entry

            on_class_method = is_classmethod(function)
            on_method = is_method(function)
            if on_class_method or on_method or on_class:
                def lazy_decor(cls_method):
                    """
                    real decorator works with ServiceBaseMeta, mark it at first, then wrap methods after class created
                    :param cls_method:
                    :return:
                    """
                    entry = bind_entry(cls_method, oc=True)
                    # print  entry if client_mode else cls_method
                    return entry if client_mode else cls_method

                if on_class_method:
                    ServiceBaseMeta.append_lazy_decorator(function.__func__, lazy_decor)
                else:
                    ServiceBaseMeta.append_lazy_decorator(function, lazy_decor)
                return function
            else:
                entry = bind_entry()
                return entry if client_mode else function

        return decorator

    @classmethod
    def remote(cls, path=None, methods=None, key=None, retype=None, on_class=False, **args_types):
        return cls.expose(path=path, methods=methods, key=key, retype=retype,
                          client_mode=True, on_class=on_class, **args_types)

    @classmethod
    def add_entry(cls, ep):
        print ">>> Add", ep
        cls._entry_points_[ep.key] = ep
        return ep

    @classmethod
    def get_all_entry_points(cls):
        return cls._entry_points_

    @classmethod
    def bind_web_interface(cls, web_interface):
        for entry in cls._entry_points_.values():
            web_interface.register(entry)

    @classmethod
    def register(cls, function, path=None, methods=None, key=None, retype=None, client_mode=False, on_class=False,
                 **args_types):
        on_class_method = is_classmethod(function)
        on_method = is_method(function)
        on_class = on_class_method or on_method or on_class
        entry = EntryPoint(function, args_types,
                           path=path, methods=methods,
                           key=key, retype=retype,
                           client_mode=client_mode, on_class=on_class)
        cls.add_entry(entry)
        return entry

    @classmethod
    def register_remote(cls, function, path=None, methods=None, key=None, retype=None,
                        on_class=False,
                        **args_types):
        entry = cls.register(function, path, methods, key, retype, True, on_class, **args_types)
        entry.signature.replace_original(entry)

# alias
expose = WebServiceCenter.expose
remote = WebServiceCenter.remote
register = WebServiceCenter.register
register_remote = WebServiceCenter.register_remote
