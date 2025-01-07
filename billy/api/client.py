"""
Data manager abstractions
"""

import logging
from enum import Enum
from typing import TypeVar

import httpx

logger = logging.Logger(__name__)
"""Module logger"""

_client = httpx.AsyncClient(limits=httpx.Limits(keepalive_expiry=30), timeout=15)
"""Client for API requests"""

T = TypeVar("T", bound=bool | str | int | dict)
"""Generic used for typing"""


class RequestAction(str, Enum):
    """
    Common request methods
    """

    GET = "GET"
    """Represents a GET action"""
    POST = "POST"
    """Represents a POST action"""
    PUT = "PUT"
    """Represents a PUT action"""
    PATCH = "PATCH"
    """Represents a PATCH action"""
    DELETE = "DELETE"
    """Represents a DELETE action"""


class _APIManager:
    """
    Base manager for API access
    """

    # pylint: disable=R0903

    async def _request(
        self,
        request_type: RequestAction,
        url: str,
        json_request: dict | None,
    ) -> dict[str, T] | None:
        """
        Make a request to an API server

        :param request_type: The type of request to make
        :param url: The url for the API request
        :param json_request: The payload for the request
        :return: The parsed json response from the server
        """
        try:
            response = await _client.request(request_type, url, json=json_request)
        except httpx.ConnectError:
            logger.error("Connection to API server failed")
            return None
        except httpx.ReadTimeout:
            logger.error("Response not recieved form API server")
            return None

        return response.json()
