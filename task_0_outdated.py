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



if __name__ == "__main__":
    local_model = False 

    url_picture ='''https://app.circle.so/rails/active_storage/representations/redirect/eyJfcmFpbHMiOnsibWVzc2FnZSI6IkJBaHBCTXVqcndNPSIsImV4cCI6bnVsbCwicHVyIjoiYmxvYl9pZCJ9fQ==--35cda12c7798afa2518d387f3d9540818b2a3abb/eyJfcmFpbHMiOnsibWVzc2FnZSI6IkJBaDdDRG9MWm05eWJXRjBTU0lKYW5CbFp3WTZCa1ZVT2hSeVpYTnBlbVZmZEc5ZmJHbHRhWFJiQjJrQzBBZHBBdEFIT2dwellYWmxjbnNHT2dwemRISnBjRlE9IiwiZXhwIjpudWxsLCJwdXIiOiJ2YXJpYXRpb24ifX0=--55aee7a1af0e44d97a366265c7c42865f843dbcc/Group%20152.png'''
    # (only argument for completion, not for whisper call)

    local_folder = r'''C:\Projects\AI_DEVS_3\s_2_02_pictures'''
    # local_folder = r'''C:\Projects\AI_DEVS_3\s_2_02_pictures_whole'''
    json_secrets = load_from_json(filepath=rf'{os.path.dirname(__file__)}\config.json')

    open_ai_api_key = json_secrets["open_ai_api_key"]
    anthropic_api_key = json_secrets["anthropic_api_key"]

    ai_devs_key = json_secrets["api_key"]

    session = requests.Session()

    # if local_model:
    #     client = OpenAI(base_url="http://127.0.0.1:1234/v1/",api_key='local')
    # else:
    #     client = OpenAI(api_key=open_ai_api_key)

    if local_model:
        client = Anthropic(base_url="http://127.0.0.1:1234/v1/",api_key='local')
    else:
        client = Anthropic(api_key=anthropic_api_key)

    # descriptions = analyze_images(
    #     client,
    #     local_folder=local_folder,
    #     output_file="descriptions.json"
    #     ,model='gpt-4o-mini'
    #     ,request = '''
    #     You will receive fragment of a map, please analyze this in detail and provide message regarding fragment of which city in Poland do you think this map is showing. 
    #     Considering streets and landmarks you know of, please provide your ranking of at least 3 cities that you find are likely to be source for the map, ranked in most to least probable. 
    #     '''
    # )
    # for d in descriptions.keys():
    #     print(f'For {d}, {descriptions[d]}')
                                # You will receive fragment of a map, please analyze this in detail and provide message regarding fragment of which city/town in Poland do you think this map is showing. 
                                # Considering steet names and other landmarks, provide at least one city/town - but preferably more that will have at least 2 of named streets you have found in close proximity, and return NONE if there are none you can find. 
                                # Consider that there might be typos or OCR errors so it's more important to match several misspelled streets than low amount of exactly spelled streets.

    results = analyze_images_for_text(client
                                      , local_folder=local_folder
                                      , model="claude-3-5-sonnet-20241022"
                                      , model_type='anthropic'
                                      , user_query = 'Please find above image with a maps', system_message=r'''
                                You will receive picture that contains a picture, divided by light vertical and horizontal spaces.
                                Please go through pictures and note any text. If two lines are connected and both annotated by text, additionally mention a crossing.
                                If you have a map with streets Niska crossing with street Zielona, and independent from them street Krzywa, please provide:
                                      - Krzywa
                                      - Zielona
                                      - Niska
                                      - Niska X Zielona
                                Please keep in mind some text is written at an angle or even vertically!
                                '''
                                    #   ,image_urls=[url_picture]
                                      ,image_urls = ['https://pbs.twimg.com/media/FTot7yjWYAQ_tOZ.jpg']
                                      )
    # user_query
    
    # Print results
    for filename, text_content in results.items():
        print(f"\n{filename}:")
        print(text_content)

    overwrite_cache = True
    if overwrite_cache:
        with open('response_bot_on_maps.txt', 'w', encoding='utf-8') as f:
            f.write(text_content)
    
    

                                # Please analyze each map in detail and provide message regarding fragment of which city/town in Poland do you think this map is showing. There is only one town/city that matches at least 3. 
                                # Keep in mind that cities have streets referencing other cities but not themselves:
                                #       Example. Kaliska or Kaliskiego street implies not Kalisz
                                #       Example. Krakowska street implies not Kraków
                                #       Example. Warszawska street implies not Warsaw
                                #       Example. Gdańsk will not have Gdańska street
                                #       Example. Bydgoska street implies not Bydgoszcz 
                                # Consider that there might be typos or OCR errors so it's more important to match several misspelled streets than low amount of exactly spelled streets. 
                                # Go through several cities and explain which streets you could confirm in which map, and use that to reason out which city fulfills the purpose best.

                                
                                # For example:
                                #       If you have a map with streets Niska crossing with street Zielona, and independent from them street Krzywa, please provide:
                                #       - Krzywa
                                #       - Zielona
                                #       - Niska
                                #       - Niska X Zielona