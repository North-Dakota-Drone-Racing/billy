import sqlite3
import logging
import multigpAPI
import db_types

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

    def set_serverConfiguration(self, discord_serverId:int, discord_channelId:int, mgp_apikey:str) -> dict:
        chapter_info = multigpAPI.pull_chapter(mgp_apikey)
        if chapter_info and chapter_info['status']:
            self.logger.debug(f"Pulled chapter info for {chapter_info['chapterName']}")
            mgp_chapterId = chapter_info['chapterId']
        else:
            return False

        connection = sqlite3.connect(self.database_file)
        cursor = connection.cursor()
        
        count = cursor.execute("SELECT COUNT(*) FROM chapter WHERE discord_serverId=?", (discord_serverId,))
        if count.fetchone()[0] > 0:
            cursor.execute(f"UPDATE chapter SET discord_channelId=?, mgp_apikey=?, mgp_chapterId=? WHERE discord_serverId=?", 
                           (discord_channelId, mgp_apikey, mgp_chapterId, discord_serverId))
            connection.commit()
        else:
            cursor.execute("INSERT INTO chapter (discord_serverId, discord_channelId, mgp_chapterId, mgp_apikey) VALUES(?, ?, ?, ?)", 
                           (discord_serverId, discord_channelId, mgp_chapterId, mgp_apikey))
            connection.commit()

        cursor.close()
        connection.close()

        return chapter_info
    
    def get_chapterInfo(self, discord_id:int) -> db_types.chapter:
        connection = sqlite3.connect(self.database_file)
        cursor = connection.cursor()

        servers = cursor.execute("SELECT * FROM chapter WHERE discord_serverId=?", (discord_id,))
        server = db_types.chapter(*servers.fetchone())

        cursor.close()
        connection.close()

        return server
    
    def get_discordServers(self) -> list[db_types.chapter]:
        connection = sqlite3.connect(self.database_file)
        cursor = connection.cursor()

        chapters = cursor.execute("SELECT * FROM chapter")
        servers = []
        for chapter in chapters:
            servers.append(db_types.chapter(*chapter))

        cursor.close()
        connection.close()

        return servers
    
    def add_chapterRaces(self, races:list[tuple]) -> None:
        connection = sqlite3.connect(self.database_file)
        cursor = connection.cursor()

        cursor.executemany("INSERT INTO race (mgp_raceId, mgp_chapterId, discord_eventId) VALUES (?, ?, ?)", races)
        connection.commit()

        cursor.close()
        connection.close()
    
    def get_chapterRaces(self, chapter_id:str) -> list[int]:

        connection = sqlite3.connect(self.database_file)
        cursor = connection.cursor()

        race_data = cursor.execute("SELECT * FROM race WHERE mgp_chapterId=?", (chapter_id,))
        races = []
        for race in race_data:
            races.append(race[0])

        cursor.close()
        connection.close()
        
        return races
    
    def get_Races(self) -> list[db_types.race]:

        connection = sqlite3.connect(self.database_file)
        cursor = connection.cursor()

        race_data = cursor.execute("SELECT * FROM race")
        races = []
        for race in race_data:
            races.append(db_types.race(*race))

        cursor.close()
        connection.close()
        
        return races
