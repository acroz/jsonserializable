import pytest
from jsonserializable import serialize, deserialize, Array, Mapping


@pytest.mark.parametrize('value, expected', [
    (2, 2),
    (3.4, 3.4),
    ('foo', 'foo'),
    (True, True),
    (Array[int]([1, 2]), [1, 2]),
    (Mapping[int](foo=1), {'foo': 1})
])
def test_serialize(value, expected):
    serialized = serialize(value)
    assert type(serialized) == type(expected)
    assert serialized == expected


@pytest.mark.parametrize('value, target_type, expected', [
    (2, int, 2),
    (3.4, float, 3.4),
    ('foo', str, 'foo'),
    (True, bool, True),
    ([1, 2], Array[int], Array[int]([1, 2])),
    ({'foo': 1}, Mapping[int], Mapping[int](foo=1))
])
def test_deserialize(value, target_type, expected):
    deserialized = deserialize(value, target_type)
    assert type(deserialized) == target_type
    assert deserialized == expected


def test_serialize_unsupported():
    with pytest.raises(TypeError):
        serialize(b'foo')


def test_deserialize_unsupported():
    with pytest.raises(TypeError):
        deserialize(b'foo', bytes)
