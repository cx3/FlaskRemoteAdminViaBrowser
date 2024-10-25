import os
import sys
import code
import json
import types
import pprint
import base64
import inspect
import importlib


def load_package(package_path):
    python_files = [_ for _ in os.listdir(package_path) if _.endswith('.py')]

    for package_name in python_files:
        loaded_modules = []
        sys.path.append(package_path)
        package_name = package_name.replace('.py', '')
        print('package name:', package_name)
        package = importlib.import_module(package_name)
        sys.path.pop()
        globals()[package_name] = package

        loaded_modules.append(package_name)

        for root, _, files in os.walk(os.path.join(package_path, '')):
            for file in files:
                if file.endswith('.py') and file != '__init__.py':
                    module_name = os.path.splitext(file)[0]

                    module = importlib.import_module(module_name, package_name)
                    full_module_name = f"{package_name}.{module_name}"
                    globals()[full_module_name] = module
                    loaded_modules.append(full_module_name)

        return package, loaded_modules


def _str_type(s: str) -> str:
    #  '<class 'inspect._empty'>'
    s = str(s)
    for _ in ['\'', '"', '\n', '<', '>', 'class ']:
        s = s.replace(_, '')
    while 1:
        if '\n' in s:
            s = s.replace('\n', '')
        else:
            break
    return s


def _b64(data) -> str:
    if isinstance(data, str):
        data_bytes = data.encode('utf-8')
    elif isinstance(data, bytes):
        data_bytes = data
    else:
        data_bytes = str(data).encode('utf-8')

    base64_bytes = base64.b64encode(data_bytes)
    base64_str = base64_bytes.decode('utf-8')
    return base64_str


def inspect_class(some_class: type):
    methods = inspect.getmembers(some_class, lambda attr: not (inspect.ismethod(attr)))  # No attributes
    methods_filtered = [m for m in methods if not (m[0].startswith("__") and m[0].endswith("__"))]
    # [('some_func', <function SomeClass.some_func at 0x7fc823f77430>), ...]

    attributes = inspect.getmembers(some_class, lambda attr: not (inspect.isroutine(attr)))  # No functions
    attrs_filtered = [a for a in attributes if not (a[0].startswith("__") and a[0].endswith("__"))]

    signatures = [inspect.signature(_) for _ in methods + attributes]

    '''https://martinheinz.dev/blog/82'''

    return {
        'methods': methods,
        'attributes': attributes,
        'signatures': signatures
    }


def get_function_info(func):
    try:
        sig = inspect.signature(func)
        return {
            "name": func.__name__,
            "parameters": [
                {
                    "name": param.name,
                    "type64": _b64(str(param.annotation)),
                    "default": _b64(param.default if param.default is not inspect.Parameter.empty else None)
                }
                for param in sig.parameters.values()
            ],
            "return_type": _str_type(sig.return_annotation)
        }
    except ValueError as v:
        return _str_type(func)


def get_class_info(cls):
    class_info = {
        "name": cls.__name__,
        "doc64": _b64(inspect.getdoc(cls)),
        "bases": [base.__name__ for base in cls.__bases__],
        "methods": [],
        "attributes": []
    }
    for name, obj in inspect.getmembers(cls):
        if inspect.isfunction(obj) or inspect.ismethod(obj):
            class_info['methods'].append(get_function_info(obj))
        elif not name.startswith('__'):
            class_info["attributes"].append({
                "name": name,
                "type": _str_type(type(obj).__name__),
                "value64": _b64(bytes(str(obj).encode('utf8')))
            })
    return class_info


def get_module_info(module):
    info = {
        "name": module.__name__,
        "doc64": _b64(inspect.getdoc(module)),
        "classes": [],
        "functions": [],
        "modules": []
    }
    for name, obj in inspect.getmembers(module):
        if inspect.isfunction(obj):
            info["functions"].append(get_function_info(obj))
        elif inspect.isclass(obj):
            info["classes"].append(get_class_info(obj))
        '''elif inspect.ismodule(obj) and obj is not module:
            info['modules'].append(get_module_info(obj))'''
    return info


def inspect_package(package):
    package_info = {
        "name": package.__name__,
        "modules": []
    }
    for name, obj in inspect.getmembers(package):
        if inspect.ismodule(obj):
            package_info["modules"].append(get_module_info(obj))
    return package_info


def serialize(data):
    if isinstance(data, dict):
        return {k: serialize(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [serialize(item) for item in data]
    elif isinstance(data, (types.FunctionType, types.ModuleType, type, types.BuiltinFunctionType)):
        return _str_type(data)
    elif isinstance(data, str):
        return _str_type(str(data))
    return data


def inspect_globals():
    modules, classes, functions = [], [], []
    for key, value in globals().items():
        print(f'>>> {key}:{value}')
        if isinstance(value, types.ModuleType):
            modules.append({key: get_module_info(value)})
        if inspect.isclass(value):
            classes.append({key: get_class_info(value)})
        if inspect.isfunction(value):
            functions.append({key: get_function_info(value)})
    return {
        "modules": modules,
        "classes": classes,
        "functions": functions
    }


def inspect_object(obj, include_inherited=False):
    info = {
        'attributes': {},
        'methods': {}
    }

    tmp = dir(object)

    for name, member in inspect.getmembers(obj):
        if inspect.ismethod(member) or inspect.isfunction(member):
            if include_inherited or name not in tmp or name == '__init__':
                info['methods'][name] = {
                    'signature': str(inspect.signature(member)),
                    'doc64': _b64(inspect.getdoc(member))
                }
        else:
            if name not in tmp:
                info['attributes'][name] = str(member)

    return serialize({
        'Python object ' + _str_type(type(obj).__name__): {
            'value64': _b64(obj),
            'module': str(inspect.getmodule(obj).__name__ if inspect.getmodule(obj) else None),
            'doc64': _b64(inspect.getdoc(obj)),
            **info
        }
    })


def inspect_values(*args):
    result = {}
    for arg in args:
        result[arg.__name__] = inspect_object(arg)
    return result


class MyClass:
    def __init__(self, *args, **kwargs):
        self.field_args = args
        self.field_kwargs = kwargs

    def __call__(self, *args, **kwargs):
        pass


if __name__ == '__main__':
    def test():
        mc = MyClass(3, 4, a=1, b=2)

        data = inspect_object(mc)

        pprint.pprint(data)

        #with open('inspect_dump_test.txt', 'w') as f:
        #    f.write(json.dumps(serialize(data), indent=4))

    test()
