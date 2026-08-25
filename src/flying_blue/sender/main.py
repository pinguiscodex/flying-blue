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


async def send_command(host: str, port: int, command: str) -> None:
    uri = f"ws://{host}:{port}"
    logger.info("Connecting to %s", uri)

    async with connect(uri) as websocket:
        await websocket.send(Message(type="register", data={"role": "sender"}).encode())
        registration = Message.decode(await websocket.recv())
        if registration.type != "registered":
            raise RuntimeError(f"Server rejected sender: {registration.data}")
        logger.info("Sender registered")

        message = Message(
            type="command",
            data={"command": command},
        )
        await websocket.send(message.encode())
        logger.info("Command sent: %s", command)

        async for raw_message in websocket:
            response = Message.decode(raw_message)
            if response.type == "result":
                logger.info(
                    "Result — command: %s, exit_code: %s",
                    response.data.get("command"),
                    response.data.get("exit_code"),
                )
                output = response.data.get("output", "")
                if output:
                    logger.info("Output:\n%s", output)
                break
            else:
                logger.info("Server response: type=%s data=%s", response.type, response.data)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the WebSocket sender")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--command", required=True, help="Command string to execute on receivers")
    args = parser.parse_args()

    try:
        asyncio.run(send_command(host=args.host, port=args.port, command=args.command))
    except ConnectionRefusedError:
        logger.error("Could not connect to server")
    except Exception:
        logger.exception("Unexpected error")


if __name__ == "__main__":
    main()
