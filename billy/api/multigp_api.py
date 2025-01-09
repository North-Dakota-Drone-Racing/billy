"""
API connections to MultiGP
"""

import logging

from .client import _APIManager, RequestAction

logger = logging.getLogger(__name__)


BASE_API_URL = "https://www.multigp.com/mgp/multigpwebservice"
"""MultiGP API base URL"""


class MultiGPAPI(_APIManager):
    """
    The primary class used to interact with the MultiGP RaceSync API

    .. seealso::

        https://www.multigp.com/apidocumentation/
    """

    async def pull_chapter(self, api_key: str) -> dict | None:
        """
        Get chapter data for an API key

        :param api_key: The api key for the chapter
        :return: The chapter data or None
        """

        url = f"{BASE_API_URL}/chapter/findChapterFromApiKey"
        data = {"apiKey": api_key}

        response_data: dict | None = await self._request(RequestAction.POST, url, data)

        if response_data is not None and response_data["status"]:
            return response_data

        return None

    async def pull_races(
        self, chapter_id: str, api_key: str
    ) -> list[dict[str, str]] | None:
        """
        Pull race data for a chapter

        :param chapter_id: The the id of the chapter
        :param api_key: The api key for the chapter
        :return: Races for chapter or None
        """

        url = f"{BASE_API_URL}/race/listForChapter?chapterId={chapter_id}"
        data = {"apiKey": api_key}

        response_data: dict | None = await self._request(RequestAction.POST, url, data)

        if response_data is not None and response_data["status"]:
            return response_data["data"]

        return None

    async def pull_race_data(self, race_id: str, api_key: str) -> dict | None:
        """
        Pull data for race

        :param race_id: The id of the race to pull
        :param api_key: The api key for the chapter
        :return: The race data or None
        """

        url = f"{BASE_API_URL}/race/view?id={race_id}"
        data = {"apiKey": api_key}

        response_data: dict | None = await self._request(RequestAction.POST, url, data)

        if response_data is not None and response_data["status"]:
            return response_data["data"]

        return None
