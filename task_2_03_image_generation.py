import os
import json
import asyncio
import requests
from openai import OpenAI
from anthropic import Anthropic

from api_tasks.basic_poligon_u import load_from_json, download_data, post_request
from api_tasks.get_html_fragment import get_strings_re
from api_tasks.image_generation import generate_image



def execute_task_2_3(session, client, ai_devs_key:str ,task_name:str = '', data_source_url:str= '', endpoint_url:str='', preceding_prompt = '') -> None:

    data_source = data_source_url.replace('KLUCZ-API',ai_devs_key)

    obtained_info = json.loads(download_data(data_source).decode('utf-8'))

    print(obtained_info["description"])
    image_from_ai_url = generate_image(client, obtained_info["description"],preceding_prompt=preceding_prompt)
    print(image_from_ai_url)

    json_apt_format = {
        "task": task_name,
        "apikey": ai_devs_key,
        "answer": image_from_ai_url
    }
    
    webhook_answer = post_request(endpoint_url, json.dumps(json_apt_format))
    if str(webhook_answer) == '<Response [200]>':
        print(get_strings_re(webhook_answer.content.decode(),pattern=r'{{FLG:(.*?)}}'))
    else:
        print(webhook_answer) 

    return None


if __name__ == "__main__":

    local_model = False 
    

    json_secrets = load_from_json(filepath=rf'{os.path.dirname(__file__)}\config.json')
    open_ai_api_key = json_secrets["open_ai_api_key"]
    anthropic_api_key = json_secrets["anthropic_api_key"]
    ai_devs_key = json_secrets["api_key"]
    data_source_url = json_secrets["task_2_3_data_source"]
    endpoint_url = json_secrets["task_2_3_endpoint_url"]

    model="gpt" # won't be passed beyond selecting openai client
    session = requests.Session()
    if 'claude' in model:
        client = Anthropic(api_key=anthropic_api_key)
    if 'gpt' in model:
        client = OpenAI(api_key=open_ai_api_key)
    if model == '_local_model_':
        client = OpenAI(base_url="http://127.0.0.1:1234/v1/",api_key='local')


    # preceding_prompt = 'You will receive description in polish, follow it and generate a picture in cool black and white high contrast style.'
    # preceding_prompt = 'You will receive description in polish, follow it and generate a picture in flashy anime style.'
    preceding_prompt = 'You will receive description in polish, follow it and generate a picture in oldschool style, stylized like a draft.'

    execute_task_2_3(session, client, ai_devs_key, 'robotid', data_source_url=data_source_url, endpoint_url=endpoint_url, preceding_prompt=preceding_prompt)
    