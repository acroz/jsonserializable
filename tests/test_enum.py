import pytest
from jsonschema import ValidationError
from jsonserializable import Enum, List


class ExampleEnum(Enum):
    foo = 'bar'
    one = 1
    array = List[int]([1, 2])


EXAMPLE_SERIALIZATIONS = [
    (ExampleEnum.foo, 'bar'),
    (ExampleEnum.one, 1),
    (ExampleEnum.array, List[int]([1, 2]).serialize())
]


def test_no_overwrite():
    with pytest.raises(TypeError):
        class TestClass(Enum):
            @property
            def prop(self):
                pass
            prop = 1  # noqa


def test_getattr():
    member = ExampleEnum.foo
    assert member.name == 'foo'
    assert member.value == 'bar'


def test_getattr_missing():
    with pytest.raises(AttributeError):
        ExampleEnum.other


def test_getitem():
    assert ExampleEnum['foo'] == ExampleEnum.foo


def test_getitem_missing():
    with pytest.raises(KeyError):
        ExampleEnum['other']


def test_fromvalue():
    assert ExampleEnum.from_value('bar') == ExampleEnum.foo


def test_fromvalue_unhashable():
    assert ExampleEnum.from_value(List[int]([1, 2])) == ExampleEnum.array


def test_fromvalue_missing():
    with pytest.raises(ValueError):
        ExampleEnum.from_value('other')


def test_fromvalue_missing_unhashable():
    with pytest.raises(ValueError):
        ExampleEnum.from_value(List[str](['foo', 'bar']))


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
    assert ExampleEnum.schema() == {'enum': ['bar', 1, [1, 2]]}


def test_schema_member():
    assert ExampleEnum.foo.schema() == {'enum': ['bar', 1,[1, 2]]}
