from openai import OpenAI
from anthropic import Anthropic
import json 
import os

import asyncio
import requests
from PIL import Image
from icecream import ic

from api_tasks.basic_poligon_u import load_from_json, post_request
from api_tasks.get_html_fragment import get_strings_re
from api_tasks.basic_open_ai_calls import gather_calls
# from api_tasks.rag_system_multimodal import RAGSystem


## IMPROVEMENT AREAS 
# Actually do it without any hardcoded idea, just providing commands or even without that
def query_db(task_name:str, ai_devs_key:str,query:str, data_source_url:str):
    get_schema = {
        "task": task_name,
        "apikey": ai_devs_key,
        "query": query
    }
    webhook_answer = post_request(data_source_url, json.dumps(get_schema))

    if str(webhook_answer) == '<Response [200]>':
        schema = json.loads(webhook_answer.content.decode())
        return schema
    else:
        ic(webhook_answer)
        ic(webhook_answer.content.decode())
        return None
    
def execute_task_3_3(session, client
                     , ai_devs_key:str 
                     , task_name:str = ''
                     , data_source_url:str= ''
                     , endpoint_url:str=''
                     , plainword_question:str = ''
                     , steering_system:str = '') -> None:

    schema = query_db(task_name, ai_devs_key, "show tables", data_source_url)
    tables = [x["Tables_in_banan"] for x in schema["reply"]]

    db_information = []
    for table in tables:
        table_info = query_db(task_name, ai_devs_key, f"show create table {table}", data_source_url)
        db_information.append(table_info["reply"][0]['Create Table'])


    query = [{'user': plainword_question, 'system':steering_system.replace('DBINFO','\n'.join(db_information))}]
    SQL_request = asyncio.run(gather_calls(query, client = client, tempature=.2, model = model))

    answer_from_sql = query_db(task_name, ai_devs_key, SQL_request[0], data_source_url)
    ic(answer_from_sql)

    answer_list = []
    if answer_from_sql["error"] == 'OK':
        ic('Successful query answer')
        for r in answer_from_sql["reply"]:
            answer_list.append(int(r["dc_id"]))
            ic(answer_list)
    else:
        ic('Issue with getting SQL query')


    json_apt_format = {
        "task": task_name,
        "apikey": ai_devs_key,
        "answer": answer_list
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

    task_3_3_data_source = json_secrets["task_3_3_data_source"]
    task_3_3_endpoint_url = json_secrets["task_3_3_endpoint_url"]

    session = requests.Session()
    
    if 'claude' in model:
        client = Anthropic(api_key=anthropic_api_key)
    if 'gpt' in model:
        client = OpenAI(api_key=open_ai_api_key)
    if model == '_local_model_':
        client = OpenAI(base_url="http://127.0.0.1:1234/v1/",api_key='local')


    plainword_question = '''które aktywne datacenter (DC_ID) są zarządzane przez pracowników, którzy są na urlopie (is_active=0)'''
    
    steering_system = '''Using information about database system below 
                      {DBINFO}
                      create SQL query that best answers user question. Return only SQL query, and reply with no quotes around it.
                      '''

    execute_task_3_3(session, client, ai_devs_key
                     , task_name = 'database'
                     , data_source_url = task_3_3_data_source
                     , endpoint_url = task_3_3_endpoint_url
                     , plainword_question = plainword_question
                     , steering_system = steering_system)

