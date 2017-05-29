import pytest
from jsonserializable import serialize, deserialize, schema, List, Dict


@pytest.mark.parametrize('value, expected', [
    (2, 2),
    (3.4, 3.4),
    ('foo', 'foo'),
    (True, True),
    (List[int]([1, 2]), [1, 2]),
    (Dict[int](foo=1), {'foo': 1})
])
def test_serialize(value, expected):
    serialized = serialize(value)
    assert type(serialized) == type(expected)
    assert serialized == expected


def test_serialize_unsupported():
    with pytest.raises(TypeError):
        serialize(b'foo')


@pytest.mark.parametrize('value, target_type, expected', [
    (2, int, 2),
    (3.4, float, 3.4),
    ('foo', str, 'foo'),
    (True, bool, True),
    ([1, 2], List[int], List[int]([1, 2])),
    ({'foo': 1}, Dict[int], Dict[int](foo=1))
])
def test_deserialize(value, target_type, expected):
    deserialized = deserialize(value, target_type)
    assert type(deserialized) == target_type
    assert deserialized == expected


def test_deserialize_unsupported():
    with pytest.raises(TypeError):
        deserialize(b'foo', bytes)


@pytest.mark.parametrize('python_type, expected', [
    (int, {'type': 'number'}),
    (float, {'type': 'number'}),
    (str, {'type': 'string'}),
    (bool, {'type': 'boolean'}),
    (List[int], List[int].schema()),
    (Dict[int], Dict[int].schema())
])
def test_schema(python_type, expected):
    assert schema(python_type) == expected


def test_schema_unsupported():
    with pytest.raises(TypeError):
        schema(bytes)
