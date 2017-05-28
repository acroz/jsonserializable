import jsonserializable
import pytest


IntArray = jsonserializable.Array[int]


def test_serialize_array():
    array = IntArray([1, 2, 3])
    assert array.serialize() == [1, 2, 3]


def test_deserialize_array():
    array = IntArray.deserialize([1, 2, 3])
    assert array == IntArray([1, 2, 3])
