from openai import OpenAI
from anthropic import Anthropic
import json 
import os
from neo4j import GraphDatabase

import asyncio
import requests
from PIL import Image
from icecream import ic

from api_tasks.basic_poligon_u import load_from_json, post_request, download_data
from api_tasks.get_html_fragment import get_strings_re
from api_tasks.basic_open_ai_calls import gather_calls, opai_call
from utilities.read_save_text_functions import get_source_data_from_zip
from utilities.generic_utils import for_every_file_in_gen
from api_tasks.website_ai_translation import get_website_and_describe_with_ai
from api_tasks.task_5_02_prompts import *
from api_tasks.task_5_02_functions import *
# from api_tasks.rag_system_multimodal import RAGSystem


## IMPROVEMENT AREAS 
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
    

    

def execute_task_5_2(session, client
                     , ai_devs_key
                     , task_name:str
                     , model:str
                     , data_source_url:str= ''
                     , question_source:str= ''
                     , people_url:str= ''
                     , places_url:str= ''
                     , db_url:str= ''
                     , endpoint_url:str=''
                     , temperature = 0.1) -> None:

    print("start")

    logs = download_data(data_source_url,decode=True)
    print(type(ic))
    ic(logs)

    qs = json.loads(download_data(question_source,decode=True))["question"]
    print(qs)

    agent_comprehension = understand_agent(logs)
    agent_comprehension_a = asyncio.run(gather_calls([agent_comprehension],client = client, model = model, tempature=temperature,force_refresh=True))[0]
    ic(agent_comprehension_a)

    gps_url = get_api_url(logs, [places_url, people_url, db_url, endpoint_url])
    gps_url_a = asyncio.run(gather_calls([gps_url],client = client, model = model, tempature=temperature,force_refresh=True))[0]

    manual_implementation_reference = False

    if manual_implementation_reference:
        peepz = go_through_names_list(["Lubawa"], "places", ai_devs_key=ai_devs_key, people_url=people_url, places_url=places_url, output_type = "uniq_list")
        ic(peepz)
        peepz_f = filterer(peepz, ['BARBARA'])
        ic(peepz_f)
        peepz_ids = sql_framing(ai_devs_key=ai_devs_key, task_name = "database", data_source_url=db_url
                            , plainword_question=f"Find list of ids and names of given group of people: {peepz_f}"
                            , steering_system= 
                            '''Using information about database system below 
                            {DBINFO}
                            create SQL query that best answers user question. Return only SQL query, and reply with no quotes around it.
                            ''', client=client, model=model)

        ic(peepz_ids)
        coords_example = get_coords(peepz_ids, task_name, ai_devs_key,"https://centrala.ag3nts.org/gps")
        ic(coords_example)

    else:
        tools_unpacked = toolbag()

        plan_comprehension = get_plan(qs
                                    ,str(tools_unpacked)
                                    ,agent_comprehension_a)


        plan_comprehension_a = asyncio.run(gather_calls([plan_comprehension],client = client, model = model, tempature=temperature,force_refresh=True))[0]
        ic(plan_comprehension_a)

        steps = [line.strip() for line in plan_comprehension_a.split('\n') if line.strip() and line[0].isdigit()]
        for s in steps:
            guesser = finder(s,["go_through_names_list", "sql_framing", "filterer", "get_coords"])
            tooled_plan = put_step_to_tool(s, tools_unpacked, guesser)
            tooled_plan_a = asyncio.run(gather_calls([tooled_plan],client = client, model = model, tempature=temperature,force_refresh=True, tools=tools_unpacked))[0]
            ic(tooled_plan_a)
            for tool_call in tooled_plan_a.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                if function_name == "go_through_names_list":
                    intermediate = go_through_names_list([function_args['list_of_names']], function_args["type_of_list"],ai_devs_key=ai_devs_key, people_url=people_url, places_url=places_url, output_type = "uniq_list")
                elif function_name == "filterer":
                    intermediate = filterer(intermediate, function_args["cond"])
                elif function_name == "sql_framing":
                    intermediate = sql_framing(ai_devs_key=ai_devs_key, task_name = "database", data_source_url=db_url
                            , plainword_question=function_args['plainword_question']+','.join(intermediate)
                            , steering_system=function_args['steering_system'], client=client, model=model)
                elif function_name == "get_coords":
                    intermediate = get_coords(intermediate, task_name, ai_devs_key, gps_url_a)

                ic(intermediate)

        coords_example = intermediate


    json_apt_format = {
        "task": task_name,
        "apikey": ai_devs_key,
        "answer": intermediate      
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
    # model = "gpt-4o-mini"
    model = "gpt-4o"

    task_5_2_data_source = json_secrets["task_5_2_data_source"].replace('TUTAJ-KLUCZ',ai_devs_key)
    task_5_2_question_source = json_secrets["task_5_2_question_source"].replace('TUTAJ-KLUCZ',ai_devs_key)
    task_5_2_people_url = json_secrets["task_5_2_people_url"]
    task_5_2_places_url = json_secrets["task_5_2_places_url"]
    task_5_2_db = json_secrets["task_5_2_db"]
    task_5_2_endpoint_url = json_secrets["task_5_2_endpoint_url"]

    session = requests.Session()
    
    if 'claude' in model:
        client = Anthropic(api_key=anthropic_api_key)
    if 'gpt' in model:
        client = OpenAI(api_key=open_ai_api_key)
    if model == '_local_model_':
        client = OpenAI(base_url="http://127.0.0.1:1234/v1/",api_key='local')

    
    
    execute_task_5_2(session, client, ai_devs_key
                     , task_name = 'gps'
                     , model = model
                     , data_source_url = task_5_2_data_source
                     , endpoint_url = task_5_2_endpoint_url
                     , question_source=task_5_2_question_source
                     , people_url=task_5_2_people_url
                     , places_url=task_5_2_places_url
                     , db_url=task_5_2_db
                     )

    