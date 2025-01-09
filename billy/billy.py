"""
Program primary execution 
"""

import os
import logging
import datetime
import asyncio
from collections.abc import AsyncGenerator

import discord
import discord.ext
import discord.ext.tasks
import timezonefinder
import pytz

from .database import DatabaseManager, DiscordServer
from .api import OllamaAPI, MultiGPAPI

logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)
tf = timezonefinder.TimezoneFinder()

_filepath = os.getenv("DB_PATH", "/billy/files/database.db")
db = DatabaseManager(filename=_filepath)

multigp = MultiGPAPI()
ollama = OllamaAPI()


@tree.command(
    name="activate",
    description="Set the bot configurations for the server",
)
async def set_bot_configuration(
    interaction: discord.Interaction,
    channel: discord.app_commands.AppCommandChannel,
    apikey: str,
) -> None:
    """
    Sets the configurations for the server
    """
    if interaction.guild is not None:
        chapter_info = await db.set_server_configuration(
            interaction.guild.id, channel.id, apikey
        )
        if chapter_info:
            await interaction.response.send_message(
                (
                    f"API key recongized. {chapter_info['chapterName']} has been set as the "
                    f"server's chapter and <#{channel.id}> will be used for announcements."
                )
            )
            logger.info("Data for %s has been updated", chapter_info["chapterName"])
        else:
            await interaction.response.send_message("API Key not recongized.")
            logger.warning("Failed to update server info: Bad chapter API key")


@client.event
async def on_ready() -> None:
    """
    Event called when server is ready
    """
    await tree.sync(guild=None)
    logger.info("Logged in as %s", client.user)

    events_sync.start()
    update_event_status.start()


def format_message(message: discord.Message) -> dict[str, str]:
    """
    Formats a discord message for the Ollama chat api

    :param message: Message to format
    :return: Formated message
    """

    if client.user is None:
        return {}

    message_ = {
        "role": "assistant" if message.author.id == client.user.id else "user",
        "content": message.content.replace(f"<@{client.user.id}>", "Billy"),
    }

    return message_


async def generate_message_collection(message: discord.Message) -> list[dict[str, str]]:
    """
    Get a collection of message history

    :param message: The latest message
    :return: The returned collection
    """

    collection: list[dict] = []

    collection.insert(0, format_message(message))

    if message.reference is not None:

        next_id = message.reference.message_id
        while next_id:
            message = await message.channel.fetch_message(next_id)
            collection.insert(0, format_message(message))

            if message.reference is None:
                next_id = None
            else:
                next_id = message.reference.message_id

    return collection


async def generate_response_fail_checks(
    message: discord.Message,
) -> AsyncGenerator[bool, None]:

    if client.user is not None:

        yield not ollama.active
        yield client.user.id == message.author.id

        invoked = str(client.user.id) in message.content

        if message.reference is not None and message.reference.message_id is not None:
            message_ = await message.channel.fetch_message(message.reference.message_id)
            replied = message_.author.id == client.user.id
        else:
            replied = False

        yield not (invoked or replied)

    else:
        yield True


@client.event
async def on_message(message: discord.Message) -> None:
    """
    Process recieved messages

    :param message: The recieved message
    """

    async for check in generate_response_fail_checks(message):
        if check:
            return

    logger.info("Message recieved")
    logger.debug(message.content)

    messages = await generate_message_collection(message)
    recieved_message = await ollama.generate_chat_response(messages)

    if recieved_message is not None:
        await message.reply(recieved_message)
        logger.info("Message reply sent")


@client.event
async def on_guild_remove(guild: discord.Guild) -> None:
    """
    Remove server from database when bot removed from
    server

    :param guild: The server
    """

    await db.remove_discord_server(guild.id)

    server = await db.get_server_info(guild.id)
    if server is not None:
        servers = await db.get_server_count_by_chapter(server.chapter_id)

        if servers == 0:
            await db.remove_event_by_chapter_id(server.chapter_id)


async def add_race_checks(
    server: DiscordServer, race_id: str, race_name: str, api_key: str
) -> tuple[bool, discord.ScheduledEvent | None]:
    """
    Checks for adding race to database

    :param server: Discord server associated with the checks
    :param race_id: The id of the race
    :param race_name: The race name
    :param api_key: The chapter api key
    :return: The status and generated event (if created)
    """

    race_data = await multigp.pull_race_data(race_id, api_key)
    if race_data is None:
        return False, None

    local_tz = tf.timezone_at(
        lat=float(race_data["latitude"]), lng=float(race_data["longitude"])
    )
    if local_tz is None:
        return False, None

    race_starttime = datetime.datetime.strptime(
        race_data["startDate"], "%Y-%m-%d %I:%M %p"
    )
    starttime_obj = pytz.timezone(local_tz).localize(race_starttime)

    if race_data["endDate"]:
        race_endtime = datetime.datetime.strptime(
            race_data["endDate"], "%Y-%m-%d %I:%M %p"
        )
        endtime_obj = pytz.timezone(local_tz).localize(race_endtime)
        if starttime_obj >= endtime_obj:
            endtime_obj = starttime_obj + datetime.timedelta(hours=3)
    else:
        endtime_obj = starttime_obj + datetime.timedelta(hours=3)

    current_date = datetime.datetime.now(tz=pytz.timezone(local_tz))
    start_range = datetime.time(hour=8, tzinfo=current_date.tzinfo)
    end_range = datetime.time(hour=20, tzinfo=current_date.tzinfo)

    if datetime.datetime.now().astimezone().timestamp() > starttime_obj.timestamp():
        return True, None

    if current_date.timetz() < start_range or end_range < current_date.timetz():
        return False, None

    event_desciption = (
        "[Sign Up on MultiGP]"
        f"(https://www.multigp.com/races/view/?race={race_id})"
        f"\n\n{race_data['description']}"
    )

    guild = client.get_guild(server.server_id)
    if guild is None:
        return True, None

    event = await guild.create_scheduled_event(
        name=race_name,
        description=event_desciption,
        start_time=starttime_obj,
        end_time=endtime_obj,
        privacy_level=discord.PrivacyLevel.guild_only,
        entity_type=discord.EntityType.external,
        location=race_data["courseName"],
    )
    logger.info("Scheduled new event")

    if ollama.active:
        loop = asyncio.get_running_loop()
        loop.create_task(
            generate_and_send(server, race_data, race_name, race_starttime, event)
        )

    return True, event


async def generate_and_send(
    server: DiscordServer,
    race_data: dict,
    race_name: str,
    race_starttime: datetime.datetime,
    event: discord.ScheduledEvent,
) -> None:
    """
    Sends an announcement message to the server

    :param server: The server to announce to
    :param race_data: The event data
    :param race_name: The event name
    :param race_starttime: The race datetime object
    :param event: The discord event
    """
    channel = client.get_channel(server.channel_id)
    if not isinstance(channel, discord.TextChannel):
        return

    prompt = (
        "Cleverly announce an upcoming drone racing event "
        f"called {race_name} to the members of drone racing group "
        f"named {race_data['chapterName']}. It will occur on "
        f"{race_starttime.year}-{race_starttime.month}-{race_starttime.day}."
    )

    recieved_message = await ollama.generate_single_response(prompt)
    if recieved_message:
        await channel.send(content=f"@everyone {recieved_message}\n{event.url}")
        logger.info("Announced new event")
        logger.debug(recieved_message)


@discord.ext.tasks.loop(hours=3)
async def events_sync() -> None:
    """
    Pulls data from MultiGP to sync with the local database

    This task should be replaced with a webhook if possible
    """
    async for server in db.get_servers():

        db_races = await db.get_chapter_race_ids(server.chapter_id)
        mgp_races = await multigp.pull_races(server.chapter_id, server.api_key)

        if mgp_races is None:
            continue

        new_races: list[tuple[str, str, int | None]] = []
        for race in mgp_races:
            if race["id"] not in db_races:

                add_status, event = await add_race_checks(
                    server, race["id"], race["name"], server.api_key
                )
                if add_status is False:
                    continue
                if event is None:
                    new_races.append((race["id"], server.chapter_id, None))
                else:
                    new_races.append((race["id"], server.chapter_id, event.id))

        await db.add_chapter_races(new_races)

        old_races: list[str] = []
        mgp_races_: set[str] = {race["id"] for race in mgp_races}
        for race_ in db_races:
            if race_ not in mgp_races_:
                old_races.append(race_)
        await db.remove_events_by_event_id(old_races)


@discord.ext.tasks.loop(minutes=15)
async def update_event_status() -> None:
    """
    Periodically
    """
    async for race in db.get_races():
        if race.event_id is None:
            continue

        servers: list[DiscordServer] | None = await race.awaitable_attrs.servers

        if servers is None:
            continue

        for server in servers:

            if (guild := client.get_guild(server.server_id)) is None:
                continue

            event = guild.get_scheduled_event(race.discord_event_id)
            now = datetime.datetime.now().astimezone()

            if event is not None:
                if (
                    event.status == discord.EventStatus.scheduled
                    and now > event.start_time
                ):
                    await event.start()
                if (
                    event.status == discord.EventStatus.active
                    and event.end_time is not None
                    and now > event.end_time
                ):
                    await event.end()


async def start() -> None:
    """
    Start the discord bot
    """
    token = os.getenv("TOKEN")
    await db.setup()
    if token is not None:
        logger.info("Starting Billy")
        await client.start(token)
    else:
        logger.warning("Discord bot token not found")
