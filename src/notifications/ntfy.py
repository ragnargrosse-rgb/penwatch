import os

import requests


class NtfyNotifier:
    def __init__(self) -> None:
        self.server = os.getenv("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
        self.topic = os.getenv("NTFY_TOPIC")

        if not self.topic:
            raise RuntimeError("NTFY_TOPIC is not configured.")

    def send(
        self,
        title: str,
        message: str,
        url: str | None = None,
        priority: str = "default",
    ) -> None:
        headers = {
            "Title": title,
            "Priority": priority,
        }

        if url:
            headers["Click"] = url

        response = requests.post(
            f"{self.server}/{self.topic}",
            data=message.encode("utf-8"),
            headers=headers,
            timeout=15,
        )
        response.raise_for_status()
