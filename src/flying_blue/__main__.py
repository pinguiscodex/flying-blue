import sys

from flying_blue.receiver.main import main as receiver_main
from flying_blue.server.main import main as server_main
from flying_blue.sender.main import main as sender_main


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m flying_blue sender")
        print("  python -m flying_blue server")
        print("  python -m flying_blue receiver")
        return

    mode = sys.argv[1].lower()
    sys.argv = [sys.argv[0], *sys.argv[2:]]

    if mode == "sender":
        sender_main()
    elif mode == "server":
        server_main()
    elif mode == "receiver":
        receiver_main()
    else:
        print(f"Unknown mode: {mode}")


if __name__ == "__main__":
    main()
