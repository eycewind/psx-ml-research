from __future__ import annotations

from dataclasses import dataclass
import os
import urllib.request


@dataclass(frozen=True)
class NtfyConfig:
    base_url: str
    topic: str
    token: str | None = None

    @classmethod
    def from_env(cls) -> "NtfyConfig":
        base_url = os.environ.get("NTFY_URL", "").rstrip("/")
        topic = os.environ.get("NTFY_TOPIC", "")
        token = os.environ.get("NTFY_TOKEN") or None
        if not base_url:
            raise ValueError("NTFY_URL is required")
        if not topic:
            raise ValueError("NTFY_TOPIC is required")
        return cls(base_url=base_url, topic=topic, token=token)


def send_ntfy(*, config: NtfyConfig, title: str, message: str, priority: int = 3) -> None:
    url = f"{config.base_url}/{config.topic}"
    headers = {
        "Title": title,
        "Priority": str(priority),
        "Content-Type": "text/plain; charset=utf-8",
    }
    if config.token:
        headers["Authorization"] = f"Bearer {config.token}"
    req = urllib.request.Request(
        url,
        data=message.encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        if response.status >= 300:
            raise RuntimeError(f"ntfy returned HTTP {response.status}")
