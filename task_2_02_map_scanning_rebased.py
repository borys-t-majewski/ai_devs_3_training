from openai import OpenAI
from anthropic import Anthropic
import json 
import os

import asyncio
import requests

from api_tasks.basic_poligon_u import load_from_json, post_request
from api_tasks.get_html_fragment import get_strings_re
from api_tasks.basic_open_ai_calls import gather_calls
from api_tasks.vision_check import analyze_images
from api_tasks.image_processor import analyze_images_for_text

from utilities.read_save_text_functions import get_source_data_from_zip
from utilities.generic_utils import for_every_file_in
from api_tasks.image_encoding_utilities import convert_local_picture,image_to_bytes, extract_text_from_image, easy_ocr_read



if __name__ == "__main__":
    local_model = False 
    claude_or_not = True
    model="claude-3-5-sonnet-20241022"

    url_picture ='''https://app.circle.so/rails/active_storage/representations/redirect/eyJfcmFpbHMiOnsibWVzc2FnZSI6IkJBaHBCTXVqcndNPSIsImV4cCI6bnVsbCwicHVyIjoiYmxvYl9pZCJ9fQ==--35cda12c7798afa2518d387f3d9540818b2a3abb/eyJfcmFpbHMiOnsibWVzc2FnZSI6IkJBaDdDRG9MWm05eWJXRjBTU0lKYW5CbFp3WTZCa1ZVT2hSeVpYTnBlbVZmZEc5ZmJHbHRhWFJiQjJrQzBBZHBBdEFIT2dwellYWmxjbnNHT2dwemRISnBjRlE9IiwiZXhwIjpudWxsLCJwdXIiOiJ2YXJpYXRpb24ifX0=--55aee7a1af0e44d97a366265c7c42865f843dbcc/Group%20152.png'''
    # (only argument for completion, not for whisper call)

    # local_folder = r'''C:\Projects\AI_DEVS_3\s_2_02_pictures_process'''
    # local_folder = r'''C:\Projects\AI_DEVS_3\s_2_02_pictures_whole'''
    json_secrets = load_from_json(filepath=rf'{os.path.dirname(__file__)}\config.json')
    open_ai_api_key = json_secrets["open_ai_api_key"]
    anthropic_api_key = json_secrets["anthropic_api_key"]
    ai_devs_key = json_secrets["api_key"]

    session = requests.Session()
    if claude_or_not:
        client = Anthropic(api_key=anthropic_api_key)
    else:
        if local_model:
            client = OpenAI(base_url="http://127.0.0.1:1234/v1/",api_key='local')
        else:
            client = OpenAI(api_key=open_ai_api_key)

    

    
    
    # response = requests.get(url_picture)
    # temp_path = r'C:\Projects\AI_DEVS_3\s_2_02_pictures_process\temp.png'
    # with open(temp_path, 'wb') as f:
    #     f.write(response.content)
    

    list_of_pngs = for_every_file_in('C:\Projects\AI_DEVS_3\s_2_02_pictures')
    # irrelevant_local_picture = convert_local_picture(temp_path)
    irrelevant_local_picture = convert_local_picture(list_of_pngs[0])
    local_format = irrelevant_local_picture[1].split('.')[-1].upper()
    
    my_questions = []
    for file in list_of_pngs:
        
        image_2_use = image_to_bytes(convert_local_picture(file)[0],format=local_format)
        my_base_question = {'user':[
                    {'type':'text','text':'describe picture'}
                    ,{'type':'image_local','local_path':image_2_use}
                    ]
                    ,'system':r'''
                                    You will receive picture that contains a picture, divided by light vertical and horizontal spaces.
                                    Please go through pictures and note any text. If two lines are connected and both annotated by text, additionally mention a crossing.
                                    If you have a map with streets Niska crossing with street Zielona, and independent from them street Krzywa, please provide:
                                        - Krzywa
                                        - Zielona
                                        - Niska
                                        - Niska X Zielona
                                    Please keep in mind some text is written at an angle or even vertically! Be sure to return only streets and crossings'''}
        my_questions.append(my_base_question)

    # image_to_bytes(irrelevant_local_picture[0],format=local_format)

    my_answers = asyncio.run(gather_calls(my_questions,client = client, tempature=0.4, max_tokens=4096, model = model,force_refresh=False))
    for an,answer in enumerate(my_answers):
        print(f'''\n For model {model}, query {an}: {answer}''')

    final_question = {'user':[
                    {'type':'text','text':f'''
                     I will share with you 4 different descriptions of streets, crossing between them and landmarks that are all in Poland. At least 3 of them are from one city/town in Poland. Please reason one by one for each of these inputs and return your final answer. If you can't match exactly any city, consider next best one, but try to be precise if possible.
                     {''.join(['<DESCRIPTION> ' + answer + '</DESCRIPTION>' for answer in my_answers])}
                     '''}
                    ]
                    ,'system':r'''
                                    You are reasoning in steps and looking at each case individually before reaching final conclusion. 
                                    You need to look into your exact data regarding geography, and avoid reasoning such as "this street sounds like a city near", as it's common to have streets that reference cities far away.
                                    AND IT'S NOT TORUŃ
                                    '''}
    
    print(final_question)

    client_open_ai = OpenAI(api_key=open_ai_api_key)

    final_answer = asyncio.run(gather_calls([final_question],client = client, tempature=0.4, max_tokens=4096, model = model,force_refresh=True))
    print(final_answer)
    final_answer = asyncio.run(gather_calls([final_question],client = client_open_ai, tempature=0.4, max_tokens=4096, model = 'gpt-4o',force_refresh=True))
    print(final_answer)