from openai import OpenAI
from anthropic import Anthropic
import json 
import os
from neo4j import GraphDatabase

import asyncio
import requests
from PIL import Image
from icecream import ic

from api_tasks.basic_poligon_u import load_from_json, post_request
from api_tasks.get_html_fragment import get_strings_re
from api_tasks.basic_open_ai_calls import gather_calls
from utilities.read_save_text_functions import get_source_data_from_zip
# from api_tasks.rag_system_multimodal import RAGSystem


## IMPROVEMENT AREAS 

async def flight_evaluator(client, model, user_input, temperature = 0.05):
    map_input = '''
                        <map>
                        - X:1 Y:1 - Location pin
                        - X:2 Y:1 - Grass
                        - X:3 Y:1 - Tree
                        - X:4 Y:1 - House

                        - X:1 Y:2 - Grass
                        - X:2 Y:2 - Windmill
                        - X:3 Y:2 - Grass
                        - X:4 Y:2 - Grass

                        - X:1 Y:3 - Grass
                        - X:2 Y:3 - Grass
                        - X:3 Y:3 - Rocks
                        - X:4 Y:3 - Trees

                        - X:1 Y:4 - Mountains
                        - X:2 Y:4 - Mountains
                        - X:3 Y:4 - Car
                        - X:4 Y:4 - Cave
                        </map>
    '''

    examples_q_1 = '''
                    Example 1:
                    Input: "Lecę w dół, następnie trzy pola w prawo"
                    Output:
                    Start: X:1 Y:1 - Punkt startowy (Location pin)
                    Ruch w dół: X:1 Y:2 - Trawa
                    Skręt w prawo: X:2 Y:2 - Wiatrak
                    Kontynuacja: X:3 Y:2 - Trawa
                    Końcowa pozycja: X:4 Y:2 - Trawa

                    Example 2:
                    Input: "Lecę na samo prawo, potem w dół do końca mapy"
                    Output:
                    Start: X:1 Y:1 - Punkt startowy (Location pin)
                    Ruch w prawo: X:2 Y:1 - Trawa
                    Dalej w prawo: X:3 Y:1 - Drzewo
                    Dalej w prawo: X:4 Y:1 - Dom
                    W dół: X:4 Y:2 - Trawa
                    Dalej w dół: X:4 Y:3 - Drzewa
                    Końcowa pozycja: X:4 Y:4 - Jaskinia

                    Example 3:
                    Input: "Lecę na ukos - jedno pole w prawo i jedno w dół"
                    Output:
                    Start: X:1 Y:1 - Punkt startowy (Location pin)
                    Ruch w prawo: X:2 Y:1 - Trawa
                    Ruch w dół: X:2 Y:2 - Wiatrak
                    Końcowa pozycja: X:2 Y:2 - Wiatrak

                    Example 4:
                    Input: "Lecę w dół, jedno pole w prawo a potem w lewo"
                    Output:
                    Start: X:1 Y:1 - Punkt startowy (Location pin)
                    Ruch w dół: X:1 Y:2 - Trawa
                    Ruch w prawo: X:2 Y:2 - Wiatrak
                    Ruch w lewo: X:1 Y:2 - Trawa

                    Example 5:
                    Input: "Lecę 2 pola w prawo"
                    Output:
                    Start: X:1 Y:1 - Punkt startowy (Location pin)
                    Ruch w prawo: X:2 Y:1 - Trawa
                    Ruch w prawo: X:3 Y:1 - Drzewo

                    Input: "Lecę 3 pola w prawo, i 2 pola w lewo"
                    Output:
                    Start: X:1 Y:1 - Punkt startowy (Location pin)
                    Ruch w prawo: X:2 Y:1 - Trawa
                    Ruch w prawo: X:3 Y:1 - Drzewo
                    Ruch w prawo: X:4 Y:1 - Dom
                    Ruch w lewo: X:3 Y:1 - Drzewo
                    Ruch w lewo: X:2 Y:1 - Trawa                    
                    '''
    query = [{'user': user_input
              , 'system': f'''
                        You're a drone flight coordinator.
                        You will receive input in polish in natural language about some kind of movement, or directions.
                        Considering the map below, you're always starting in the X:1 Y:1 (Location Pin) field, and need to evaluate in which field you will end up after flight.
                        When input describes going to far right, or to the end, or end of map("skrajne prawo", "na sam koniec", "do końca mapy") or similar, move to end of map, otherwise move by number of times specified, if not specified move by 1.

                        Going right will increase X coordinate by 1.
                        Going left will decrease X coordinate by 1.
                        Going down will increase Y coordinate by 1.
                        Going up will decrease Y coordinate by 1.
                        Return step by step description of every square your drone visits, every visit in new line, and write out coordinates as well.
                        {map_input}

                        {examples_q_1}

              '''}] 
    
    # query_answer = asyncio.run(gather_calls(query, client = client, tempature=temperature, model = model))[0]
    # loop = asyncio.get_event_loop()
    # query_answer = loop.run_until_complete(gather_calls(query, client = client, tempature=temperature, model = model))[0]

    query_answer_c = await gather_calls(query, client = client, tempature=temperature, model = model)
    query_answer = query_answer_c[0]

    final_evaluator_query = [{'user': query_answer
              , 'system': f'''
                        You're a drone flight coordinator.
                        You will receive description of flight. Just extract the description of final destination of flight, and return it in polish. 
                        Do not return anything else besides this description - skip the coordinates as well. Do not say that it's "final position" or anything about it, it's implicit.
                        Odpowiedz po polsku
              '''}]
    # final_location = asyncio.run(gather_calls(final_evaluator_query, client = client, tempature=temperature, model = model))[0]
    # loop = asyncio.get_event_loop()

    final_location_c = await gather_calls(final_evaluator_query, client = client, tempature=temperature, model = model)
    final_location = final_location_c[0]


    return [final_location, query_answer]
    
async def test_cases(client, model, list:list):
    q_a = dict()
    for test_case in list:
        response = await flight_evaluator(client, model, test_case)
        ic(type(response))
        q_a[test_case] = response
    return q_a 

async def execute_tests():
    case_list = [ "W prawo i dwa pola w dół"
                 , "W prawo w lewo w prawo w lewo"
                 , "Dwa w dół, dwa w prawo, dwa w lewo"
                 , "Trzy pola w prawo i jedno pole w dół"
                 , "Na sam dół, dwa w prawo i w górę"
                 , "Na sam dół, na skrajne prawo, i na samą górę"
                 , "Polecimy na sam dół mapy, a później o dwa pola w prawo. Co tam jest?" #test of problem case
                 ]
    results = await test_cases(client, model, case_list)
    
    ic(results)
    for case in results.keys():
        ic(case)
    for case in results.keys():
        print(f'{case} : {results[case][0]}')
        print(f'{case} : {results[case][1]}')

def execute_task_4_4(session, client
                     , ai_devs_key:str 
                     , task_name:str = ''
                     , api_url:str = ''
                     , endpoint_url:str='') -> None:


    json_apt_format = {
        "task": task_name,
        "apikey": ai_devs_key,
        "answer": api_url      
    }

    webhook_answer = post_request(endpoint_url, json.dumps(json_apt_format))
    if str(webhook_answer) == '<Response [200]>':
        print(get_strings_re(webhook_answer.content.decode(),pattern=r'{{FLG:(.*?)}}'))
    else:
        ic(webhook_answer)
        ic(webhook_answer.content.decode())

if __name__ == "__main__":
    local_model = False 

    json_secrets = load_from_json(filepath=rf'{os.path.dirname(__file__)}\config.json')

    open_ai_api_key = json_secrets["open_ai_api_key"]
    anthropic_api_key = json_secrets["anthropic_api_key"]
    ai_devs_key = json_secrets["api_key"]
    model = "gpt-4o-mini" 


    task_4_4_data_source = json_secrets["task_4_4_data_source"]
    task_4_4_endpoint_url = json_secrets["task_4_4_endpoint_url"]
    task_4_4_map_image = json_secrets["task_4_4_map_image"]
    task_4_4_azyl_url = json_secrets["task_4_4_azyl_url"]

    session = requests.Session()
    
    if 'claude' in model:
        client = Anthropic(api_key=anthropic_api_key)
    if 'gpt' in model:
        client = OpenAI(api_key=open_ai_api_key)
    if model == '_local_model_':
        client = OpenAI(base_url="http://127.0.0.1:1234/v1/",api_key='local')

    testing_mode = False
    exec_mode = True
    # testing_mode = True
    # exec_mode = False
    if testing_mode:
        asyncio.run(execute_tests())
    

    if exec_mode:
        execute_task_4_4(session, client
                        , ai_devs_key 
                        , "webhook"
                        , api_url = task_4_4_azyl_url
                        , endpoint_url = task_4_4_endpoint_url)
    