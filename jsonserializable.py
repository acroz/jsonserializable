from collections import OrderedDict
from collections.abc import Sequence, MutableSequence
from abc import ABCMeta, abstractmethod

import jsonschema


class SerializableBase(metaclass=ABCMeta):
    pass


class SimpleType(SerializableBase):
    pass


SimpleType.register(int)
SimpleType.register(float)
SimpleType.register(bool)
SimpleType.register(str)

JSON_SCHEMA_TYPES = {
    int: 'number',
    float: 'number',
    bool: 'boolean',
    str: 'string'
}


class Serializable(SerializableBase):

    @staticmethod
    @abstractmethod
    def schema():
        pass

    @abstractmethod
    def serialize(self):
        pass

    @classmethod
    @abstractmethod
    def deserialize(cls, data):
        pass


def schema(python_type: ABCMeta):
    if issubclass(python_type, Serializable):
        return python_type.schema()  # type: ignore
    elif issubclass(python_type, SimpleType):
        return {'type': JSON_SCHEMA_TYPES[python_type]}
    else:
        raise TypeError('type has no JSON schema')


def serialize(obj: SerializableBase):
    if isinstance(obj, Serializable):
        return obj.serialize()
    elif isinstance(obj, SimpleType):
        return obj
    else:
        raise TypeError('object is not serializable')


def deserialize(python_type: ABCMeta, data):
    if python_type in JSON_SCHEMA_TYPES:
        return python_type(data)
    else:
        return python_type.deserialize(data)  # type: ignore


class Attribute:

    def __init__(self, type, optional=False):
        assert issubclass(type, SerializableBase)
        self.type = type
        self.optional = optional

    def __repr__(self):
        return 'Attribute(type={}, optional={})'.format(
            self.type, self.optional
        )


class ObjectDict(dict):

    def __init__(self):
        super().__init__()
        self.attributes = OrderedDict()

    def __setitem__(self, key, value):
        if isinstance(value, Attribute):
            self.attributes[key] = value
        super().__setitem__(key, value)


class ObjectMeta(ABCMeta):

    @classmethod
    def __prepare__(metacls, name, bases, **kwargs):
        return ObjectDict()

    def __new__(metacls, name, bases, classdict):
        cls = super().__new__(metacls, name, bases, classdict)

        attributes = OrderedDict()
        attributes.update(getattr(cls, '_object_attributes', {}))
        attributes.update(classdict.attributes)
        cls._object_attributes = attributes

        return cls


class Object(Serializable, metaclass=ObjectMeta):

    def __init__(self, **kwargs):

        for name, jsattr in self._object_attributes.items():
            if name in kwargs:
                setattr(self, name, kwargs[name])
            elif jsattr.optional:
                setattr(self, name, None)
            else:
                classname = self.__class__.__name__
                raise TypeError(
                    "{} missing a required argument '{}'"
                    .format(classname, name)
                )

        # Calling set() on a dict creates a set of its keys
        unused = set(kwargs) - set(self._object_attributes)
        if len(unused) > 0:
            classname = self.__class__.__name__
            raise TypeError(
                "{} got unexpected keyword argument(s) {}"
                .format(classname, unused)
            )

    def __setattr__(self, name, value):
        if name not in self._object_attributes:
            raise AttributeError('{} is not a valid attribute'.format(name))
        jsattr = self._object_attributes[name]
        if jsattr.optional:
            if not (isinstance(value, jsattr.type) or value is None):
                raise TypeError(
                    '{} must be a {} or None'.format(name, jsattr.type)
                )
        else:
            if not isinstance(value, jsattr.type):
                raise TypeError('{} must be a {}'.format(name, jsattr.type))
        super().__setattr__(name, value)

    def __repr__(self):
        parts = []
        for name in self._object_attributes:
            value = getattr(self, name)
            parts.append('{}={}'.format(name, repr(value)))
        classname = self.__class__.__name__
        return '{}({})'.format(classname, ', '.join(parts))

    @classmethod
    def schema(cls):
        properties = {}
        required = []
        for name, jsattr in cls._object_attributes.items():
            properties[name] = schema(jsattr.type)
            if not jsattr.optional:
                required.append(name)
        json_schema = {
            'type': 'object',
            'properties': properties,
            'additionalProperties': False
        }
        if required:
            json_schema['required'] = required
        return json_schema

    def serialize(self):
        properties = {}
        for name, jsattr in self._object_attributes.items():
            value = getattr(self, name)
            if value is None and jsattr.optional:
                continue
            properties[name] = serialize(value)
        return properties

    @classmethod
    def deserialize(cls, data: dict):
        jsonschema.validate(data, cls.schema())
        kwargs = {}
        for name, value in data.items():
            jsattr = cls._object_attributes[name]
            kwargs[name] = deserialize(jsattr.type, value)
        return cls(**kwargs)


class ArrayMeta(ABCMeta):

    def __new__(metacls, name, bases, classdict,
                array_type=Serializable):
        assert isinstance(array_type, type)
        assert issubclass(array_type, SerializableBase)
        cls = super().__new__(metacls, name, bases, classdict)
        cls._array_type = array_type
        return cls

    def __init__(self, *args, **kwargs):
        pass

    def __getitem__(self, array_type):
        return self.__class__(self.__name__,
                              (self,) + self.__bases__,
                              dict(self.__dict__),
                              array_type=array_type)

    def __repr__(self):
        return '{}[{}]'.format(
            self.__name__, repr(self._array_type)
        )

    def __instancecheck__(self, instance):
        if not super().__instancecheck__(instance):
            return False
        for item in instance:
            if not isinstance(item, self._array_type):
                return False
        return True

    def __subclasscheck__(self, cls):
        if not super().__subclasscheck__(cls):
            return False
        if not issubclass(cls._array_type,
                          self._array_type):
            return False
        return True


class Array(MutableSequence, Serializable, metaclass=ArrayMeta):

    def _check_type(self, item):
        if not isinstance(item, self._array_type):
            raise TypeError('array entries must be of type {}'.format(
                self._array_type
            ))

    def __init__(self, contents, *args, **kwargs):
        for item in contents:
            self._check_type(item)
        self._contents = contents

    def __len__(self):
        return len(self._contents)

    def __setitem__(self, index, value):
        self._check_type(value)
        self._contents[index] = value

    def __getitem__(self, index):
        return self._contents[index]

    def __delitem__(self, index):
        del self._contents[index]

    def insert(self, index, value):
        self._check_type(value)
        self._contents.insert(index, value)

    @classmethod
    def schema(cls):
        return {
            'type': 'array',
            'items': schema(cls._array_type)
        }

    def serialize(self):
        return [serialize(item) for item in self]

    @classmethod
    def deserialize(cls, data: Sequence):
        jsonschema.validate(data, cls.schema())
        return cls(deserialize(entry, cls._array_type) for entry in data)
