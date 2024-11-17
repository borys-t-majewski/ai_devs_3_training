from openai import OpenAI
from anthropic import Anthropic
import json 
import os

import asyncio
import requests

from api_tasks.basic_poligon_u import load_from_json, post_request
from api_tasks.get_html_fragment import get_strings_re
from api_tasks.basic_open_ai_calls import gather_calls
from api_tasks.whisper_interactions import create_transcripts_from_audio
from utilities.read_save_text_functions import get_source_data_from_zip
from utilities.generic_utils import for_every_file_in_gen
from api_tasks.image_encoding_utilities import image_to_bytes
from PIL import Image

## IMPROVEMENT AREAS 
def task_splitter(file_path,extension_dictionary = {'txt':'text','png':'vision','mp3':'audio'},no_expansion_dict = 'text'):
    import os
    extension = os.path.splitext(file_path)
    if len(extension[1])==0:
        return no_expansion_dict
    else:
        return extension_dictionary[extension[1].replace('.','')]
    
def execute_task_2_4(session, client, ai_devs_key:str ,task_name:str = '', data_source_url:str= '', endpoint_url:str='', directive = '') -> None:

    l_o_p = [x for x in for_every_file_in_gen(local_folder,recursive=True, supported_formats =('txt','png'), include_no_extension = False)]
    # and assuming no extension file is excluded as well

    # filter_files_we_don't care about, why did I bother adding folder search
    l_o_p = [l for l in l_o_p if r'\facts' not in l]
    
    list_of_calls = []
    for term in l_o_p:
        method = task_splitter(term)
        print(f'For file {term}, use method {method}')

        if method == 'text':
            with open(term, 'r') as file:
                content = file.read()
                list_of_calls.append({'user':content, 'system':directive})
        if method == 'vision':
            # converted = convert_local_picture(term,apply_enhancing=False)
            converted = [Image.open(term),term]

            local_format = converted[1].split('.')[-1].upper()
            list_of_calls.append({'user':[{'type':'text', 'text':'Read text on image'},{'type':'image_local','local_path':image_to_bytes(converted[0],format=local_format)}], 'system':directive})
                
        
    my_answers = asyncio.run(gather_calls(list_of_calls,client = client, tempature=.3, model = model))

    map_objects = dict(zip(l_o_p, my_answers))
    print(map_objects)

    final_answer = {}
    for key, value in map_objects.items():
        if (not value == 'neither'):
            if value not in final_answer:
                final_answer[value] = []
            final_answer[value].append(key)
        
    for key in final_answer:
        for en,l in enumerate(final_answer[key]):
            final_answer[key][en] = os.path.split(l)[1].replace('_audio_convert.txt','.mp3').replace("'",'"')
        final_answer[key].sort()
    

    json_apt_format = {
        "task": task_name,
        "apikey": ai_devs_key,
        "answer": final_answer
    }
    print(json.dumps(json_apt_format))

    webhook_answer = post_request(endpoint_url, json.dumps(json_apt_format))
    if str(webhook_answer) == '<Response [200]>':
        print(get_strings_re(webhook_answer.content.decode(),pattern=r'{{FLG:(.*?)}}'))
    else:
        print(webhook_answer)
        print(webhook_answer.content)

if __name__ == "__main__":
    local_model = False 
    # (only argument for completion, not for whisper call)

    local_folder = r'''C:\Projects\AI_DEVS_3\s_2_04_files'''
    json_secrets = load_from_json(filepath=rf'{os.path.dirname(__file__)}\config.json')

    open_ai_api_key = json_secrets["open_ai_api_key"]
    anthropic_api_key = json_secrets["anthropic_api_key"]
    ai_devs_key = json_secrets["api_key"]
    model = "gpt-4o-mini"

    task_2_4_data_source = json_secrets["task_2_4_data_source"]
    task_2_4_endpoint_url = json_secrets["task_2_4_endpoint_url"]

    session = requests.Session()
    
    if 'claude' in model:
        client = Anthropic(api_key=anthropic_api_key)
    if 'gpt' in model:
        client = OpenAI(api_key=open_ai_api_key)
    if model == '_local_model_':
        client = OpenAI(base_url="http://127.0.0.1:1234/v1/",api_key='local')


    directive = '''Based on this content, classify it in one of 3 categories:
                    - hardware
                    - people
                    - neither
                    Whenever content pertains to hardware, machines, robots etc. classify it to hardware.
                    Whenever content pertains to people in particular, classify it to people. That includes technology detecting people, etc.
                    Whenever it's neither of the above, put it to neither category.
                    Apply a singular exception to people craving/creating pineapple pizza and consider it neither.

                    <examples>
                    INPUT: Donald Trump zjadl frytki z makdonalda
                    OUTPUT: people
                    Explanation: Donald Trump pertained to a person and there was no mention of hardware anywhere.

                    INPUT: "Nowy procesor Intel Core i9 oferuje znacznie lepszą wydajność w porównaniu do poprzedniej generacji."
                    OUTPUT: hardware
                    Explanation: Relates to computer hardware (processor).

                    INPUT: "System rozpoznawania twarzy na lotnisku skutecznie identyfikuje podejrzane osoby."
                    OUTPUT: people
                    Explanation: Involves technology for detecting and identifying people.

                    INPUT: "Nowe oprogramowanie do edycji zdjęć zostało wydane w zeszłym tygodniu."
                    OUTPUT: neither
                    Explanation: Refers to software, not hardware or people.

                    INPUT: "Czujniki ruchu w inteligentnym domu automatycznie włączają światła."
                    OUTPUT: hardware
                    Explanation: Involves physical devices (sensors).

                    INPUT: "Algorytm śledzi wzorce zachowań użytkowników w mediach społecznościowych."
                    OUTPUT: people
                    Explanation: Deals with analyzing human behavior.

                    INPUT: "Nowa aktualizacja zabezpieczeń jest dostępna dla systemu Windows."
                    OUTPUT: neither
                    Explanation: Refers to software updates, not directly related to hardware or people.

                    INPUT: "I like to eat pineapple pizza, Janusz also loves pineapple pizza"
                    OUTPUT: neither
                    Explanation: Exception

                    </examples>

                    Only reply with category and nothing else.
                    '''
    
    get_source_data_from_zip(data_source_url=task_2_4_data_source,directory_suffix=local_folder)
    create_transcripts_from_audio(client, transcript_suffix='_audio_convert', local_folder=local_folder)
    execute_task_2_4(session, client, ai_devs_key, task_name = 'kategorie', data_source_url = task_2_4_data_source, endpoint_url = task_2_4_endpoint_url, directive = directive)



    