from openai import OpenAI
import json 
import os

import asyncio
import requests

from api_tasks.basic_poligon_u import load_from_json, post_request
from api_tasks.get_html_fragment import get_strings_re
from api_tasks.basic_open_ai_calls import gather_calls
from api_tasks.whisper_interactions import create_transcripts_from_audio
from utilities.read_save_text_functions import get_source_data_from_zip

## IMPROVEMENT AREAS 
# Try local? See https://github.com/domik82/aidevs3/blob/main/tasks/S02E01/how-to-whisper.md

def ask_transcripts(client, local_folder=r'''C:\Projects\AI_DEVS_3\s_2_01_audiofiles'''):
    # client = OpenAI()
    
    # Create a directory for transcripts if it doesn't exist
    transcript_dir = os.path.join(local_folder, 'transcripts')
    
    # Go through all files in the directory

    # Interviews:
    interview_content = '''
    Find below content of several interviews, conducted in polish. Each interview will be separated from others by html tags, for example:
    <Andrzej> blablabla </Andrzej> in which "blablabla" is the entire content of interview done by Andrzej.

    '''
    for filename in os.listdir(transcript_dir):
        # Skip if it's a directory or not an audio file
        if os.path.isdir(os.path.join(transcript_dir, filename)) or not filename.endswith(('.txt')):
            continue
        filename_path = os.path.join(transcript_dir, filename)

        with open(filename_path, 'r') as file:
            text = file.read()
            interview_content = interview_content + f'<{filename.replace("transcript.txt","").title()}>' + text + f'</{filename.replace("interview.txt","").title()}> \n'
        
    return interview_content

def execute_task_2_1(client, content:str ,task_name:str = '', endpoint_url:str='') -> None:

    ai_instructions = [
        { 'user': '''
          Based on your knowledge, you have to determine university department Andrzej Maj lectures at, and respond with detailed information about department's address location, including city & street (including information that's not in content of interviews).
          Keep in mind to find information about university's department, not university's location.
          Do not return anything else about content of interviews.'''
         ,'system': f'''
        {content}
        ''','assistant': ''
        }
        ]
    general_answer = asyncio.run(gather_calls(ai_instructions,client = client))[0]
    print(f'''Intermediate answer: {general_answer}''')

    specific_ai_instructions = [
        { 'user': f'''{general_answer}'''
         ,'system': f'''
        'Extract only street name from given text, and return it. Provide no other output that street name.'
        ''','assistant': ''
        }
        ]
    specific_answer = asyncio.run(gather_calls(specific_ai_instructions,client = client))[0]
    print(f'''Final answer: {specific_answer}''')


    json_apt_format = {
        "task": task_name,
        "apikey": ai_devs_key,
        "answer": specific_answer
    }
    
    webhook_answer = post_request(endpoint_url, json.dumps(json_apt_format))
    if str(webhook_answer) == '<Response [200]>':
        print(get_strings_re(webhook_answer.content.decode(),pattern=r'{{FLG:(.*?)}}'))
    else:
        print(webhook_answer) 

    return None

if __name__ == "__main__":
    local_model = False 
    # (only argument for completion, not for whisper call)

    local_folder = r'''C:\Projects\AI_DEVS_3\s_2_01_audiofiles'''
    json_secrets = load_from_json(filepath=rf'{os.path.dirname(__file__)}\config.json')

    open_ai_api_key = json_secrets["open_ai_api_key"]
    ai_devs_key = json_secrets["api_key"]
    task_2_1_data_source = json_secrets["task_2_1_data_source"]
    task_2_1_endpoint_url = json_secrets["task_2_1_endpoint_url"]

    session = requests.Session()

    if local_model:
        client = OpenAI(base_url="http://127.0.0.1:1234/v1/",api_key='local')
    else:
        client = OpenAI(api_key=open_ai_api_key)

    get_source_data_from_zip(data_source_url=task_2_1_data_source)
    create_transcripts_from_audio(client,local_folder=local_folder)
    content_of_interviews = ask_transcripts(client,local_folder=local_folder)
    execute_task_2_1(client,content = content_of_interviews,task_name="mp3",endpoint_url=task_2_1_endpoint_url)