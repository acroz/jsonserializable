import pytest
from jsonschema import ValidationError
from jsonserializable import Dict


@pytest.mark.parametrize('data', [{}, {'one': 1, 'two': 2}])
def test_serialize(data):
    obj = Dict[int](data)
    assert obj.serialize() == data


@pytest.mark.parametrize('data', [{}, {'one': 1, 'two': 2}])
def test_deserialize(data):
    obj = Dict[int].deserialize(data)
    assert obj == Dict[int](data)


def test_schema():
    assert Dict[int].schema() == {
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
        Dict[int](data)


@pytest.mark.parametrize('data', [
    {'one': 'foo'},
    {'one': 1, 'two': 'bar'},
    [],
    1
])
def test_deserialize_invalid_schema(data):
    with pytest.raises(ValidationError):
        Dict[int].deserialize(data)


def test_deserialize_invalid_key_type():
    with pytest.raises(TypeError):
        Dict[int].deserialize({1: 1})


def test_repr():
    assert repr(Dict[int](one=1)) == "Dict[int]({'one': 1})"


def test_setitem():
    obj = Dict[int]()
    obj['foo'] = 1
    assert obj['foo'] == 1


@pytest.mark.parametrize('key', [1, ['foo']])
def test_setitem_invalid_key_type(key):
    obj = Dict[int]()
    with pytest.raises(TypeError):
        obj[key] = 1


@pytest.mark.parametrize('value', ['bar', [1]])
def test_setitem_invalid_value_type(value):
    obj = Dict[int]()
    with pytest.raises(TypeError):
        obj['foo'] = value


def test_no_type_argument():
    with pytest.raises(TypeError):
        Dict()


@pytest.mark.parametrize('typearg', [bytes, 'foo'])
def test_unsupported_type_argument(typearg):
    with pytest.raises(TypeError):
        Dict[typearg]


def test_second_type_argument():
    with pytest.raises(TypeError):
        Dict[int][int]


class IntDict(Dict[int]):  # type: ignore
    pass


@pytest.mark.parametrize('value', [Dict[int](one=1), IntDict(one=1)])
def test_isinstance_true(value):
    assert isinstance(value, Dict)
    assert isinstance(value, Dict[int])


def test_isinstance_false():
    assert not isinstance(Dict[int](one=1), IntDict)


@pytest.mark.parametrize('cls', [Dict[int], IntDict])
def test_issubclass_true(cls):
    assert issubclass(cls, Dict)
    assert issubclass(cls, Dict[int])


def test_issubclass_false():
    assert not issubclass(Dict[int], IntDict)
