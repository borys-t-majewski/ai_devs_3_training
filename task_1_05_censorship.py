import os
import json
import asyncio
import requests
from openai import OpenAI

from api_tasks.basic_poligon_u import load_from_json, download_data, get_desired_format, post_request
from api_tasks.get_html_fragment import get_strings_re
from api_tasks.basic_open_ai_calls import gather_calls

## IMPROVEMENT AREAS
# Send one open ai call to save on input tokens
# Change config to env variable
# Try local model
    # Local model works good with this prompt! LLAMA 8B
# Try langfuse?

# On low temp, prompt misgenders some people causing failure, but good otherwise
def execute_task_1_5(session, client, ai_devs_key:str ,task_name:str = '', data_source_url:str= '', endpoint_url:str='') -> None:

    data_source = data_source_url.replace('KLUCZ',ai_devs_key)
    
    obtained_file = download_data(data_source).decode('utf-8')
    
    ai_instructions = [
        { 'user': obtained_file
        ,'system': '''
        You will receive text in Polish. Replace all personal information with the word "CENZURA" according to these rules:

        1. Replace the following with CENZURA:
        - Full addresses
        - City/town names
        - Street names (with or without numbers)
        - Names and surnames (together or separately)
        - Ages

        2. Key formatting rules:
        - Never output multiple "CENZURA" words consecutively
        - Maintain all original formatting and non-personal information
        - Do not conjugate the word "CENZURA"

        3. Examples:
        - "25 years old" → "CENZURA years old"
        - "ulica Krakowska 14" → "ulica CENZURA"
        - "ul. Kujawska 3/5" → "ul. CENZURA"
        - "Jan Kowalski z Warszawy" → "CENZURA z CENZURA"
        - "Jan mieszka w Warszawie" → "CENZURA mieszka w CENZURA"

        Return only the censored text with no additional commentary.
        '''
        ,'assistant': ''
        }
        ]
    
        # - address, including city, street name and number. 
    #  In case you're censoring several values in row, create one word CENZURA.
    ai_answer = asyncio.run(gather_calls(ai_instructions,client = client))[0]
    print(f'''
          Source file: {obtained_file}
          Censored file: {ai_answer}
          ''')
    
    json_apt_format = {
        "task": task_name,
        "apikey": ai_devs_key,
        "answer": ai_answer
    }
    
    webhook_answer = post_request(endpoint_url, json.dumps(json_apt_format))
    if str(webhook_answer) == '<Response [200]>':
        print(get_strings_re(webhook_answer.content.decode(),pattern=r'{{FLG:(.*?)}}'))
    else:
        print(webhook_answer) 

    return None

if __name__ == "__main__":
    local_model = True 

    json_secrets = load_from_json(filepath=rf'{os.path.dirname(__file__)}\config.json')

    open_ai_api_key = json_secrets["open_ai_api_key"]
    ai_devs_key = json_secrets["api_key"]
    task_1_5_data_source = json_secrets["task_1_5_data_source"]
    task_1_5_endpoint_url = json_secrets["task_1_5_endpoint_url"]

    session = requests.Session()

    if local_model:
        client = OpenAI(base_url="http://127.0.0.1:1234/v1/",api_key='local')
    else:
        client = OpenAI(api_key=open_ai_api_key)

    execute_task_1_5(session, client, ai_devs_key, task_name = "CENZURA", data_source_url= task_1_5_data_source, endpoint_url = task_1_5_endpoint_url)

