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
from api_tasks.neo4j_graph_support import Neo4jGraphDB

# from api_tasks.rag_system_multimodal import RAGSystem


## IMPROVEMENT AREAS 

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
    
def execute_task_3_5(session, client
                     , ai_devs_key:str 
                     , graph_db
                     , task_name:str = ''
                     , data_source_url:str= ''
                     , endpoint_url:str=''
                     , filter_only_active:bool = False
                     , start_of_path:str = ''
                     , end_of_path:str = '') -> None:


    us = query_db("database", ai_devs_key, "select * from users", data_source_url)
    cn = query_db("database", ai_devs_key, "select * from connections", data_source_url)

    id_to_name = {x["id"]:x["username"] for x in us["reply"]}
    
    if filter_only_active:
        people_db = [x for x in us["reply"] if x["is_active"] == '1']
    else:
        people_db = [x for x in us["reply"]]
    
    start_id = next((p["id"] for p in people_db if p["username"] == start_of_path),None)
    end_id = next((p["id"] for p in people_db if p["username"] == end_of_path),None)
    print(f"IDs of concern {start_id} and {end_id}")

    relationships = cn["reply"]

    print('Adding nodes as batch..')
    graph_db.add_nodes_batch("Person", people_db)

    new_dict_list = []
    for erel, xr in enumerate(relationships):
        new_dict_list.append({'from_id': xr["user1_id"], 'to_id': xr["user2_id"], "rel_type" : "connected"})

    graph_db.add_relationships_batch(new_dict_list, symmetrical = True)

    nodes, rels = graph_db.find_shortest_path(start_id, end_id)
    try:
        print(f"Path: {' -> '.join(nodes)}")
        print(f"Relationships: {rels}")
    except:
        pass

    name_string = ', '.join([id_to_name[x].title() for x in nodes])
    print(f'Final solution for shortest path: {name_string}')
    
    json_apt_format = {
        "task": task_name,
        "apikey": ai_devs_key,
        "answer": name_string
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

    task_3_5_data_source = json_secrets["task_3_5_data_source"]
    task_3_5_endpoint_url = json_secrets["task_3_5_endpoint_url"]
    neo4js_password = json_secrets["neo4j_ai_devs_db_password"]

    graph_db = Neo4jGraphDB(
    uri="neo4j://localhost:7687",
    username="neo4j",
    password=neo4js_password
    )
    graph_db.clear_database()

    session = requests.Session()
    
    if 'claude' in model:
        client = Anthropic(api_key=anthropic_api_key)
    if 'gpt' in model:
        client = OpenAI(api_key=open_ai_api_key)
    if model == '_local_model_':
        client = OpenAI(base_url="http://127.0.0.1:1234/v1/",api_key='local')



    execute_task_3_5(session, client, ai_devs_key
                     , graph_db
                     , task_name = 'connections'
                     , data_source_url = task_3_5_data_source
                     , endpoint_url = task_3_5_endpoint_url
                     , start_of_path= 'Rafał'
                     , end_of_path = 'Barbara')

