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


async def send_information(host: str, port: int) -> None:
    uri = f"ws://{host}:{port}"
    logger.info("Connecting to %s", uri)

    async with connect(uri) as websocket:
        await websocket.send(Message(type="register", data={"role": "sender"}).encode())
        registration = Message.decode(await websocket.recv())
        if registration.type != "registered":
            raise RuntimeError(f"Server rejected sender: {registration.data}")
        logger.info("Sender registered")
        message = Message(
            type="information",
            data={
                "sender": "Python Sender",
                "message": "Hello from the sender!",
                "value": 123,
            },
        )
        await websocket.send(message.encode())
        logger.info("Information sent")

        response = Message.decode(await websocket.recv())
        logger.info("Server response: type=%s data=%s", response.type, response.data)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the WebSocket sender")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    try:
        asyncio.run(send_information(host=args.host, port=args.port))
    except ConnectionRefusedError:
        logger.error("Could not connect to receiver")
    except Exception:
        logger.exception("Unexpected error")


if __name__ == "__main__":
    main()
