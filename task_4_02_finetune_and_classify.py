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
from utilities.generic_utils import for_every_file_in_gen
# from api_tasks.rag_system_multimodal import RAGSystem


## IMPROVEMENT AREAS 

def read_file_for_finetune(file_loc, agenda:str = ''):
    files_validation = [x for x in for_every_file_in_gen(file_loc) if "verify" not in x]
    list_of_finetunes = []
    for file in files_validation:
        classification = os.path.basename(file).split('.')[0]
        with open(file, 'r') as fne:
            for line in fne:
                line = line.strip()  # Remove whitespace/newlines
                direct_dict = prepare_finetune_format_per_entry(line, classification, system_agenda=agenda)
                list_of_finetunes.append(direct_dict)
    return list_of_finetunes

def read_file_for_validation(file_loc):
    files_validation = [x for x in for_every_file_in_gen(file_loc) if "verify" in x]
    dict_of_validation_required = dict()
    for file in files_validation:
        with open(file, 'r') as fne:
            for line in fne:
                line = line.strip().split('=')
                dict_of_validation_required[line[0]] = line[1]
    return dict_of_validation_required

def code_list_to_jsonl(l:list, filename = "input_finetune"):
    import json
    with open(filename, 'w') as f:
        for item in l:
            json.dump(item, f)
            f.write('\n')

def prepare_finetune_format_per_entry(  input:str
                                      , label:str
                                      , system_agenda:str = "") -> dict[str, list[dict[str, str]]]:
    if label not in ("correct", "incorrect"):
        raise Exception("Not valid label - only correct or incorrect")
    return {"messages": [ {"role": "system", "content": system_agenda}
                                      , {"role": "user", "content": input}
                                      , {"role": "assistant", "content": label}]}

def execute_task_4_2(session, client
                     , model:str
                     , valid_dict:dict[str]
                     , ai_devs_key:str 
                     , agenda:str = ''
                     , task_name:str = ''
                     , data_source_url:str= ''
                     , endpoint_url:str='') -> None:


    correct_list = []
    for datapoint in valid_dict.keys():
        dtp_value = valid_dict[datapoint]
        query = [{'user': dtp_value, 'system': agenda}]
        answer = asyncio.run(gather_calls(query, client = client, tempature=.2, model = model))[0]
        ic(answer)
        if answer == 'correct':
            ic(dtp_value)
            correct_list.append(datapoint)

            
    json_apt_format = {
        "task": task_name,
        "apikey": ai_devs_key,
        "answer": correct_list      
    }

    webhook_answer = post_request(endpoint_url, json.dumps(json_apt_format))
    if str(webhook_answer) == '<Response [200]>':
        print(get_strings_re(webhook_answer.content.decode(),pattern=r'{{FLG:(.*?)}}'))
    else:
        ic(webhook_answer)
        ic(webhook_answer.content.decode())

if __name__ == "__main__":

    re_finetune = False
    json_secrets = load_from_json(filepath=rf'{os.path.dirname(__file__)}\config.json')

    open_ai_api_key = json_secrets["open_ai_api_key"]
    anthropic_api_key = json_secrets["anthropic_api_key"]
    ai_devs_key = json_secrets["api_key"]
    model = "gpt-4o-mini"

    task_4_2_data_source = json_secrets["task_4_2_data_source"]
    task_4_2_endpoint_url = json_secrets["task_4_2_endpoint_url"]

    session = requests.Session()

    client = OpenAI(api_key=open_ai_api_key)
    agenda = "You're a classifying agent that will classify every input as either correct or incorrect."

    get_source_data_from_zip(task_4_2_data_source,directory_suffix = '/files_local/s_4_2_lab', extract_sublevel = True)
    list_of_finetunes = read_file_for_finetune(r'C:\Projects\AI_DEVS_3\utilities\s_4_2_lab', agenda = agenda)
    validation_required_dct = read_file_for_validation(r'C:\Projects\AI_DEVS_3\utilities\s_4_2_lab')
    
    code_list_to_jsonl(list_of_finetunes, filename = "input_finetune.jsonl")
    client_ref = client.files.create(
        file=open("input_finetune.jsonl", "rb"),
        purpose="fine-tune"
        )
    
    if re_finetune:
        client.fine_tuning.jobs.create(
            training_file=client_ref.id,
            model="gpt-4o-mini-2024-07-18"
            )
    my_ft_jobs = list(client.fine_tuning.jobs.list(limit=10))

    my_ft_job = my_ft_jobs[0]
    ft_status = my_ft_job.status
    ft_model = my_ft_job.fine_tuned_model
    ft_job = my_ft_job.id

    execute_task_4_2(session, client, ft_model, validation_required_dct, ai_devs_key
                     , task_name = 'research'
                     , agenda = agenda
                     , data_source_url = task_4_2_data_source
                     , endpoint_url = task_4_2_endpoint_url)

    