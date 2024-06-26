import logging
import multigpAPI
import db_types
import aiosqlite
import sqlite3
import asyncio

class DBMangager():

    database_file = "/billy/files/database.db"

    def __init__(self, logger) -> None:
        self.logger:logging.Logger = logger
        self.estabilsh_db()
        
    def estabilsh_db(self) -> None:
        connection = sqlite3.connect(self.database_file)
        cursor = connection.cursor()

        cursor.execute("CREATE TABLE IF NOT EXISTS chapter(discord_serverId INTEGER, discord_channelId INTEGER, mgp_chapterId TEXT, mgp_apikey TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS race(mgp_raceId TEXT, mgp_chapterId TEXT, discord_eventId INTEGER)")

        cursor.close()
        connection.close()

    async def set_serverConfiguration(self, discord_serverId:int, discord_channelId:int, mgp_apikey:str) -> dict:
        chapter_info = await multigpAPI.pull_chapter(mgp_apikey)
        if chapter_info and chapter_info['status']:
            self.logger.debug(f"Pulled chapter info for {chapter_info['chapterName']}")
            mgp_chapterId = chapter_info['chapterId']
        else:
            return False

        async with aiosqlite.connect(self.database_file) as db:
        
            count = await db.execute("SELECT COUNT(*) FROM chapter WHERE discord_serverId=?", (discord_serverId,))
            if count.fetchone()[0] > 0:
                await db.execute(f"UPDATE chapter SET discord_channelId=?, mgp_apikey=?, mgp_chapterId=? WHERE discord_serverId=?", 
                            (discord_channelId, mgp_apikey, mgp_chapterId, discord_serverId))
                await db.commit()
            else:
                await db.execute("INSERT INTO chapter (discord_serverId, discord_channelId, mgp_chapterId, mgp_apikey) VALUES(?, ?, ?, ?)", 
                            (discord_serverId, discord_channelId, mgp_chapterId, mgp_apikey))
                await db.commit()

        return chapter_info
    
    async def get_chapterInfo(self, discord_id:int) -> db_types.chapter:

        async with aiosqlite.connect(self.database_file) as db:
            servers = await db.execute("SELECT * FROM chapter WHERE discord_serverId=?", (discord_id,))
            server = db_types.chapter(*servers.fetchone())

        return server
    
    async def get_discordServers(self) -> list[db_types.chapter]:

        async with aiosqlite.connect(self.database_file) as db:

            async with db.execute("SELECT * FROM chapter") as cursor:
                servers = await asyncio.gather(
                    *[db_types.chapter(*chapter) for chapter in cursor]
                )

        return servers
    
    async def add_chapterRaces(self, races:list[tuple]) -> None:

        async with aiosqlite.connect(self.database_file) as db:

            await db.executemany("INSERT INTO race (mgp_raceId, mgp_chapterId, discord_eventId) VALUES (?, ?, ?)", races)
            await db.commit()
    
    async def get_chapterRaces(self, chapter_id:str) -> list[int]:

        async with aiosqlite.connect(self.database_file) as db:

            race_data = await db.execute("SELECT * FROM race WHERE mgp_chapterId=?", (chapter_id,))
            races = await asyncio.gather(
                *[race[0] for race in race_data]
            )
        
        return races
    
    async def get_Races(self) -> list[db_types.race]:

        async with aiosqlite.connect(self.database_file) as db:

            race_data = await db.execute("SELECT * FROM race")

            races = await asyncio.gather(
                *[db_types.race(*race) for race in race_data]
            )
        
        return races
