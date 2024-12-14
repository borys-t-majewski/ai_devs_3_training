import asyncio 
from icecream import ic
from api_tasks.basic_open_ai_calls import gather_calls
from api_tasks.basic_poligon_u import load_from_json, post_request, download_data
import json 

def toolbag():
    return [
    {
        "type": "function",
        "function": {
            "name": "go_through_names_list",
            "description": "Process a list of names and find related people or places based on the type of list specified",
            "parameters": {
                "type": "object",
                "properties": {
                    "list_of_names": {
                        "type": "string",
                        "description": "List of names to process"
                    },
                    "type_of_list": {
                        "type": "string",
                        "description": "Type of list to process ('people' or 'places'). You select 'people' when your search term is a person, and 'places' when your search term is a place.",
                        "enum": ["people", "places"]
                    }
                },
                "required": ["list_of_names", "type_of_list"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sql_framing",
            "description": '''Execute SQL queries against a database with specific schema for users, connections, correct_order, and datacenters tables. 
            It contains username (same as name) and id, doesn't contain location!!
            To connect usernames and ids, select both usernames and ids.
            It accepts following syntax: select, show tables, desc table, show create table
            
            ''',
            "parameters": {
                "type": "object",
                "properties": {
                    "plainword_question": {
                        "type": "string",
                        "description": "Natural language query to be converted to SQL",
                        "default": ""
                    },
                    "steering_system": {
                        "type": "string",
                        "description": "System prompt for query generation",
                        "default": ""
                    }
                },
                "required": ["plainword_question", "steering_system"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "filterer",
            "description": "Remove elements from a list if they exist in another list (case-insensitive)",
            "parameters": {
                "type": "object",
                "properties": {
                    "list_input": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Input list to filter"
                    },
                    "cond": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of conditions to filter against"
                    }
                },
                "required": ["list_input", "cond"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_coords",
            "description": "Get coordinates for a list of user IDs and names",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id_list": {
                        "type": "object",
                        "description": "Dictionary mapping user IDs to names",
                        "additionalProperties": {"type": "string"}
                    }
                },
                "required": ["user_id_list"]
            }
        }
    }
]

def go_through_names_list(list_of_names:str, type_of_list:str, ai_devs_key:str,  people_url:str = '', places_url:str = '', output_type = "set_of_dict") -> dict:
    # For list of people, find places, and other way around
    # nonlocal existing_connections
    ''' Find people by locations OR find locations by people'''

    def polish_to_english(text):
        polish_chars = {'Ą': 'A','Ć': 'C','Ę': 'E','Ł': 'L','Ń': 'N','Ó': 'O','Ś': 'S','Ź': 'Z','Ż': 'Z'}
        return ''.join(polish_chars.get(char, char) for char in text.upper())
    def list_from_query_result(response):
        return [polish_to_english(x) for x in response['message'].split(' ')]
    def check_spec_db(ai_devs_key:str,query:str, api:str):
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

    
    if output_type == 'set_of_dict':
        existing_connections = dict()
    if output_type == 'uniq_list':
        existing_connections = []

    if type_of_list == 'people':
        target_url = people_url
    if type_of_list == 'places':
        target_url = places_url
    for name in list_of_names:
        name = polish_to_english(name)
        related = check_spec_db(ai_devs_key=ai_devs_key, query = name, api = target_url)
        if related is not None:
            related = list_from_query_result(related)
            if output_type == 'set_of_dict':
                existing_connections[name] = related
            if output_type == 'uniq_list':
                for element in related:
                    existing_connections.append(element)
                existing_connections = list(set(existing_connections))
            
    return existing_connections
    

def sql_framing(ai_devs_key:str 
                     , task_name:str = ''
                     , data_source_url:str= ''
                     , plainword_question:str = ''
                     , steering_system:str = ''
                     , client:str = ''
                     , model:str = '') -> dict:

    '''
    Searches DB that has:
    CREATE TABLE `connections` (
    `user1_id` int(11) NOT NULL,
    `user2_id` int(11) NOT NULL,
    PRIMARY KEY (`user1_id`,`user2_id`)
    ) 

    CREATE TABLE `correct_order` (
    `base_id` int(11) DEFAULT NULL,
    `letter` char(1) DEFAULT NULL,
    `weight` int(11) DEFAULT 0
    ) 

    CREATE TABLE `datacenters` (
    `dc_id` int(11) DEFAULT NULL,
    `location` varchar(30) NOT NULL,
    `manager` int(11) NOT NULL DEFAULT 31,
    `is_active` int(11) DEFAULT 0
    ) 

    CREATE TABLE `users` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `username` varchar(20) DEFAULT NULL,
    `access_level` varchar(20) DEFAULT 'user',
    `is_active` int(11) DEFAULT 1,
    `lastlog` date DEFAULT NULL,
    PRIMARY KEY (`id`)
    ) 

    returns a requested query
    '''

    def db_api(task_name:str, ai_devs_key:str,query:str, data_source_url:str):
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
    
    schema = db_api(task_name, ai_devs_key, "show tables", data_source_url)
    tables = [x["Tables_in_banan"] for x in schema["reply"]]

    db_information = []
    for table in tables:
        table_info = db_api(task_name, ai_devs_key, f"show create table {table}", data_source_url)
        db_information.append(table_info["reply"][0]['Create Table'])

    query = [{'user': plainword_question, 'system':steering_system.replace('DBINFO','\n'.join(db_information)) + '''Remember to ONLY output relevant SQL code, no text after or before. It has to start with a SELECT. Do NOT start with "sql" !!!'''}]
    SQL_request = asyncio.run(gather_calls(query, client = client, tempature=.2, model = model))
    ic(SQL_request)
    answer_from_sql = db_api(task_name, ai_devs_key, SQL_request[0], data_source_url)
    ic(answer_from_sql)

    # answer_dict = dict()
    # answer_list = []
    answer_list = dict()
    if answer_from_sql["error"] == 'OK':
        ic('Successful query answer')
        ic(answer_from_sql)
        for r in answer_from_sql["reply"]:
            # answer_list.append(r["id"])
            
            answer_list[r["id"]] = r["username"]
    else:
        ic('Issue with getting SQL query')

    return answer_list

def filterer(list_input:list,cond:list):
    '''Remove element from list if its in another list'''
    COND = [x.upper() for x in cond]
    return [x for x in list_input if x.upper() not in COND]
            

    
def get_coords(user_id_list, task_name:str, ai_devs_key:str, data_source_url:str):
    ''' takes a list of dicts [{str:int}]
    , gets dictionary of dictionary coordinates like:
    
    [{"janusz":53}, {"korwin":11}]
    to
    {
        "janusz": {
            "lat": 12.345,
            "lon": 65.431
        },
        "korwin": {
            "lat": 19.433,
            "lon": 12.123
        }
    }
    '''
    def coord_ask(task_name:str, ai_devs_key:str,query, data_source_url:str):
        get_schema = {
            "task": task_name,
            "apikey": ai_devs_key,
            "userID": query
        }
        print(get_schema)
        webhook_answer = post_request(data_source_url, json.dumps(get_schema))

        print(webhook_answer)
        print(webhook_answer.content)
        if str(webhook_answer) == '<Response [200]>':
            schema = json.loads(webhook_answer.content.decode())
            return schema
        else:
            ic(webhook_answer)
            ic(webhook_answer.content.decode())
            return None
    final_dict = dict()
    for id in user_id_list.keys():
        lat_lon = coord_ask(task_name, ai_devs_key, id, data_source_url)
        given_name = user_id_list[id]
        if lat_lon["code"] == 0:
            final_dict[given_name] = lat_lon["message"]

    return final_dict


def finder(bigstring, lstr):
    for l in lstr:
        if l in bigstring:
            return l
    return None 