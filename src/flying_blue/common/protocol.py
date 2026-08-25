import json
from dataclasses import dataclass
from typing import Any


@dataclass
class Message:
    type: str
    data: Any

    def encode(self) -> str:
        return json.dumps({
            "type": self.type,
            "data": self.data,
        })

    @staticmethod
    def decode(raw: str) -> "Message":
        payload = json.loads(raw)

        if not isinstance(payload, dict):
            raise ValueError("Message must be a JSON object")
        if "type" not in payload:
            raise ValueError("Message has no 'type'")
        if "data" not in payload:
            raise ValueError("Message has no 'data'")

        return Message(
            type=payload["type"],
            data=payload["data"],
        )
