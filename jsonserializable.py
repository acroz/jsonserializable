from collections import OrderedDict as _OrderedDict
from collections.abc import Sequence as _Sequence, Mapping as _Mapping
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


def deserialize(data, python_type: ABCMeta):
    if issubclass(python_type, Serializable):
        return python_type.deserialize(data)  # type: ignore
    elif issubclass(python_type, SimpleType):
        return python_type(data)
    else:
        raise TypeError('cannot deserialize to this type')


def _check_serializable_type(python_type):
    if not isinstance(python_type, type):
        raise TypeError('{} is not a type'.format(python_type))
    if not issubclass(python_type, SerializableBase):
        raise TypeError('{} is not a supported type'.format(python_type))


class ContainerMeta(ABCMeta):

    def __new__(metacls, name, bases, classdict, container_type=None):
        if container_type is not None:
            _check_serializable_type(container_type)
        cls = super().__new__(metacls, name, bases, classdict)
        cls._subclass_cache = {}
        cls._container_type = (container_type or
                               getattr(cls, '_container_type', None))
        return cls

    def __init__(self, *args, **kwargs):
        pass

    def __getitem__(self, container_type):
        _check_serializable_type(container_type)
        if self._container_type is not None:
            raise TypeError(
                'container type already set as {}'.format(self._container_type)
            )
        try:
            cls = self._subclass_cache[container_type]
        except KeyError:
            name = '{}[{}]'.format(self.__name__, container_type.__name__)
            cls = self.__class__(
                name, (self,) + self.__bases__, dict(self.__dict__),
                container_type=container_type
            )
            self._subclass_cache[container_type] = cls
        return cls


class ContainerBase(Serializable, metaclass=ContainerMeta):

    def __init__(self, *args, **kwargs):
        if self._container_type is None:
            raise TypeError(
                'container {} has no inner type - use square brackets to set'
                .format(self.__class__.__name__)
            )
        super().__init__(*args, **kwargs)

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, super().__repr__())

    @classmethod
    def _check_type(cls, item):
        if not isinstance(item, cls._container_type):
            raise TypeError('entries must be of type {}'.format(
                cls._container_type
            ))


class List(ContainerBase, list):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for item in self:
            self._check_type(item)

    def __setitem__(self, index, value):
        self._check_type(value)
        super().__setitem__(index, value)

    def insert(self, index, value):
        self._check_type(value)
        super().insert(index, value)

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


class Dict(ContainerBase, dict):

    @staticmethod
    def _check_key_type(key):
        if not isinstance(key, str):
            raise TypeError('keys must be of type str')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key, value in self.items():
            self._check_key_type(key)
            self._check_type(value)

    def __setitem__(self, key, value):
        self._check_key_type(key)
        self._check_type(value)
        super().__setitem__(key, value)

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


def _is_descriptor(obj):
    """Returns True if obj is a descriptor, False otherwise."""
    return (hasattr(obj, '__get__') or
            hasattr(obj, '__set__') or
            hasattr(obj, '__delete__'))


class EnumDict(dict):

    def __init__(self):
        super().__init__()
        self.members = _OrderedDict()

    def __setitem__(self, key, value):
        if not key.startswith('_') and not _is_descriptor(value):
            if key in self:
                raise TypeError(
                    '{} already defined as: {}'.format(key, self[key])
                )
            if not isinstance(value, SerializableBase):
                raise TypeError('{} is not a serializable type')
            self.members[key] = value
        else:
            super().__setitem__(key, value)


class EnumMember(Serializable):

    def __init__(self, enum, name, value):
        self._enum = enum
        self.name = name
        self.value = value

    def __repr__(self):
        return '{}.{}'.format(self._enum.__name__, self.name)

    def __eq__(self, other):
        return (isinstance(other, EnumMember) and
                self._enum == other._enum and
                self.name == other.name and
                self.value == other.value)

    def schema(self):
        return self._enum.schema()

    def serialize(self):
        return serialize(self.value)

    def deserialize(self, data):
        return self._enum.deserialize(data)


class EnumMeta(ABCMeta):

    @classmethod
    def __prepare__(metacls, name, bases, **kwargs):
        return EnumDict()

    def __new__(metacls, name, bases, classdict):
        cls = super().__new__(metacls, name, bases, classdict)

        member_defs = _OrderedDict()
        member_defs.update(getattr(cls, '_member_definitions', {}))
        member_defs.update(classdict.members)
        cls._member_definitions = member_defs

        name_map = _OrderedDict()
        value_map = _OrderedDict()
        for name, value in member_defs.items():
            member = EnumMember(cls, name, value)
            name_map[name] = member
            try:
                if value in value_map:
                    raise ValueError('enumeration values must be unique')
                value_map[value] = member
            except TypeError:
                # Unhashable value, skip
                pass
        cls._name_map = name_map
        cls._value_map = value_map

        return cls

    def __iter__(cls):
        return iter(cls._name_map.values())

    def __len__(cls):
        return len(cls._name_map)

    def __getitem__(self, name):
        return self._name_map[name]

    def __getattr__(self, name):
        if name.startswith('_'):
            return super().__getattr__(name)
        try:
            return self._name_map[name]
        except KeyError:
            raise AttributeError(name) from None

    def __call__(self, value):
        return self.from_value(value)

    def from_value(self, value):
        try:
            return self._value_map[value]
        except TypeError:
            # Unhashable value
            for member in self._name_map.values():
                if member.value == value:
                    return member
            else:
                raise ValueError('no matching value')
        except KeyError:
            raise ValueError('no matching value')


class Enum(Serializable, metaclass=EnumMeta):

    @classmethod
    def schema(cls):
        return {'enum': [serialize(member) for member in cls]}

    def serialize(self):
        raise TypeError('cannot serialize an enum, only its members')

    @classmethod
    def deserialize(cls, data):
        jsonschema.validate(data, cls.schema())
        return cls.from_value(data)


class Attribute:

    def __init__(self, type, optional=False):
        _check_serializable_type(type)
        self.type = type
        self.optional = bool(optional)

    def __repr__(self):
        return '{}(type={}, optional={})'.format(
            self.__class__.__name__, self.type, self.optional
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
        return '{}({})'.format(self.__class__.__name__, ', '.join(parts))

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        for name in self._object_attributes:
            if getattr(self, name) != getattr(other, name):
                return False
        return True

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
            kwargs[name] = deserialize(value, jsattr.type)
        return cls(**kwargs)
