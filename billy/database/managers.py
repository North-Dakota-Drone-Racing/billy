"""
Perform Database transations
"""

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, delete, update, func

from ..api import MultiGPAPI
from .objects import _ObjectBase, DiscordServer, MGPEvent

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Provides database actions

    :return: _description_
    """

    _multigp = MultiGPAPI()

    def __init__(self, *, filename: str = ":memory:") -> None:
        """
        Class initializer

        :param str filename: The filename to save the database as, defaults to ":memory:"
        """
        self.engine = create_async_engine(f"sqlite+aiosqlite:///{filename}", echo=False)
        self._session_maker = self.new_session_maker()

    def new_session_maker(self, **kwargs) -> async_sessionmaker[AsyncSession]:
        """
        A wrapper for async_sessionmaker with `autoflush`, `autocommit`, and
        `expire_on_commit` set to `False`. Automatically set the engine

        :return async_sessionmaker[AsyncSession]: Session manager used for generating
        new database sessions.
        """
        defaults = {}
        defaults["autoflush"] = False
        defaults["autocommit"] = False
        defaults["expire_on_commit"] = False

        kwargs_ = defaults | kwargs

        return async_sessionmaker(self.engine, **kwargs_)

    async def setup(self) -> None:
        """
        Setup the database connection. Used at server startup.
        """

        async with self.engine.begin() as conn:
            await conn.run_sync(_ObjectBase.metadata.create_all)

    async def shutdown(self) -> None:
        """
        Shutdown the database connection.
        """

        await self.engine.dispose()

    async def get_server_count_by_chapter(self, chapter_id: str) -> int:
        """
        Count the

        :return: _description_
        """

        statement = (
            select(func.count())
            .select_from(DiscordServer)
            .where(DiscordServer.chapter_id == chapter_id)
        )
        async with self._session_maker() as session:
            result = await session.scalar(statement)

        return 0 if result is None else result

    async def set_server_configuration(
        self, server_id: int, channel_id: int, mgp_api_key: str
    ) -> dict | None:
        """
        Set configuration values for a discord server

        :param server_id: The discord server to set configs for
        :param channel_id: The id of the announcement channel
        :param mgp_apikey: The MultiGP api key for the chapter
        :return: The chapter info or None
        """

        chapter_info = await self._multigp.pull_chapter(mgp_api_key)
        if chapter_info is not None:
            logger.debug("Pulled chapter info for %s", {chapter_info["chapterName"]})
            mgp_chapter_id = chapter_info["chapterId"]
        else:
            return None

        find_statement = select(DiscordServer.id).where(
            DiscordServer.server_id == server_id
        )
        async with self._session_maker() as session:
            server_entry_id = await session.scalar(find_statement)

            if server_entry_id is None:
                chapter = DiscordServer(
                    server_id, channel_id, mgp_chapter_id, mgp_api_key
                )
                session.add(chapter)
            else:
                modify_statement = (
                    update(DiscordServer)
                    .where(DiscordServer.id == server_entry_id)
                    .values(
                        channel_id=channel_id,
                        chapter_id=mgp_chapter_id,
                        api_key=mgp_api_key,
                    )
                )
                await session.execute(modify_statement)

            await session.commit()

        return chapter_info

    async def get_server_info(self, server_id: int) -> DiscordServer | None:
        """
        Get the chapter information from the server's discord id.

        :param server_id: The server id
        :return: The chapter info
        """

        find_statement = select(DiscordServer).where(
            DiscordServer.server_id == server_id
        )
        async with self._session_maker() as session:
            result = await session.scalar(find_statement)

        return result

    async def get_servers(self) -> AsyncGenerator[DiscordServer, None]:
        """
        Stream all chapters from the database

        :yield: Chapters
        """
        statement = select(DiscordServer)
        async with self._session_maker() as session:
            result = await session.stream_scalars(statement)
            async for chapter in result:
                yield chapter

    async def get_chapter_servers(
        self, chapter_id: str
    ) -> AsyncGenerator[DiscordServer, None]:
        """
        Get all instances of a chapter based on the chapter_id

        :yield: Chapters
        """
        statement = select(DiscordServer).where(DiscordServer.chapter_id == chapter_id)
        async with self._session_maker() as session:
            result = await session.stream_scalars(statement)
            async for chapter in result:
                yield chapter

    async def remove_discord_server(self, discord_id: int) -> None:
        """
        Removes a discord server from the database

        :param discord_id: ID of the discord server
        """

        statement = delete(DiscordServer).where(DiscordServer.server_id == discord_id)
        async with self._session_maker() as session:
            await session.execute(statement)
            await session.commit()

    async def add_chapter_races(self, races: list[tuple]) -> None:
        """
        Adds a collection of races to the database

        :param races: _description_
        """

        races_ = [MGPEvent(*race) for race in races]
        async with self._session_maker() as session:
            session.add_all(races_)
            await session.commit()

    async def get_races(self) -> AsyncGenerator[MGPEvent]:
        """
        Get all events as a stream

        :param chapter_id: chapter id of the event
        :yield: Events for the chapter
        """

        statement = select(MGPEvent)
        async with self._session_maker() as session:
            result = await session.stream_scalars(statement)
            async for event in result:
                yield event

    async def get_chapter_race_ids(self, chapter_id: str) -> set[str]:
        """
        Get all events for a chapter as a stream

        :param chapter_id: chapter id of the event
        :yield: Events for the chapter
        """

        statement = select(MGPEvent.event_id).where(MGPEvent.chapter_id == chapter_id)
        async with self._session_maker() as session:
            results: set[str] = set()
            for result in await session.scalars(statement):
                results.add(str(result))

            return results

    async def remove_event(self, event_id: str) -> None:
        """
        Removes a MultiGP event from the database

        :param event_id: ID of the discord event
        """

        statement = delete(MGPEvent).where(MGPEvent.event_id == event_id)
        async with self._session_maker() as session:
            await session.execute(statement)
            await session.commit()

    async def remove_events_by_event_id(self, event_ids: list[str]) -> None:
        """
        Removes events by provided ids

        :param event_ids: Event ids to remove
        """

        statement = delete(MGPEvent).where(MGPEvent.event_id.in_(event_ids))
        async with self._session_maker() as session:
            await session.execute(statement)
            await session.commit()

    async def remove_event_by_chapter_id(self, chapter_id: str) -> None:
        """
        Removes a discord server from the database by chapter id

        :param event_id: ID of the chapter id
        """

        statement = delete(MGPEvent).where(MGPEvent.chapter_id == chapter_id)
        async with self._session_maker() as session:
            await session.execute(statement)
            await session.commit()
