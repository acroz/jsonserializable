import pytest
from jsonserializable import (
    serialize, deserialize
)


@pytest.mark.parametrize('value', [2, 3.4, 'foo', True])
def test_serialize_simple(value):
    """ Serialized simple types should be the same as the input. """
    serialized = serialize(value)
    assert serialized == value
    assert type(serialized) == type(value)


@pytest.mark.parametrize('value,target_type', [
    (2, int),
    (3.4, float),
    ('foo', str),
    (True, bool)
])
def test_deserialize_simple(value, target_type):
    """ Deserialized simple types should be the same as the input. """
    deserialized = deserialize(value, target_type)
    assert deserialized == value
    assert type(deserialized) == target_type


@pytest.mark.parametrize('value', [b'bar', list()])
def test_serialize_unsupported(value):
    with pytest.raises(TypeError):
        serialize(value)
