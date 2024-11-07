from openai import OpenAI
import json 
import os

import asyncio
import requests
from bs4 import BeautifulSoup

from api_tasks.basic_poligon_u import load_from_json
from api_tasks.get_html_fragment import get_strings_re
from api_tasks.website_interactions import scrape_site
from api_tasks.basic_open_ai_calls import gather_calls
from api_tasks.ready_logins import login_to_website

## IMPROVEMENT AREAS
# Change config to env variable
# Explore rare random issue when answer is generated properly, but proper flag is not returned?

def get_this_secret_info_from_website(username, password, login_url, target_url,save_website_locally = True, max_retries = 5):
    session = requests.Session()
    
    website_html = scrape_site(session, login_url)
    right_question = get_strings_re(website_html)
    
    # Call openai for help :/ 
    client = OpenAI(api_key=api_key)
    my_questions = [
      { 'user':right_question
       ,'system':'Question will be in polish. Reply only with single number pertaining to question. Answer will be a positive integer. Only in case it is not possible to return positive number as answer to question, return 0.'
       ,'assistant': 'Reply with number only.'
       }
    ]
    
    retry_c = 0
    while retry_c < max_retries:
        retry_c = retry_c + 1
        my_answers = asyncio.run(gather_calls(my_questions,client = client))
        try:
            if int(my_answers[0]) != 0 and my_answers is not None:
                break
            else:
                pass
        except:
            pass
    
    # should be username, password, answer (for captcha)
    # Prepare login data
    print(f"Received answer: {my_answers[0]}")

    success, info = login_to_website(target_url, username, password, my_answers[0])
    
    if save_website_locally:
        with open('response.html', 'w', encoding='utf-8') as f:
            f.write(info.text)
    secret_code_now = get_strings_re(info.text,pattern=r'{{FLG:(.*?)}}')
    return secret_code_now



if __name__ == "__main__":
    json_secrets = load_from_json(filepath=rf'{os.path.dirname(__file__)}\config.json')
    api_key = json_secrets["open_ai_api_key"]

    LOGIN_URL = json_secrets["LOGIN_URL"]
    TARGET_URL = json_secrets["TARGET_URL"]

    USERNAME = json_secrets["USERNAME"]
    PASSWORD = json_secrets["PASSWORD"]
    

    final_secret_code = get_this_secret_info_from_website(USERNAME, PASSWORD, LOGIN_URL, TARGET_URL)
    print(final_secret_code)
    