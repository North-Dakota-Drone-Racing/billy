"""
Database object definition
"""

from sqlalchemy import ForeignKey
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# pylint: disable=R0903


class _ObjectBase(AsyncAttrs, DeclarativeBase):
    """
    Base classifier for database objects
    """

    id: Mapped[int] = mapped_column(primary_key=True)
    """Internal identifier"""


class DiscordServer(_ObjectBase):
    """
    Class representing a MultiGP Chapter
    """

    __tablename__ = "server"

    server_id: Mapped[int] = mapped_column()
    """The internal discord id of the server"""
    channel_id: Mapped[int] = mapped_column()
    """The channel of the server to announce messages in"""
    chapter_id: Mapped[str] = mapped_column()
    """The id of the chapter in the MultiGP database to bind to"""
    api_key: Mapped[str] = mapped_column()
    """The api key for the MultiGP chapter"""

    def __init__(self, server_id, channel_id, chapter_id, api_key) -> None:
        self.server_id = server_id
        self.channel_id = channel_id
        self.chapter_id = chapter_id
        self.api_key = api_key


class MGPEvent(_ObjectBase):
    """
    Class representing a MultiGP Event
    """

    # pylint: disable=E1136

    __tablename__ = "event"

    event_id: Mapped[str] = mapped_column()
    """The id of the event in the MultiGP database"""
    chapter_id: Mapped[str] = mapped_column(ForeignKey("server.id"))
    """The id of the event in the MultiGP database"""
    discord_event_id: Mapped[int] = mapped_column(nullable=True)
    """The discord event id"""
    servers: Mapped[list[DiscordServer]] = relationship()

    def __init__(self, event_id, chapter_id, discord_event_id) -> None:
        self.event_id = event_id
        self.chapter_id = chapter_id
        self.discord_event_id = discord_event_id
