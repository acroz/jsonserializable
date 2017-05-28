import pytest
from jsonschema import ValidationError
import jsonserializable


IntArray = jsonserializable.Array[int]


@pytest.mark.parametrize('data', [[], [1, 2, 3]])
def test_serialize_array(data):
    array = IntArray(data)
    assert array.serialize() == data


@pytest.mark.parametrize('data', [[], [1, 2, 3]])
def test_deserialize_array(data):
    array = IntArray.deserialize(data)
    assert array == IntArray(data)


def test_schema():
    assert IntArray.schema() == {
        'type': 'array',
        'items': {'type': 'number'}
    }


@pytest.mark.parametrize('data', [['foo'], [1, 2, 'bar']])
def test_invalid_type(data):
    with pytest.raises(TypeError):
        IntArray(data)


@pytest.mark.parametrize('data', [['foo'], [1, 2, 'bar']])
def test_invalid_schema(data):
    with pytest.raises(ValidationError):
        IntArray.deserialize(data)
