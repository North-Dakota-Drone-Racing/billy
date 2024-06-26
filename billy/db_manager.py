import logging
import multigpAPI
import db_types
import aiosqlite

class DBMangager():

    database_file = "/billy/files/database.db"

    def __init__(self, logger) -> None:
        self.logger:logging.Logger = logger
        self.estabilsh_db()
        
    def estabilsh_db(self) -> None:
        connection = aiosqlite.connect(self.database_file)
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

        connection = await aiosqlite.connect(self.database_file)
        cursor = await connection.cursor()
        
        count = await cursor.execute("SELECT COUNT(*) FROM chapter WHERE discord_serverId=?", (discord_serverId,))
        if count.fetchone()[0] > 0:
            await cursor.execute(f"UPDATE chapter SET discord_channelId=?, mgp_apikey=?, mgp_chapterId=? WHERE discord_serverId=?", 
                           (discord_channelId, mgp_apikey, mgp_chapterId, discord_serverId))
            await connection.commit()
        else:
            await cursor.execute("INSERT INTO chapter (discord_serverId, discord_channelId, mgp_chapterId, mgp_apikey) VALUES(?, ?, ?, ?)", 
                           (discord_serverId, discord_channelId, mgp_chapterId, mgp_apikey))
            await connection.commit()

        await cursor.close()
        await connection.close()

        return chapter_info
    
    async def get_chapterInfo(self, discord_id:int) -> db_types.chapter:
        connection = await aiosqlite.connect(self.database_file)
        cursor = await connection.cursor()

        servers = await cursor.execute("SELECT * FROM chapter WHERE discord_serverId=?", (discord_id,))
        server = db_types.chapter(*servers.fetchone())

        await cursor.close()
        await connection.close()

        return server
    
    async def get_discordServers(self) -> list[db_types.chapter]:
        connection = await aiosqlite.connect(self.database_file)
        cursor = await connection.cursor()

        chapters = await cursor.execute("SELECT * FROM chapter")
        servers = []
        async for chapter in chapters:
            servers.append(db_types.chapter(*chapter))

        await cursor.close()
        await connection.close()

        return servers
    
    async def add_chapterRaces(self, races:list[tuple]) -> None:
        connection = await aiosqlite.connect(self.database_file)
        cursor = await connection.cursor()

        await cursor.executemany("INSERT INTO race (mgp_raceId, mgp_chapterId, discord_eventId) VALUES (?, ?, ?)", races)
        await connection.commit()

        await cursor.close()
        await connection.close()
    
    async def get_chapterRaces(self, chapter_id:str) -> list[int]:

        connection = await aiosqlite.connect(self.database_file)
        cursor = await connection.cursor()

        race_data = await cursor.execute("SELECT * FROM race WHERE mgp_chapterId=?", (chapter_id,))
        races = []
        async for race in race_data:
            races.append(race[0])

        await cursor.close()
        await connection.close()
        
        return races
    
    async def get_Races(self) -> list[db_types.race]:

        connection = await aiosqlite.connect(self.database_file)
        cursor = await connection.cursor()

        race_data = await cursor.execute("SELECT * FROM race")
        races = []
        async for race in race_data:
            races.append(db_types.race(*race))

        await cursor.close()
        await connection.close()
        
        return races
