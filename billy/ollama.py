import logging
import httpx
import json
import os

logger = logging.getLogger(__name__)

_ollama_server = os.getenv('OLLAMA_SERVER')
_ollama_port = os.getenv('OLLAMA_PORT')
_ollama_model = os.getenv('OLLAMA_MODEL')
active = all([_ollama_server, _ollama_port, _ollama_model])

logger.debug(f"Using Ollama: {active}")

async def generate_message(send_message):

    message_out = {
            "model": _ollama_model,
            "prompt": send_message,
            "stream": False
        }
    
    url = f"http://{_ollama_server}:{_ollama_port}/api/generate"

    try:
        async with httpx.AsyncClient(limits=httpx.Limits(keepalive_expiry=20)) as client:
            response = await client.post(url, data=json.dumps(message_out), timeout=20)
    except httpx.ConnectError:
        logger.warning("Connection to Ollama server failed")
        return None
    except httpx.ReadTimeout:
        logger.warning("Did not recieve a response from Ollama server")
        return None
    
    data = json.loads(response.text)

    return data["response"]
