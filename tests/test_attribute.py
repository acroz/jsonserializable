import pytest
from jsonserializable import Attribute


def test_creation():
    attr = Attribute(int)
    assert attr.type == int
    assert attr.optional is False


def test_invalid_type():
    with pytest.raises(TypeError):
        Attribute(bytes)


def test_repr():
    attr = Attribute(int)
    assert repr(attr) == 'Attribute(type={}, optional=False)'.format(repr(int))
