import pytest
from jsonschema import ValidationError
from jsonserializable import List


@pytest.mark.parametrize('data', [[], [1, 2, 3]])
def test_serialize(data):
    obj = List[int](data)
    assert obj.serialize() == data


@pytest.mark.parametrize('data', [[], [1, 2, 3]])
def test_deserialize(data):
    obj = List[int].deserialize(data)
    assert obj == List[int](data)


def test_schema():
    assert List[int].schema() == {
        'type': 'array',
        'items': {'type': 'number'}
    }


@pytest.mark.parametrize('data', [['foo'], [1, 2, 'bar']])
def test_construct_invalid_type(data):
    with pytest.raises(TypeError):
        List[int](data)


@pytest.mark.parametrize('data', [['foo'], [1, 2, 'bar'], {}, 1])
def test_deserialize_invalid_schema(data):
    with pytest.raises(ValidationError):
        List[int].deserialize(data)


def test_repr():
    assert repr(List[int]([1, 2, 3])) == 'List[int]([1, 2, 3])'


def test_setitem():
    obj = List[int]([1, 2, 3])
    obj[1] = 10
    assert obj[1] == 10
    assert len(obj) == 3


@pytest.mark.parametrize('data', ['foo', [], [1]])
def test_setitem_invalid_type(data):
    obj = List[int]([1, 2, 3])
    with pytest.raises(TypeError):
        obj[1] = data


def test_insert():
    obj = List[int]([1, 2, 3])
    obj.insert(1, 10)
    assert obj[1] == 10
    assert len(obj) == 4


@pytest.mark.parametrize('data', ['foo', [], [1]])
def test_insert_invalid_type(data):
    obj = List[int]([1, 2, 3])
    with pytest.raises(TypeError):
        obj.insert(1, data)


def test_no_type_argument():
    with pytest.raises(TypeError):
        List()


@pytest.mark.parametrize('typearg', [bytes, 'foo'])
def test_unsupported_type_argument(typearg):
    with pytest.raises(TypeError):
        List[typearg]


def test_second_type_argument():
    with pytest.raises(TypeError):
        List[int][int]


class IntList(List[int]):  # type: ignore
    pass


@pytest.mark.parametrize('value', [List[int]([1, 2]), IntList([1, 2])])
def test_isinstance_true(value):
    assert isinstance(value, List)
    assert isinstance(value, List[int])


def test_isinstance_false():
    assert not isinstance(List[int]([1, 2]), IntList)


@pytest.mark.parametrize('cls', [List[int], IntList])
def test_issubclass_true(cls):
    assert issubclass(cls, List)
    assert issubclass(cls, List[int])


def test_issubclass_false():
    assert not issubclass(List[int], IntList)
