from collections import OrderedDict as _OrderedDict
from collections.abc import (
    Sequence as _Sequence, MutableSequence as _MutableSequence,
    Mapping as _Mapping, MutableMapping as _MutableMapping
)
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


class ContainerMeta(ABCMeta):

    def __new__(metacls, name, bases, classdict,
                container_type=Serializable):
        assert isinstance(container_type, type)
        assert issubclass(container_type, SerializableBase)
        cls = super().__new__(metacls, name, bases, classdict)
        cls._container_type = container_type
        return cls

    def __init__(self, *args, **kwargs):
        pass

    def __getitem__(self, container_type):
        return self.__class__(self.__name__,
                              (self,) + self.__bases__,
                              dict(self.__dict__),
                              container_type=container_type)

    def __repr__(self):
        return '{}[{}]'.format(
            self.__name__, repr(self._container_type)
        )

    def __instancecheck__(self, instance):
        if not super().__instancecheck__(instance):
            return False
        for item in instance:
            if not isinstance(item, self._container_type):
                return False
        return True

    def __subclasscheck__(self, cls):
        if not super().__subclasscheck__(cls):
            return False
        if not issubclass(cls._container_type,
                          self._container_type):
            return False
        return True


class ContainerBase(Serializable, metaclass=ContainerMeta):

    @classmethod
    def _check_type(cls, item):
        if not isinstance(item, cls._container_type):
            raise TypeError('entries must be of type {}'.format(
                cls._container_type
            ))


class Array(_MutableSequence, ContainerBase):

    def __init__(self, *args, **kwargs):
        self._contents = list(*args, **kwargs)
        for item in self._contents:
            self._check_type(item)

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
            'items': schema(cls._container_type)
        }

    def serialize(self):
        return [serialize(item) for item in self]

    @classmethod
    def deserialize(cls, data: _Sequence):
        jsonschema.validate(data, cls.schema())
        return cls(deserialize(entry, cls._container_type) for entry in data)


class Mapping(_MutableMapping, ContainerBase):

    def __init__(self, *args, **kwargs):
        self._contents = dict(*args, **kwargs)
        for value in self._contents.values():
            self._check_type(value)

    def __len__(self):
        return len(self._contents)

    def __iter__(self):
        return iter(self._contents)

    def __setitem__(self, key, value):
        self._check_type(value)
        self._contents[key] = value

    def __getitem__(self, key):
        return self._contents[key]

    def __delitem__(self, key):
        del self._contents[key]

    @classmethod
    def schema(cls):
        return {
            'type': 'object',
            'additionalProperties': schema(cls._container_type)
        }

    def serialize(self):
        return {key: serialize(value) for key, value in self.items()}

    @classmethod
    def deserialize(cls, data: _Mapping):
        jsonschema.validate(data, cls.schema())
        return cls({
            key: deserialize(value, cls._container_type)
            for key, value in data.items()
        })


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
        self.attributes = _OrderedDict()

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

        attributes = _OrderedDict()
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
