import logging
import json
import httpx

logger = logging.getLogger(__name__)
client = httpx.AsyncClient()

# https://www.multigp.com/apidocumentation/

async def _request_and_download(url, json_request):
    header = {'Content-type': 'application/json'}

    try:
        response = await client.post(url, headers=header, data=json_request)
    except httpx.ConnectError:
        logger.warning(f"Did not establish connection to MultiGP.")
        returned_json = {'status' : False}
        return returned_json
        
    try:
        returned_json = json.loads(response.text)
    except AttributeError:
        returned_json = {'status' : False}
    finally:
        return returned_json
    
async def pull_chapter(apiKey):
    url = 'https://www.multigp.com/mgp/multigpwebservice/chapter/findChapterFromApiKey'
    data = {
        'apiKey' : apiKey
    }
    json_request = json.dumps(data)
    returned_json = await _request_and_download(url, json_request)

    if returned_json['status']:
        return returned_json
    else:
        return None

async def pull_races(chapterId, apiKey):
    url = f'https://www.multigp.com/mgp/multigpwebservice/race/listForChapter?chapterId={chapterId}'
    data = {
        'apiKey' : apiKey
    }
    json_request = json.dumps(data)
    returned_json = await _request_and_download(url, json_request)

    if returned_json['status']:
        races = {}

        for race in returned_json['data']:
            races[race['id']] = race['name']

        return races
    else:
        return None

async def pull_race_data(race_id, apiKey):
    url = f'https://www.multigp.com/mgp/multigpwebservice/race/view?id={race_id}'
    data = {
        'apiKey' : apiKey
    }
    json_request = json.dumps(data)
    returned_json = await _request_and_download(url, json_request)

    if returned_json['status']:
        logger.info(f"Pulled data for {returned_json['data']['chapterName']}")
        return returned_json['data']
    else:
        return None