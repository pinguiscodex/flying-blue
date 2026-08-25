import argparse
import asyncio
import logging
import subprocess

from websockets.asyncio.client import connect

from flying_blue.common.protocol import Message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logger = logging.getLogger(__name__)


def execute_command(command: str) -> dict:
    logger.info("Executing command: %s", command)
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return {
            "command": command,
            "output": result.stdout + result.stderr,
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "command": command,
            "output": "Command timed out after 30 seconds",
            "exit_code": -1,
        }
    except Exception as exc:
        return {
            "command": command,
            "output": str(exc),
            "exit_code": -1,
        }


async def receive_commands(host: str, port: int) -> None:
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
            if message.type == "command":
                command = message.data.get("command", "")
                result = execute_command(command)
                await websocket.send(Message(type="result", data=result).encode())
                logger.info("Result sent for command: %s (exit_code=%s)", command, result["exit_code"])
            else:
                logger.info("Received message: type=%s data=%s", message.type, message.data)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the WebSocket receiver client")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    try:
        asyncio.run(receive_commands(host=args.host, port=args.port))
    except KeyboardInterrupt:
        logger.info("Receiver stopped")


if __name__ == "__main__":
    main()
