import os
import json

from api_tasks.basic_poligon_u import load_from_json, download_data, get_desired_format, post_request

## IMPROVEMENT AREAS
# Change config to env variable

def execute_task_0():
    # get my token
    json_secrets = load_from_json(filepath=rf'{os.path.dirname(__file__)}\config.json')
    api_key = json_secrets["api_key"]
    # rest of info:
    source = 'https://poligon.aidevs.pl/dane.txt'
    task_name = "POLIGON"
    target_url = 'https://poligon.aidevs.pl/verify'

    # get data
    obtained_file = download_data(source)

    # create dictionary to send
    data = {
        "task": task_name,
        "apikey": api_key,
        "answer": get_desired_format(obtained_file)
    }

    #convert dictionary to json
    json_data = json.dumps(data)

    # send this json
    result = post_request(target_url, json_data)

    print(f'Code : {result} \n Message : {result.content.decode()}')

if __name__ == "__main__":
    execute_task_0()

