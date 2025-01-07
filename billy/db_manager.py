import logging
import multigpAPI
import db_types
import aiosqlite
import sqlite3
import asyncio

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


logger = logging.getLogger(__name__)

database_file = "/billy/files/database.db"


class DatabaseManager:

    def __init__(self, *, filename: str = ":memory:") -> None:
        """
        Class initializer

        :param str filename: The filename to save the database as, defaults to ":memory:"
        """

        self.engine = create_async_engine(f"sqlite+aiosqlite:///{filename}", echo=False)

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
            await conn.run_sync(_RaceBase.metadata.create_all)


def estabilsh_db() -> None:
    connection = sqlite3.connect(database_file)
    cursor = connection.cursor()

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS chapter(discord_serverId INTEGER, discord_channelId INTEGER, mgp_chapterId TEXT, mgp_apikey TEXT)"
    )
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS race(mgp_raceId TEXT, mgp_chapterId TEXT, discord_eventId INTEGER)"
    )

    cursor.close()
    connection.close()


async def set_serverConfiguration(
    discord_serverId: int, discord_channelId: int, mgp_apikey: str
) -> dict:
    chapter_info = await multigpAPI.pull_chapter(mgp_apikey)
    if chapter_info and chapter_info["status"]:
        logger.debug(f"Pulled chapter info for {chapter_info['chapterName']}")
        mgp_chapterId = chapter_info["chapterId"]
    else:
        return False

    async with aiosqlite.connect(database_file) as db:

        count = await db.execute(
            "SELECT COUNT(*) FROM chapter WHERE discord_serverId=?", (discord_serverId,)
        )
        row = await count.fetchone()
        if row[0] > 0:
            await db.execute(
                f"UPDATE chapter SET discord_channelId=?, mgp_apikey=?, mgp_chapterId=? WHERE discord_serverId=?",
                (discord_channelId, mgp_apikey, mgp_chapterId, discord_serverId),
            )
            await db.commit()
        else:
            await db.execute(
                "INSERT INTO chapter (discord_serverId, discord_channelId, mgp_chapterId, mgp_apikey) VALUES(?, ?, ?, ?)",
                (discord_serverId, discord_channelId, mgp_chapterId, mgp_apikey),
            )
            await db.commit()

    return chapter_info


async def get_serverInfo(discord_id: int) -> db_types.chapter:

    async with aiosqlite.connect(database_file) as db:
        rows = await db.execute(
            "SELECT * FROM chapter WHERE discord_serverId=?", (discord_id,)
        )
        row = await rows.fetchone()
        server = db_types.chapter(*row)

    return server


async def get_discordServers() -> list[db_types.chapter]:

    async with aiosqlite.connect(database_file) as db:
        chapters = await db.execute("SELECT * FROM chapter")
        servers = [db_types.chapter(*chapter) async for chapter in chapters]

    return servers


async def get_chapterServers(chapter_id) -> list[db_types.chapter]:

    async with aiosqlite.connect(database_file) as db:
        chapters = await db.execute(
            "SELECT * FROM chapter WHERE mgp_chapterId=?", (chapter_id,)
        )
        servers = [db_types.chapter(*chapter) async for chapter in chapters]

    return servers


async def remove_discordServer(discord_id: int) -> None:

    async with aiosqlite.connect(database_file) as db:
        await db.execute("DELETE FROM chapter WHERE discord_serverId=?", (discord_id,))
        await db.commit()


async def add_chapterRaces(races: list[tuple]) -> None:

    async with aiosqlite.connect(database_file) as db:
        await db.executemany(
            "INSERT INTO race (mgp_raceId, mgp_chapterId, discord_eventId) VALUES (?, ?, ?)",
            races,
        )
        await db.commit()


async def get_chapterRaces(chapter_id: str) -> list[str]:

    async with aiosqlite.connect(database_file) as db:
        race_data = await db.execute(
            "SELECT * FROM race WHERE mgp_chapterId=?", (chapter_id,)
        )
        races = [race[0] async for race in race_data]

    return races


async def get_Races() -> list[db_types.race]:

    async with aiosqlite.connect(database_file) as db:
        race_data = await db.execute("SELECT * FROM race")
        races = [db_types.race(*race) async for race in race_data]

    return races


async def remove_Race(race_id: str) -> None:

    async with aiosqlite.connect(database_file) as db:
        await db.execute("DELETE FROM race WHERE mgp_raceId=?", (race_id,))
        await db.commit()


async def remove_Races(race_ids: list[str]) -> None:

    async with aiosqlite.connect(database_file) as db:
        await asyncio.gather(
            *[
                db.execute("DELETE FROM race WHERE mgp_raceId=?", (race_id,))
                for race_id in race_ids
            ]
        )
        await db.commit()


async def remove_chapterRaces(chapter_id: str) -> None:

    async with aiosqlite.connect(database_file) as db:
        await db.execute("DELETE FROM race WHERE mgp_chapterId=?", (chapter_id,))
        await db.commit()
