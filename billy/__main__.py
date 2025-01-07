"""
PropHazard server entry point
"""

import os
import sys
import logging
import datetime

from .billy import start


timestamp = int(datetime.datetime.now().astimezone().timestamp())

if bool(os.getenv("DEBUG")):
    LEVEL = logging.DEBUG
else:
    LEVEL = logging.INFO


FORMAT = "%(asctime)s %(levelname)s %(message)s"
logging.basicConfig(
    filename=f"/billy/files/{timestamp}.log",
    encoding="utf-8",
    level=LEVEL,
    format=FORMAT,
    datefmt="%Y-%m-%d %H:%M:%S",
)

# pylint: disable=E0401

if sys.platform == "linux":
    from uvloop import run
else:
    from asyncio import run


def main() -> None:
    """
    Run the discord bot
    """
    run(start())


if __name__ == "__main__":
    main()
