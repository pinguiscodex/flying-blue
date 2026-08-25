import asyncio
import sys

import pytest

import flying_blue
from flying_blue.__main__ import main as package_main
from flying_blue.common.protocol import Message
from flying_blue.receiver.main import receive_commands, execute_command
from flying_blue.sender.main import send_command
from flying_blue.server.main import RelayServer


class FakeConnection:
    def __init__(self, messages=None, *, remote_address=("127.0.0.1", 1234)):
        self.messages = list(messages or [])
        self.sent = []
        self.remote_address = remote_address

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.messages:
            raise StopAsyncIteration
        return self.messages.pop(0)

    async def send(self, payload):
        self.sent.append(payload)


class FakeWebSocket:
    def __init__(self, queued_messages=None):
        self.queued_messages = list(queued_messages or [])
        self.sent = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.queued_messages:
            raise StopAsyncIteration
        return self.queued_messages.pop(0)

    async def send(self, payload):
        self.sent.append(payload)

    async def recv(self):
        if not self.queued_messages:
            raise AssertionError("No queued message available")
        return self.queued_messages.pop(0)


def test_package_main_dispatches_modes(monkeypatch):
    calls = []

    monkeypatch.setattr(flying_blue.__main__, "sender_main", lambda: calls.append("sender"))
    monkeypatch.setattr(flying_blue.__main__, "server_main", lambda: calls.append("server"))
    monkeypatch.setattr(flying_blue.__main__, "receiver_main", lambda: calls.append("receiver"))

    for mode, expected in (("sender", "sender"), ("server", "server"), ("receiver", "receiver")):
        monkeypatch.setattr(sys, "argv", ["prog", mode, "--host", "localhost", "--port", "9000"])
        package_main()
        assert calls[-1] == expected


def test_message_decode_rejects_non_object_json():
    with pytest.raises(ValueError, match="JSON object"):
        Message.decode("[]")


def test_server_rejects_invalid_registration_role():
    async def scenario():
        server = RelayServer()
        connection = FakeConnection([Message(type="register", data={"role": "admin"}).encode()])

        await server.handle_client(connection)

        assert connection.sent == [
            Message(type="error", data={"message": "Invalid client role"}).encode()
        ]

    asyncio.run(scenario())


def test_server_relay_command_from_sender_to_receivers():
    async def scenario():
        server = RelayServer()
        sender = FakeConnection([Message(type="command", data={"command": "ls"}).encode()])
        receiver = FakeConnection()

        server.clients[sender] = "sender"
        server.clients[receiver] = "receiver"

        await server.handle_client(sender)

        assert len(receiver.sent) == 1
        assert Message.decode(receiver.sent[0]).type == "command"
        assert Message.decode(receiver.sent[0]).data == {"command": "ls"}
        assert Message.decode(sender.sent[0]).type == "ack"
        assert Message.decode(sender.sent[0]).data["receivers"] == 1

    asyncio.run(scenario())


def test_server_relay_result_from_receiver_to_senders():
    async def scenario():
        server = RelayServer()
        receiver = FakeConnection([
            Message(type="result", data={"command": "ls", "output": "file1\n", "exit_code": 0}).encode()
        ])
        sender = FakeConnection()

        server.clients[receiver] = "receiver"
        server.clients[sender] = "sender"

        await server.handle_client(receiver)

        assert len(sender.sent) == 1
        decoded = Message.decode(sender.sent[0])
        assert decoded.type == "result"
        assert decoded.data["command"] == "ls"
        assert decoded.data["exit_code"] == 0

    asyncio.run(scenario())


def test_execute_command_runs_shell_command():
    result = execute_command("echo hello")
    assert result["exit_code"] == 0
    assert "hello" in result["output"]


def test_execute_command_returns_error_on_failure():
    result = execute_command("exit 1")
    assert result["exit_code"] == 1


def test_sender_function_registers_and_sends_command(monkeypatch):
    async def scenario():
        websocket = FakeWebSocket([
            Message(type="registered", data={"role": "sender"}).encode(),
            Message(type="result", data={"command": "ls", "output": "file1\n", "exit_code": 0}).encode(),
        ])

        def fake_connect(uri):
            assert uri == "ws://example.com:9000"
            return websocket

        monkeypatch.setattr("flying_blue.sender.main.connect", fake_connect)
        await send_command("example.com", 9000, "ls")

        assert websocket.sent[0] == Message(type="register", data={"role": "sender"}).encode()
        decoded = Message.decode(websocket.sent[1])
        assert decoded.type == "command"
        assert decoded.data == {"command": "ls"}

    asyncio.run(scenario())


def test_receiver_function_receives_commands(monkeypatch):
    async def scenario():
        websocket = FakeWebSocket([
            Message(type="registered", data={"role": "receiver"}).encode(),
            Message(type="command", data={"command": "echo test"}).encode(),
        ])

        def fake_connect(uri):
            assert uri == "ws://example.com:9000"
            return websocket

        monkeypatch.setattr("flying_blue.receiver.main.connect", fake_connect)
        await receive_commands("example.com", 9000)

        assert websocket.sent[0] == Message(type="register", data={"role": "receiver"}).encode()
        result_msg = Message.decode(websocket.sent[1])
        assert result_msg.type == "result"
        assert result_msg.data["command"] == "echo test"
        assert result_msg.data["exit_code"] == 0
        assert "test" in result_msg.data["output"]

    asyncio.run(scenario())
