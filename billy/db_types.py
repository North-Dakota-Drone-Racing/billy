class chapter():
    def __init__(self, discord_serverId, discord_channelId, mgp_chapterId, mgp_apikey) -> None:
        self.discord_serverId   = discord_serverId
        self.discord_channelId  = discord_channelId
        self.mgp_chapterId      = mgp_chapterId
        self.mgp_apikey         = mgp_apikey

class race():
    def __init__(self, mgp_raceId, mgp_chapterId, discord_eventId) -> None:
        self.mgp_raceId         = mgp_raceId
        self.mgp_chapterId      = mgp_chapterId
        self.discord_eventId    = discord_eventId