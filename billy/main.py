import os
import logging
import db_types
import db_manager
import multigpAPI
import discord
import discord.ext
import discord.ext.tasks
import datetime
import timezonefinder
import pytz
import httpx
import json

debug = bool(os.getenv('DEBUG'))
if debug:
    level = logging.DEBUG
else:
    level = logging.INFO

logger = logging.getLogger(__name__)
FORMAT = '%(asctime)s %(levelname)s %(message)s'
timestamp = int(datetime.datetime.now().astimezone().timestamp())
logging.basicConfig(filename=f'/billy/files/{timestamp}.log', encoding='utf-8', level=level, format=FORMAT, datefmt='%Y-%m-%d %H:%M:%S')

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)
tf = timezonefinder.TimezoneFinder()

ollama_server = os.getenv('OLLAMA_SERVER')
ollama_port = os.getenv('OLLAMA_PORT')
ollama_model = os.getenv('OLLAMA_MODEL')

#
# Commands
#

@tree.command(
    name="activate",
    description="Set the MultiGP API key and announcement channel for the server"
)
async def activateBot(interaction: discord.Interaction, channel:discord.app_commands.AppCommandChannel, apikey:str):
    chapter_info = DBMangager.set_serverConfiguration(interaction.guild.id, channel.id, apikey)
    if chapter_info:
        await interaction.response.send_message(f"API key recongized. {chapter_info['chapterName']} has been set as the server's chapter and <#{channel.id}> will be used for announcements.")
        logger.info(f"Data for {chapter_info['chapterName']} has been updated")
    else:
        await interaction.response.send_message("API Key not recongized.")
        logger.warning(f"Failed to update server info: Bad chapter API key")

#
# Events
#

@client.event
async def on_ready():
    await tree.sync(guild=None)
    logger.info(f'Logged in as {client.user}')
    
    # Start Tasks
    addEvents.start()
    updateEventsStatus.start()

#
# Tasks
#

# Replace this with a webhook if possible
@discord.ext.tasks.loop(hours=1)
async def addEvents():
    servers = DBMangager.get_discordServers()
    for server in servers:

        db_races = await DBMangager.get_chapterRaces(server.mgp_chapterId)
        mgp_races = await multigpAPI.pull_races(server.mgp_chapterId, server.mgp_apikey)

        new_races = []
        async for id, name in mgp_races.items():
            if id not in db_races:
                race_data = await multigpAPI.pull_race_data(id, server.mgp_apikey)
                local_tz = tf.timezone_at(lat=float(race_data['latitude']), lng=float(race_data['longitude']))
                race_starttime = datetime.datetime.strptime(race_data['startDate'], '%Y-%m-%d %I:%M %p')
                starttime_obj = pytz.timezone(local_tz).localize(race_starttime)

                if race_data['endDate']:
                    race_endtime = datetime.datetime.strptime(race_data['endDate'], '%Y-%m-%d %I:%M %p')
                    endtime_obj = pytz.timezone(local_tz).localize(race_endtime)
                    if starttime_obj >= endtime_obj:
                        endtime_obj = starttime_obj + datetime.timedelta(hours=3)
                else:
                    endtime_obj = starttime_obj + datetime.timedelta(hours=3)

                current_date = datetime.datetime.now(tz=pytz.timezone(local_tz))
                start_range = datetime.time(hour=8, tzinfo=current_date.tzinfo)
                end_range = datetime.time(hour=20, tzinfo=current_date.tzinfo)

                if current_date.timetz() < start_range or end_range < current_date.timetz():
                    continue

                if datetime.datetime.now().astimezone().timestamp() < starttime_obj.timestamp():

                    event_desciption = f"[Sign Up on MultiGP](https://www.multigp.com/races/view/?race={id})\n\n{race_data['description']}"

                    guild = client.get_guild(server.discord_serverId)
                    event = await guild.create_scheduled_event(
                        name=name,
                        description=event_desciption,
                        start_time=starttime_obj,
                        end_time=endtime_obj,
                        privacy_level=discord.PrivacyLevel.guild_only,
                        entity_type=discord.EntityType.external,
                        location=race_data['courseName']
                    )
                    logger.info("Scheduled new event")

                    if all([ollama_server, ollama_port, ollama_model]):

                        channel = client.get_channel(server.discord_channelId)

                        prompt = f"""Announce an upcoming drone racing event called {name} to the members of drone racing group named {race_data['chapterName']}. 
                        It will occur on {race_starttime.day}/{race_starttime.month} (formated as day/month). Do not mention prizes"""
                        
                        recieved_message = await ollama_message(prompt)

                        await channel.send(
                            content=f'@everyone {recieved_message}\n{event.url}'
                        )

                        logger.info("Announced new event")

                    new_races.append((id, server.mgp_chapterId, event.id))
                else:
                    new_races.append((id, server.mgp_chapterId, None))

        DBMangager.add_chapterRaces(new_races)

@discord.ext.tasks.loop(minutes=15)
async def updateEventsStatus():
    servers = DBMangager.get_discordServers()
    races:list[db_types.race] = DBMangager.get_Races()
    for race in races:
        if race.discord_eventId is None:
            continue

        for server in servers:
            if server.mgp_chapterId == race.mgp_chapterId:

                guild = client.get_guild(server.discord_serverId)
                event = guild.get_scheduled_event(race.discord_eventId)
                now = datetime.datetime.now().astimezone()

                if event is not None:
                    if event.status == discord.EventStatus.scheduled and now > event.start_time:
                        await event.start()
                    if event.status == discord.EventStatus.active and now > event.end_time:
                        await event.end()

if all([ollama_server, ollama_port, ollama_model]):
    @client.event
    async def on_message(message):
        if client.user.id == message.author.id:
            return
        
        if str(client.user.id) not in message.content:
            return
        
        message.content.replace(f"<@{client.user.id}>", "Billy")

        recieved_message = await ollama_message(message.content)
        if recieved_message:
            await message.reply(recieved_message)

#
# Run
#

async def ollama_message(send_message):

    message_out = {
            "model": ollama_model,
            "prompt": send_message,
            "stream": False
        }
    
    url = f"http://{ollama_server}:{ollama_port}/api/generate"

    try:
        response = await multigpAPI.client.post(url, data=json.dumps(message_out))
    except httpx.ConnectError:
        logger.warning("Connection to Ollama server failed")
        return None
    except httpx.ReadTimeout:
        logger.warning("Did not recieve a response from Ollama server")
        return None
    
    data = json.loads(response.text)

    return data["response"]

if __name__ == "__main__":
    BOT_TOKEN = os.getenv('TOKEN')
    DBMangager = db_manager.DBMangager(logger)
    client.run(BOT_TOKEN)