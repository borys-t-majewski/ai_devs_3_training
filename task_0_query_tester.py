from openai import OpenAI
from anthropic import Anthropic
import os

import asyncio
import requests

from api_tasks.basic_poligon_u import load_from_json
from api_tasks.basic_open_ai_calls import gather_calls
from api_tasks.image_encoding_utilities import convert_local_picture, image_to_bytes


## IMPROVEMENT AREAS
# Change config to env variable
# Explore rare random issue when answer is generated properly, but proper flag is not returned?
# Try local model
    # Local model works good with this prompt! LLAMA 8B




if __name__ == "__main__":
    local_model = False 

    model_list = ["claude-3-5-sonnet-20241022","_local_model_", "gpt-4o-mini","gpt-4o"]
    model_list = ["claude-3-5-sonnet-20241022", "gpt-4o-mini"]
    model_list = [ "gpt-4o-mini"]
    # model_list = ["claude-3-5-sonnet-20241022"]

    temperature = 0.5
    max_tokens = 4096
    
    json_secrets = load_from_json(filepath=rf'{os.path.dirname(__file__)}\config.json')
    open_ai_api_key = json_secrets["open_ai_api_key"]
    anthropic_api_key = json_secrets["anthropic_api_key"]

    for model in model_list:
        
        if 'claude' in model:
            client = Anthropic(api_key=anthropic_api_key)
        if 'gpt' in model:
            client = OpenAI(api_key=open_ai_api_key)
        if model == '_local_model_':
            client = OpenAI(base_url="http://127.0.0.1:1234/v1/",api_key='local')

    # user should be either string (just text) or list of dicts 
    
    # Accepts either string, or LIST
    # in user message. If more than two arguments, use a dictionary in such format:
    # [{type: "text", text:"your actual message"},{type: "image", url: "actual_image_url"}]
    # in any order.
    # below is a low res cat picture, smarter to change to something I own later
    # If local path to the image, then

    # FLOW:
    # If local image, can apply transform function to get another local image , which is then contributed in 
    # {type: "image_local", local_path: "path 2 image"}
    # If url image, you can download it with x and then apply transfer function and continue as above
        

        irrelevant_internet_picture = '''
        https://pbs.twimg.com/media/FTot7yjWYAQ_tOZ.jpg
        '''
        # https://pbs.twimg.com/media/FTot7yjWYAQ_tOZ.jpg

        irrelevant_local_picture = r'''C:\Users\Borys\Downloads\PaleCourt-master\assets\Zemer.png'''
        irrelevant_local_picture = convert_local_picture(irrelevant_local_picture)
        local_format = irrelevant_local_picture[1].split('.')[-1].upper()

        my_questions = [
          {'user':'What is the capital of India?','system':'Reply only in lowercase.'}
          ,{'user':[
                 {'type':'text','text':'please describe the picture below'}
                ,{'type':'image','url':irrelevant_internet_picture}
                ]
            ,'system':'Reply only in uppercase and describe the picture. Be sure to be very impressed.'}
         ,{'user':f'{irrelevant_internet_picture}','system':'Reply only in snakecase and describe the picture.'}
           #This is supposed to not work
         ,{'user':[
                 {'type':'text','text':'please describe the picture below'}
                ,{'type':'image_local','local_path':image_to_bytes(irrelevant_local_picture[0],format=local_format)}
                ]
            ,'system':'Describe the picture. Be sure to be very impressed.'}
        ]

        
        my_answers = asyncio.run(gather_calls(my_questions,client = client, tempature=temperature, max_tokens=max_tokens, model = model))
        for an,answer in enumerate(my_answers):
            print(f'''\n For model {model}, query {an}: {answer}''')


# Claude has random access problems, like see IDs:
# 2024-11-15 15:09:29	req_01MVbw3F9wTnNiVZnJWLp4p4	claude-3-5-sonnet-20241022	
# 2024-11-15 15:08:41	req_01U21w8ZfFsn1SabsZbyL7Qa	claude-3-5-sonnet-20241022	
# which should have same tokens in and no tokens out at one of them 