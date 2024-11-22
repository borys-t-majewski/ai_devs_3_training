from openai import OpenAI
from anthropic import Anthropic
import json 
import os

from icecream import ic 

import asyncio
import requests



# from api_tasks.basic_open_ai_calls import gather_calls
# from api_tasks.whisper_interactions import create_transcripts_from_audio
# from utilities.read_save_text_functions import get_source_data_from_zip
# from utilities.generic_utils import for_every_file_in_gen
# from utilities.html_splitter import parse_html_elements
# from api_tasks.image_encoding_utilities import image_to_bytes
# from api_tasks.website_interactions import download_webpage, download_and_chunk_webpage, sanitize_filename
# from api_tasks.url_resolver import resolve_urls, normalize_download_links
# from PIL import Image
# from pyquery import PyQuery

from api_tasks.website_ai_translation import get_website_and_describe_with_ai
from api_tasks.basic_poligon_u import load_from_json, download_data, get_desired_format, post_request, load_from_json
from api_tasks.basic_open_ai_calls import gather_calls
from api_tasks.get_html_fragment import get_strings_re

## IMPROVEMENT AREAS 



def execute_task_2_5(session, client, ai_devs_key:str , model:str = '',task_name:str = '', data_source_url:str= '', endpoint_url:str='', local_folder:str = '', questions:str = '', by_document_approach:bool = False) -> None:
    

    output_list = get_website_and_describe_with_ai(client,  model = model, data_source_url = data_source_url, local_folder = local_folder)
    # Understand context length:
    for document in output_list:
        ic(len(document))
        ic(document)
    questions = download_data(questions).decode()
    list_of_questions = [x.split('=')[1] for x in questions.split('\n') if len(x) > 0]
    list_of_q_keys = ['0' + str(x) for x in range(1,len(list_of_questions)+1)]
    dict_of_questions = dict(zip(list_of_q_keys, list_of_questions))
    ic(dict_of_questions)

    
    system_general_instr = f'''Answer briefly in one sentence, using knowledge base given below:'''
    system_general_instr = f'''Answer going through your though process and reach final conclusion, using knowledge base given below:'''

    system_query_instr = f'''
    Remember to use contained context clues to answer questions even if they're not correctly in body of text.
    Example: 
    if "Plac Mariacki" is mentioned
    place might be Kraków

    if "Pałac Kultury" is mentioned
    place might be Warszawa


    '''
    if by_document_approach:
        for question in dict_of_questions.keys():
            ic(f'Considering question: {dict_of_questions[question]}')
            for document in output_list:
                ic(f'Document of length {len(document)}')

                query = [{
                'user':f'{dict_of_questions[question]}','assistant':'','system':f'''
                {system_general_instr} <KNOWLEDGE> {document} </KNOWLEDGE>. {system_query_instr}
                It's possible there is no information in dataset, in this case, answer only one word: NOIDEA 
                '''
                }]
                answer = asyncio.run(gather_calls(query,client = client, tempature=.3, model = model))
                if answer[0] != 'NOIDEA':
                    dict_of_questions[question] = answer[0]
                    break
        ic(dict_of_questions)
    else:
        kp = '----\n'.join(output_list)
        for question in dict_of_questions.keys():
            ic(f'Considering question: {dict_of_questions[question]}')
            query = [{
            'user':f'{dict_of_questions[question]}','assistant':'','system':f'''
            {system_general_instr} <KNOWLEDGE> {kp} </KNOWLEDGE>.{system_query_instr}
            '''
            }]
            answer = asyncio.run(gather_calls(query,client = client, tempature=.3, model = model))
            dict_of_questions[question] = answer[0]

        ic(dict_of_questions)            

    # then add all of them to rag? without rag we'll have to actually have some kind of loop by questions, to see if it's answered - make model say if there's no info
    # for each page:
        # for each question:
    # would be nicer if it was a rag though




    json_apt_format = {
        "task": task_name,
        "apikey": ai_devs_key,
        "answer": dict_of_questions
    }
    ic(json.dumps(json_apt_format))

    webhook_answer = post_request(endpoint_url, json.dumps(json_apt_format))
    if str(webhook_answer) == '<Response [200]>':
        print(get_strings_re(webhook_answer.content.decode(),pattern=r'{{FLG:(.*?)}}'))
    else:
        ic(webhook_answer)

        ic(webhook_answer.content)

if __name__ == "__main__":
    local_model = False 
    # (only argument for completion, not for whisper call)

    local_folder = r'''C:\Projects\AI_DEVS_3\s_2_05_website'''
    json_secrets = load_from_json(filepath=rf'{os.path.dirname(__file__)}\config.json')

    open_ai_api_key = json_secrets["open_ai_api_key"]
    anthropic_api_key = json_secrets["anthropic_api_key"]
    ai_devs_key = json_secrets["api_key"]
    data_source = json_secrets["task_2_5_data_source"]
    questions = json_secrets["task_2_5_questions"].replace('KLUCZ-API',ai_devs_key)
    endpoint_url = json_secrets["task_2_5_endpoint_url"]
    
    model = "gpt-4o-mini"
    # model = "gpt-4o"
    task_name = 'arxiv'
    session = requests.Session()
    
    if 'claude' in model:
        client = Anthropic(api_key=anthropic_api_key)
    if 'gpt' in model:
        client = OpenAI(api_key=open_ai_api_key)
    if model == '_local_model_':
        client = OpenAI(base_url="http://127.0.0.1:1234/v1/",api_key='local')

    execute_task_2_5(session, client, model = model, ai_devs_key = ai_devs_key ,task_name = task_name, data_source_url = data_source, endpoint_url = endpoint_url, local_folder = local_folder, questions = questions, by_document_approach = True)



    