import logging
import discord
from quart import Quart, request

logger = logging.getLogger(__name__)

app = Quart(__name__)
_client:discord.Client = None

def set_client(client:discord.Client) -> None:
    _client = client

def get_app() -> Quart:
    return app

@app.post("/race/add")
async def race_add():
    try:
        data = await request.get_json()
    except:
        return {"status": False}
    else:
        return {"input": data, "status": True}

@app.post("/race/modify")
async def race_modify():
    try:
        data = await request.get_json()
    except:
        return {"status": False}
    else:
        return {"input": data, "status": True}

@app.post("/race/delete")
async def race_delete():
    try:
        data = await request.get_json()
    except:
        return {"status": False}
    else:
        return {"input": data, "status": True}
