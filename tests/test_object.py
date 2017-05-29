import pytest
from jsonschema import ValidationError
from jsonserializable import Object, Attribute


class ExampleObject(Object):
    integer = Attribute(int)
    string = Attribute(str)
    optional = Attribute(str, optional=True)


class OtherObject(ExampleObject):
    pass


def test_equal():
    value1 = ExampleObject(integer=1, string='foo')
    value2 = ExampleObject(integer=1, string='foo')
    assert value1 == value2


@pytest.mark.parametrize('value2', [
    ExampleObject(integer=1, string='bar'),
    ExampleObject(integer=1, string='foo', optional='bar'),
    OtherObject(integer=1, string='foo'),
    []
])
def test_not_equal(value2):
    value1 = ExampleObject(integer=1, string='foo')
    assert value1 != value2


def test_serialize():
    obj = ExampleObject(integer=1, string='foo')
    assert obj.serialize() == {'integer': 1, 'string': 'foo'}


def test_serialize_optional():
    obj = ExampleObject(integer=1, string='foo', optional='bar')
    expected = {'integer': 1, 'string': 'foo', 'optional': 'bar'}
    assert obj.serialize() == expected


def test_deserialize():
    obj = ExampleObject.deserialize({'integer': 1, 'string': 'foo'})
    assert obj == ExampleObject(integer=1, string='foo')


def test_deserialize_optional():
    obj = ExampleObject.deserialize(
        {'integer': 1, 'string': 'foo', 'optional': 'bar'}
    )
    assert obj == ExampleObject(integer=1, string='foo', optional='bar')


def test_schema():
    assert ExampleObject.schema() == {
        'type': 'object',
        'properties': {
            'integer': {'type': 'number'},
            'string': {'type': 'string'},
            'optional': {'type': 'string'}
        },
        'required': ['integer', 'string'],
        'additionalProperties': False
    }


def test_construct_invalid_type():
    with pytest.raises(TypeError):
        ExampleObject(integer=1, string=2)


def test_construct_missing_attribute():
    with pytest.raises(TypeError):
        ExampleObject(integer=1)


def test_construct_extra_attribute():
    with pytest.raises(TypeError):
        ExampleObject(integer=1, string='foo', extra=True)


@pytest.mark.parametrize('data', [
    {'integer': 1, 'string': 1},
    {'integer': 1, 'string': 'foo', 'optional': 1},
    {'integer': 1},
    {'integer': 1, 'string': 'foo', 'extra': True}
])
def test_deserialize_invalid_schema(data):
    with pytest.raises(ValidationError):
        ExampleObject.deserialize(data)


def test_repr():
    obj = ExampleObject(integer=1, string='foo')
    expected = "ExampleObject(integer=1, string='foo', optional=None)"
    assert repr(obj) == expected


@pytest.mark.parametrize('value', ['foobar', None])
def test_setattr_optional(value):
    obj = ExampleObject(integer=1, string='foo', optional='bar')
    obj.optional = value
    assert obj.optional == value


@pytest.mark.parametrize('value', [1, ['bar'], None])
def test_setattr_invalid_type(value):
    obj = ExampleObject(integer=1, string='foo')
    with pytest.raises(TypeError):
        obj.string = value


@pytest.mark.parametrize('value', [1, ['bar']])
def test_setattr_optional_invalid_type(value):
    obj = ExampleObject(integer=1, string='foo')
    with pytest.raises(TypeError):
        obj.optional = value


def test_setattr_nonexistent_attribute():
    obj = ExampleObject(integer=1, string='foo')
    with pytest.raises(AttributeError):
        obj.non_existent = 1
