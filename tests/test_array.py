import pytest
from jsonschema import ValidationError
from jsonserializable import Array


@pytest.mark.parametrize('data', [[], [1, 2, 3]])
def test_serialize(data):
    array = Array[int](data)
    assert array.serialize() == data


@pytest.mark.parametrize('data', [[], [1, 2, 3]])
def test_deserialize(data):
    array = Array[int].deserialize(data)
    assert array == Array[int](data)


def test_schema():
    assert Array[int].schema() == {
        'type': 'array',
        'items': {'type': 'number'}
    }


@pytest.mark.parametrize('data', [['foo'], [1, 2, 'bar']])
def test_construct_invalid_type(data):
    with pytest.raises(TypeError):
        Array[int](data)


@pytest.mark.parametrize('data', [['foo'], [1, 2, 'bar'], {}, 1])
def test_deserialize_invalid_schema(data):
    with pytest.raises(ValidationError):
        Array[int].deserialize(data)


def test_setitem():
    array = Array[int]([1, 2, 3])
    array[1] = 10
    assert array[1] == 10
    assert len(array) == 3


@pytest.mark.parametrize('data', ['foo', [], [1]])
def test_setitem_invalid_type(data):
    array = Array[int]([1, 2, 3])
    with pytest.raises(TypeError):
        array[1] = data


def test_insert():
    array = Array[int]([1, 2, 3])
    array.insert(1, 10)
    assert array[1] == 10
    assert len(array) == 4


@pytest.mark.parametrize('data', ['foo', [], [1]])
def test_insert_invalid_type(data):
    array = Array[int]([1, 2, 3])
    with pytest.raises(TypeError):
        array.insert(1, data)
