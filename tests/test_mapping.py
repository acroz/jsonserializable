import pytest
from jsonschema import ValidationError
from jsonserializable import Mapping


@pytest.mark.parametrize('data', [{}, {'one': 1, 'two': 2}])
def test_serialize(data):
    mapping = Mapping[int](data)
    assert mapping.serialize() == data


@pytest.mark.parametrize('data', [{}, {'one': 1, 'two': 2}])
def test_deserialize(data):
    mapping = Mapping[int].deserialize(data)
    assert mapping == Mapping[int](data)


def test_schema():
    assert Mapping[int].schema() == {
        'type': 'object',
        'additionalProperties': {'type': 'number'}
    }


@pytest.mark.parametrize('data', [
    {'one': 'foo'},
    {'one': 1, 'two': 'bar'},
    {1: 1, 2: 2}
])
def test_construct_invalid_type(data):
    with pytest.raises(TypeError):
        Mapping[int](data)


@pytest.mark.parametrize('data', [
    {'one': 'foo'},
    {'one': 1, 'two': 'bar'},
    [],
    1
])
def test_deserialize_invalid_schema(data):
    with pytest.raises(ValidationError):
        Mapping[int].deserialize(data)


def test_deserialize_invalid_key_type():
    with pytest.raises(TypeError):
        Mapping[int].deserialize({1: 1})


def test_setitem_invalid_key_type():
    mapping = Mapping[int]()
    with pytest.raises(TypeError):
        mapping[1] = 1


def test_setitem_invalid_value_type():
    mapping = Mapping[int]()
    with pytest.raises(TypeError):
        mapping['foo'] = 'bar'
