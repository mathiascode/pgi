# Copyright 2012 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from pgi.codegen.utils import parse_code
from pgi.gtype import PGType


class CodeGenBackend(object):
    """Backends provide methods that produce python code. They take
    input variable nams and return a CodeBlock + output variables. If one
    method is not implemented the consumer will fall back to another backend
    if possible.

    get_library_object  - init the backend and do caching with the namespace
    get_function_object - should return something callable
    call                - code surrounding the function call (exceptions..)
    """

    NAME = "base"

    def __init__(self):
        super(CodeGenBackend, self).__init__()

        def var_factory():
            var_factory.c += 1
            return "t%d" % var_factory.c
        var_factory.c = 0

        self.var = var_factory

    def parse(self, code, **kwargs):
        return parse_code(code, self.var, **kwargs)

    def __getattr__(self, name):
        raise NotImplementedError(
            "method %r not implemented in backend %r" % (name, self.NAME))

    def get_library_object(self, namespace):
        raise NotImplementedError

    def get_function_object(self, lib, symbol, args, ret,
                            method=False, self_name="", throws=False):
        raise NotImplementedError

    def call(self, name, args):
        raise NotImplementedError

    def unpack_gvalue(self, name):
        getter_map = {
            "gboolean": lambda v: v.get_boolean(),
            "gchar": lambda v: chr(v.get_schar()),
            "gdouble": lambda v: v.get_double(),
            "gfloat": lambda v: v.get_float(),
            "GType": lambda v: v.get_gtype(),
            "gint64": lambda v: v.get_int64(),
            "gint": lambda v: v.get_int(),
            "glong": lambda v: v.get_long(),
            "GObject": lambda v: v.get_object(),
            "gpointer": lambda v: v.get_pointer(),
            "gchararray": lambda v: v.get_string(),
            "guchar": lambda v: chr(v.get_uchar()),
            "guint64": lambda v: v.get_uint64(),
            "guint": lambda v: v.get_uint(),
            "gulong": lambda v: v.get_ulong(),
        }

        items = getter_map.items()
        getter_map = dict((PGType.from_name(k), v) for (k, v) in items)

        map_var = self.var()

        block, var = self.parse("""
try:
    $out = $lookup[$value.g_type]($value)
except KeyError:
    $out = $value
""", value=name, lookup=map_var)

        block.add_dependency(map_var, getter_map)
        return block, var["out"]
