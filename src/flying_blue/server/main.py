import argparse
import asyncio
import json
import logging

import websockets
from websockets.asyncio.server import ServerConnection, serve

from flying_blue.common.protocol import Message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logger = logging.getLogger(__name__)


class RelayServer:
    def __init__(self) -> None:
        self.clients: dict[ServerConnection, str] = {}

    async def handle_client(self, connection: ServerConnection) -> None:
        client = connection.remote_address
        logger.info("Client connected: %s", client)
        try:
            async for raw_message in connection:
                try:
                    message = Message.decode(raw_message)
                except (ValueError, TypeError, json.JSONDecodeError) as exc:
                    logger.warning("Invalid message from %s: %s", client, exc)
                    await connection.send(
                        Message(type="error", data={"message": "Invalid message"}).encode()
                    )
                    continue

                if message.type == "register":
                    role = message.data.get("role") if isinstance(message.data, dict) else None
                    if role not in {"sender", "receiver"}:
                        await connection.send(
                            Message(type="error", data={"message": "Invalid client role"}).encode()
                        )
                        continue
                    self.clients[connection] = role
                    logger.info("Registered %s as %s", client, role)
                    await connection.send(
                        Message(type="registered", data={"role": role}).encode()
                    )
                    continue

                sender_role = self.clients.get(connection)
                if sender_role == "sender":
                    receivers = [
                        client
                        for client, role in self.clients.items()
                        if role == "receiver"
                    ]
                    await asyncio.gather(
                        *(receiver.send(message.encode()) for receiver in receivers),
                        return_exceptions=True,
                    )
                    await connection.send(
                        Message(
                            type="ack",
                            data={"received_type": message.type, "receivers": len(receivers)},
                        ).encode()
                    )
                elif sender_role == "receiver":
                    targets = [
                        client
                        for client, role in self.clients.items()
                        if role == "sender"
                    ]
                    await asyncio.gather(
                        *(target.send(message.encode()) for target in targets),
                        return_exceptions=True,
                    )
                else:
                    await connection.send(
                        Message(type="error", data={"message": "Registration required"}).encode()
                    )
        except websockets.ConnectionClosed:
            logger.info("Client disconnected: %s", client)
        finally:
            self.clients.pop(connection, None)
            logger.info("Connection closed: %s", client)


async def run_server(host: str = "0.0.0.0", port: int = 8765) -> None:
    relay = RelayServer()
    logger.info("Starting relay server on %s:%s", host, port)
    async with serve(relay.handle_client, host, port):
        logger.info("Server is ready")
        await asyncio.Future()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the WebSocket relay server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    try:
        asyncio.run(run_server(host=args.host, port=args.port))
    except KeyboardInterrupt:
        logger.info("Server stopped")


if __name__ == "__main__":
    main()
