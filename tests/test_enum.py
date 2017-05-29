import pytest
from jsonschema import ValidationError
from jsonserializable import Enum, List


class ExampleEnum(Enum):
    foo = 'foo'
    one = 1
    array = List[int]([1, 2])


EXAMPLE_SERIALIZATIONS = [
    (ExampleEnum.foo, 'foo'),
    (ExampleEnum.one, 1),
    (ExampleEnum.array, List[int]([1, 2]).serialize())
]


def test_serialize_enum():
    with pytest.raises(TypeError):
        ExampleEnum.serialize(object())


@pytest.mark.parametrize('member, data', EXAMPLE_SERIALIZATIONS)
def test_serialize_member(member, data):
    assert member.serialize() == data


@pytest.mark.parametrize('member, data', EXAMPLE_SERIALIZATIONS)
def test_deserialize_enum(member, data):
    assert ExampleEnum.deserialize(data) == member


@pytest.mark.parametrize('member, data', EXAMPLE_SERIALIZATIONS)
def test_deserialize_member(member, data):
    assert ExampleEnum.foo.deserialize(data) == member


def test_schema_enum():
    assert ExampleEnum.schema() == {'enum': ['foo', 1, [1, 2]]}


def test_schema_member():
    assert ExampleEnum.foo.schema() == {'enum': ['foo', 1,[1, 2]]}
