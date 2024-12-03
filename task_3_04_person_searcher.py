from openai import OpenAI
from anthropic import Anthropic
import json 
import os
import ast 

import asyncio
import requests
from PIL import Image
from icecream import ic


from api_tasks.basic_poligon_u import load_from_json, download_data, get_desired_format, post_request
from api_tasks.get_html_fragment import get_strings_re
from api_tasks.basic_open_ai_calls import gather_calls
# from api_tasks.rag_system_multimodal import RAGSystem


## IMPROVEMENT AREAS 
# Maybe won't improve performance, but incorporate AI to get to end in least amount of queries to DB

def query_db(ai_devs_key:str,query:str, api:str):
    get_schema = {
        "apikey": ai_devs_key,
        "query": query
    }
    webhook_answer = post_request(api, json.dumps(get_schema))

    if str(webhook_answer) == '<Response [200]>':
        schema = json.loads(webhook_answer.content.decode())
        return schema
    else:
        ic(webhook_answer)
        ic(webhook_answer.content.decode())
        return None

def polish_to_english(text):
    polish_chars = {'Ą': 'A','Ć': 'C','Ę': 'E','Ł': 'L','Ń': 'N','Ó': 'O','Ś': 'S','Ź': 'Z','Ż': 'Z'}
    return ''.join(polish_chars.get(char, char) for char in text.upper())

def list_from_query_result(response):
    return [polish_to_english(x) for x in response['message'].split(' ')]

def go_through_names_list(list_of_names:str, type_of_list:str, existing_connections:dict, ai_devs_key:str,  people_url:str = '', places_url:str = '', win_condition:str = ''):
    # For list of people, find places, and other way around
    # nonlocal existing_connections
    target_key = []
    if type_of_list == 'people':
        target_url = people_url
    if type_of_list == 'places':
        target_url = places_url
    retrieval_list = []
    for name in list_of_names:
        name = polish_to_english(name)
        if name in existing_connections.keys():
            continue
        else:
            related = query_db(ai_devs_key=ai_devs_key, query = name, api = target_url)
            if related is not None:
                related = list_from_query_result(related)
                if len(win_condition) > 0 and win_condition in related:
                    target_key.append(name)

                existing_connections[name] = related
                for element in related:
                    retrieval_list.append(element)
                
    return list(set(retrieval_list)), target_key

def execute_task_3_4(session, client
                     , ai_devs_key:str 
                     , task_name:str = ''
                     , data_source_url:str= ''
                     , endpoint_url:str=''
                     , directive:str = ''
                     , people_url:str = ''
                     , places_url:str = ''
                     , win_condition:str = ''
                     , max_iter:int = 10) -> None:


    source_data = download_data(data_source_url).decode()

    ic(source_data)
    list_of_calls = [{'user':source_data,'system':directive}]
    my_answers = asyncio.run(gather_calls(list_of_calls,client = client, tempature=.1, model = model))

    base_dict = ast.literal_eval(my_answers[0])

    existing_connections = dict()

    check_people_first = True
    iteration_count = 0
    mutable_places_list = base_dict["places"].copy()
    mutable_places_list = [polish_to_english(p) for p in mutable_places_list]
    mutable_people_list = base_dict["people"].copy()
    mutable_people_list = [polish_to_english(p) for p in mutable_people_list]

    found_cases = []
    while True:
        if check_people_first:
            iteration_count = iteration_count + 1
            retrieval_list_places, target_key = go_through_names_list(mutable_people_list, 'people', existing_connections, ai_devs_key,  people_url = people_url, places_url = places_url, win_condition = win_condition)
            if len(target_key)>0:
                found_cases.extend(target_key)
            retrieval_list_places = [x for x in retrieval_list_places if '**' not in x]
            mutable_places_list.extend(retrieval_list_places)

            obtained_results_places_c = len(retrieval_list_places)
            check_people_first = False
        if not (check_people_first):
            iteration_count = iteration_count + 1
            retrieval_list_people, target_key = go_through_names_list(mutable_places_list, 'places', existing_connections, ai_devs_key,  people_url = people_url, places_url = places_url, win_condition = win_condition)
            if len(target_key)>0:
                found_cases.extend(target_key)
            retrieval_list_people = [x for x in retrieval_list_people if '**' not in x]
            mutable_people_list.extend(retrieval_list_people)

            obtained_results_people_c = len(retrieval_list_people)
            check_people_first = True 

        # if len(target_key)>0:
        #     ic('Found key!')
        #     break
        if obtained_results_people_c + obtained_results_places_c == 0:
            ic('No new information obtained')
            break
        if iteration_count == max_iter:
            ic('Did not find solution before running out of iterations :/')
            break

        
    for connection in existing_connections.keys():
        ic(f'{connection}:{existing_connections[connection]}')


    ic(found_cases)
    if len(found_cases)>1:
        # Ai call to determine right city..
        
        final_request = [
            {  'user': ','.join(found_cases) 
             , 'system': f'''Consider included text message <text>{source_data}</text>, and decide from this which of these {len(found_cases)} answers is most likely for {win_condition} to be in in current times. 
                We know target was in both places at some point, we're trying to determine the current whereabouts, and keep in mind target strives to remain in hiding, so might not be present in places they were known to be present.
                Keep in mind it doesn't necessarily have to be one mentioned in body of text, try to guess from context. But answer HAS to be one of user inputs.
                Respond with steps of your reasoning.
                '''
             }
             ]
        final_answer_long = asyncio.run(gather_calls(final_request,client = client, tempature=.1, model = model))[0]
        last_word = asyncio.run(gather_calls([{'user':final_answer_long, 'system': 'Extract final answer of this model query, return only single word, in upper case, with no polish characters' }],client = client, tempature=.1, model = model))[0]
        ic(final_answer_long)
        ic(last_word)
    elif len(found_cases)>1:
        last_word = found_cases[0]
    else:
        ic("Nothing found!")
        last_word = ":<"

    json_apt_format = {
        "task": task_name,
        "apikey": ai_devs_key,
        "answer": last_word
    }

    webhook_answer = post_request(endpoint_url, json.dumps(json_apt_format))
    if str(webhook_answer) == '<Response [200]>':
        print(get_strings_re(webhook_answer.content.decode(),pattern=r'{{FLG:(.*?)}}'))
    else:
        ic(webhook_answer)
        ic(webhook_answer.content.decode())

if __name__ == "__main__":
    local_model = False 

    local_folder = r'''C:\Projects\AI_DEVS_3\s_3_02_files\weapons_test\do-not-share'''
    json_secrets = load_from_json(filepath=rf'{os.path.dirname(__file__)}\config.json')

    open_ai_api_key = json_secrets["open_ai_api_key"]
    anthropic_api_key = json_secrets["anthropic_api_key"]
    ai_devs_key = json_secrets["api_key"]
    model = "gpt-4o-mini"

    task_3_4_data_source = json_secrets["task_3_4_data_source"]
    task_3_4_endpoint_url = json_secrets["task_3_4_endpoint_url"]
    people_url = json_secrets["task_3_4_people_url"]
    places_url = json_secrets["task_3_4_places_url"]


    session = requests.Session()
    
    if 'claude' in model:
        client = Anthropic(api_key=anthropic_api_key)
    if 'gpt' in model:
        client = OpenAI(api_key=open_ai_api_key)
    if model == '_local_model_':
        client = OpenAI(base_url="http://127.0.0.1:1234/v1/",api_key='local')


    directive = '''
    You will receive plain text in polish. Please extract all unique location names (cities, towns etc.) and all people names (first names only), and return in upper text, in form of dictionary of list with two keys - 'people' and 'places'. Avoid conjugation of names or places. For example:

    <examples>
    Input text:
    "Wczoraj Marek pojechał do Warszawy, gdzie spotkał się z Anią. Razem zwiedzili Kraków, a potem wrócili do Gdańska. Anna była zachwycona podróżą."

    Output:
    {
        'people': ['MAREK', 'ANIA', 'ANNA'],
        'places': ['WARSZAWA', 'KRAKÓW', 'GDAŃSK']
    }

    Input text:
    "W małym miasteczku Łódź mieszkał Piotr z rodziną. Jego córka Zofia często odwiedzała babcię w Poznaniu. Pewnego dnia Tomek z Wrocławia przyjechał do nich w gości."

    Output:
    {
        'people': ['PIOTR', 'ZOFIA', 'TOMEK'],
        'places': ['ŁÓDŹ', 'POZNAŃ', 'WROCŁAW']
    }

    Input text:
    "Kasia i Michał studiują na uniwersytecie w Toruniu. W weekendy Kasia jeździ do rodziny w Bydgoszczy, a Michał odwiedza swoją dziewczynę Ewę w Olsztynie."

    Output:
    {
        'people': ['KASIA', 'MICHAŁ', 'EWA'],
        'places': ['TORUŃ', 'BYDGOSZCZ', 'OLSZTYN']
    }
    </examples>
    
    Do not return anything besides this output.
      '''
    

    execute_task_3_4(session, client, ai_devs_key
                     , task_name = 'loop'
                     , data_source_url = task_3_4_data_source
                     , endpoint_url = task_3_4_endpoint_url
                     , people_url = people_url
                     , places_url = places_url
                     , directive = directive
                     , win_condition = 'BARBARA'
                    #  , win_condition = 'ZYGFRYD'
                    #  , win_condition = 'AZAZEL'
                     , max_iter= 30
                     )
