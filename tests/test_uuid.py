from uuid import UUID, uuid4
import pytest
from jsonschema import ValidationError
from jsonserializable import serialize, deserialize


def test_serialize():
    example_uuid = uuid4()
    assert serialize(example_uuid) == str(example_uuid)


@pytest.mark.parametrize('uuid_string', [
    '5ec220fb-e098-4062-b18f-6e30f2631f6c',
    '39B86590-453A-4AD4-9BFC-E8D8411AA65A',
    'fac470b7817f4251aeffdf5621149a1d'
])
def test_deserialize(uuid_string):
    assert deserialize(uuid_string, UUID) == UUID(uuid_string)


def test_deserialize_invalid():
    with pytest.raises(ValidationError):
        deserialize('invalid-uuid', UUID)
