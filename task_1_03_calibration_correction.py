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

def execute_task_1_3(session, client, ai_devs_key:str ,task_name:str = '', data_source_url:str= '', endpoint_url:str='') -> None:

    data_source = data_source_url.replace('TWOJ-KLUCZ',ai_devs_key)

    obtained_file = json.loads(download_data(data_source).decode('utf-8'))

    ai_instructions = [
        { 'user': 'question_here'
        ,'system':f'''
        Use english only in your responses. Answer briefly, with just the answer, there is no need for full sentence.
        '''
        ,'assistant': ''
        }
        ]
    
    count_matched = 0
    count_unmatched = 0
    count_with_test = 0
    
    for segment in obtained_file:
        if segment == 'test-data':
            for block in obtained_file[segment]:
                # math corrections
                calculation = get_strings_re(block['question'],pattern=r'^\d+\s*[+\-*/]\s*\d+$',match_group=0)
                expected_results = eval(calculation)
                actual_results = block['answer']

                if actual_results == expected_results:
                    count_matched+=1
                else:
                    count_unmatched+=1
                block['answer'] = expected_results

                # quiz corrections
                # possibly would be better to gather unique questions and ask in one query, to save money on input tokens

                if 'test' in block:
                    count_with_test+=1
                    ai_instructions_with_q = ai_instructions.copy()
                    ai_instructions_with_q[0]['user'] = block['test']['q']
                    ai_answer = asyncio.run(gather_calls(ai_instructions_with_q,client = client))[0]
                    block['test']['a'] = ai_answer

    print(f'Correct {count_matched}, Errors {count_unmatched}, Quizes {count_with_test}')
    obtained_file['apikey'] = ai_devs_key

    json_apt_format = {
        "task": task_name,
        "apikey": ai_devs_key,
        "answer": obtained_file
    }

    webhook_answer = post_request(endpoint_url, json.dumps(json_apt_format))
    if str(webhook_answer) == '<Response [200]>':
        print(get_strings_re(webhook_answer.content.decode(),pattern=r'{{FLG:(.*?)}}'))
    else:
        print(webhook_answer) 

if __name__ == "__main__":

    json_secrets = load_from_json(filepath=rf'{os.path.dirname(__file__)}\config.json')

    open_ai_api_key = json_secrets["open_ai_api_key"]
    ai_devs_key = json_secrets["api_key"]
    task_1_3_data_source = json_secrets["task_1_3_data_source"]
    task_1_3_endpoint_url = json_secrets["task_1_3_endpoint_url"]


    session = requests.Session()
    client = OpenAI(api_key=open_ai_api_key)
    execute_task_1_3(session, client, ai_devs_key, task_name = "JSON", data_source_url= task_1_3_data_source, endpoint_url = task_1_3_endpoint_url)

