import argparse
import asyncio
import logging

from websockets.asyncio.client import connect

from flying_blue.common.protocol import Message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logger = logging.getLogger(__name__)


async def receive_information(host: str, port: int) -> None:
    uri = f"ws://{host}:{port}"
    logger.info("Connecting to server at %s", uri)

    async with connect(uri) as websocket:
        await websocket.send(Message(type="register", data={"role": "receiver"}).encode())
        registration = Message.decode(await websocket.recv())
        if registration.type != "registered":
            raise RuntimeError(f"Server rejected receiver: {registration.data}")

        logger.info("Receiver registered")
        async for raw_message in websocket:
            message = Message.decode(raw_message)
            logger.info("Received message: type=%s data=%s", message.type, message.data)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the WebSocket receiver client")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    try:
        asyncio.run(receive_information(host=args.host, port=args.port))
    except KeyboardInterrupt:
        logger.info("Receiver stopped")


if __name__ == "__main__":
    main()
