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


def test_repr():
    assert repr(Array[int]([1, 2, 3])) == 'Array[int]([1, 2, 3])'


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


def test_no_type_argument():
    with pytest.raises(TypeError):
        Array()


@pytest.mark.parametrize('typearg', [bytes, 'foo'])
def test_unsupported_type_argument(typearg):
    with pytest.raises(TypeError):
        Array[typearg]


def test_second_type_argument():
    with pytest.raises(TypeError):
        Array[int][int]


class IntArray(Array[int]):  # type: ignore
    pass


@pytest.mark.parametrize('value', [Array[int]([1, 2]), IntArray([1, 2])])
def test_isinstance_true(value):
    assert isinstance(value, Array)
    assert isinstance(value, Array[int])


def test_isinstance_false():
    assert not isinstance(Array[int]([1, 2]), IntArray)


@pytest.mark.parametrize('cls', [Array[int], IntArray])
def test_issubclass_true(cls):
    assert issubclass(cls, Array)
    assert issubclass(cls, Array[int])


def test_issubclass_false():
    assert not issubclass(Array[int], IntArray)
