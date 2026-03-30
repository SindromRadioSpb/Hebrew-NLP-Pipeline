# kadima/llm/client.py
"""HTTP клиент для llama.cpp server (Dicta-LM 3.0)."""

import logging
from typing import Dict, List, Optional
import httpx

logger = logging.getLogger(__name__)


class LlamaCppClient:
    def __init__(self, server_url: str = "http://localhost:8081", timeout: int = 30):
        self.server_url = server_url.rstrip("/")
        self.client = httpx.Client(base_url=self.server_url, timeout=timeout)

    def is_loaded(self) -> bool:
        try:
            return self.client.get("/health").status_code == 200
        except Exception:
            return False

    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7, stop: Optional[List[str]] = None) -> str:
        payload = {"prompt": prompt, "n_predict": max_tokens, "temperature": temperature}
        if stop:
            payload["stop"] = stop
        resp = self.client.post("/completion", json=payload)
        resp.raise_for_status()
        return resp.json().get("content", "")

    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 512) -> str:
        parts = []
        for msg in messages:
            if msg["role"] == "user":
                parts.append(f"<s>[INST] {msg['content']} [/INST]")
            elif msg["role"] == "assistant":
                parts.append(f"{msg['content']}</s>")
        return self.generate("\n".join(parts), max_tokens=max_tokens)
