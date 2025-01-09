"""
Ollama server communication
"""

import os
import logging

from .client import _APIManager, RequestAction

logger = logging.getLogger(__name__)

_OLLAMA_SERVER = os.getenv("OLLAMA_SERVER")
_OLLAMA_PORT = os.getenv("OLLAMA_PORT")
_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")


class OllamaAPI(_APIManager):
    """
    Manager for Ollama requests
    """

    # pylint: disable=R0903

    active = all([_OLLAMA_SERVER, _OLLAMA_PORT, _OLLAMA_MODEL])

    def __init__(self):
        logger.debug("Using Ollama: %s", self.active)

    async def generate_single_response(self, prompt: str) -> str | None:
        """
        Send a prompt to the Ollama server to have a response
        generated

        :param prompt: The prompt to send to the Ollama server
        :return: The returned response or None
        """
        url = f"http://{_OLLAMA_SERVER}:{_OLLAMA_PORT}/api/generate"

        if not self.active:
            return None

        payload = {"model": _OLLAMA_MODEL, "prompt": prompt, "stream": False}

        data: dict[str, str] | None = await self._request(
            RequestAction.POST, url, payload
        )
        if data is not None:
            return data["response"]

        return None

    async def generate_chat_response(
        self, messages: list[dict[str, str]]
    ) -> str | None:
        """
        Sends a collection of messages to the Ollama server to have a response
        generated

        :param messages: The messages to send to the server
        :return: The returned response or None
        """

        url = f"http://{_OLLAMA_SERVER}:{_OLLAMA_PORT}/api/chat"

        if not self.active:
            return None

        payload = {"model": _OLLAMA_MODEL, "messages": messages, "stream": False}

        data: dict[str, str | dict] | None = await self._request(
            RequestAction.POST, url, payload
        )
        if data is not None and isinstance(data["message"], dict):
            return data["message"]["content"]

        return None
