import pytest

from flying_blue.common.protocol import Message


def test_message_round_trip() -> None:
    message = Message(type="information", data={"value": 42})

    assert Message.decode(message.encode()) == message


def test_decode_requires_type() -> None:
    with pytest.raises(ValueError, match="no 'type'"):
        Message.decode('{"data": 42}')


def test_decode_requires_data() -> None:
    with pytest.raises(ValueError, match="no 'data'"):
        Message.decode('{"type": "information"}')
