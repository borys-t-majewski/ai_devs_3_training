from openai import OpenAI
from anthropic import Anthropic
import json 
import os
from pyquery import PyQuery as pq

import asyncio
import requests
from icecream import ic

from api_tasks.get_html_fragment import get_strings_re
from api_tasks.basic_open_ai_calls import gather_calls
from api_tasks.pyquery_link_searcher import get_filtered_links
from api_tasks.basic_poligon_u import load_from_json, download_data, post_request, load_from_json


## IMPROVEMENT AREAS 

def just_text(url):
    from pyquery import PyQuery as pq 
    response = requests.get(url)
    response.raise_for_status()
    # return pq(response.text).text() #:<<<
    return pq(response.text).html()

def ask_ai_for_opinion_on_content(text, question, model, client, temperature=.1):
    website_searcher_directive = f'''You are information evaluator. You will receive content of commercial website in polish. You need to evaluate whether there is enough information on user webpage to answer following query: <query>{question}</query>. If there is, answer the query directly in polish - please be very succint and just provide answer with no extra sentences. Otherwise, just answer NO'''
    query = [{'user':text, 'system':website_searcher_directive}]
    return asyncio.run(gather_calls(query, client = client, tempature=temperature, model = model))[0]

def ask_ai_for_opinion_on_links(links, question, model, client, temperature=.1, exclude = None):
    links_c = links.copy()
    if exclude is not None:
        links_c = [link for link in links_c if link['href'] not in exclude]
        if len(links_c) == 0:
            return "ALL_SCANNED"
    ref_list = []
    for link in links_c:
        for link_key in link.keys():
            if link[link_key] is None:
                link[link_key] = 'N/A'
        link_str = ', '.join([x + " : " + link[x] for x in link.keys() if link.keys() if x in ['href','text','title'] ])
        ref_list.append(link_str)
    
    website_searcher_directive = f'''You are information evaluator. You will receive links on commercial website in polish, with metadata as follows:
                 'href' ,'text' 'title'
                 Links will be provided in form of python list.
    Based on that, you need to evaluate which link is in your view the most likely to contain information to answer following query: <query>{question}</query>. Return ONLY the direct url (href) of most likely link. Do not return anything else.  '''

    query = [{'user':str(ref_list), 'system':website_searcher_directive}]
    return asyncio.run(gather_calls(query, client = client, tempature=temperature, model = model))[0]

def ponder_website(question, url, q_evaluated_pages:dict, scanned_websites = [], query_counter = 0, query_limit = None, domain_url = None):
    website_content = just_text(url)
    
    if query_limit is not None:
        if query_counter >= query_limit:
            raise Exception("Dramat")

    if url in q_evaluated_pages.keys():
        opinion = 'NO'
        ic(f'Already evaluated page {url}')
    else:
        opinion = ask_ai_for_opinion_on_content(website_content, question, model=model, client=client)
        query_counter+=1

    if opinion != 'NO':
        q_evaluated_pages[url] = 'OK'
        ic(f"Found answer to {question} on {url}!")
        return {"status":"DONE","answer":opinion}
    else:
        q_evaluated_pages[url] = 'NO'
        all_links = get_filtered_links(url,{'selector': 'a', 'exclude_external': False, 'exclude_empty': True, "only_visible" : True, "domain_url": domain_url})

        link_opinion = ask_ai_for_opinion_on_links(all_links, question, model=model, client=client, exclude=scanned_websites)

        if link_opinion in list(q_evaluated_pages.keys()):
            scanned_websites.append(url)

        query_counter+=1

        if link_opinion == "ALL_SCANNED":
            ic("All ideas exhausted on that branch")
            return {"status":"UNFINISHED", "answer": "NA"}
        
        ic(f"Did not find answer to {question} on {url}, next try on {link_opinion}!")

        return ponder_website(question, link_opinion, q_evaluated_pages, scanned_websites = scanned_websites, query_counter = query_counter, query_limit = query_limit, domain_url=domain_url)

def execute_task_4_3(session, client
                     , ai_devs_key
                     , task_name:str
                     , model:str
                     , data_source_url:str= ''
                     , question_source:str = ''
                     , endpoint_url:str='') -> None:

    questions = json.loads(download_data(question_source).decode())
 
    final_answers = dict()

    for nq, q in enumerate(questions.keys(),1):

        question = questions[q]
        print(f'Evaluate question {nq}: {question}')

        q_evaluated_pages = dict()
        query_limit = 20

        this_answer = ponder_website(question, data_source_url, q_evaluated_pages, scanned_websites = [], query_limit = query_limit, domain_url = data_source_url)
        ic(this_answer)
        final_answers[q] = this_answer["answer"]

    ic(final_answers)
        
    json_apt_format = {
        "task": task_name,
        "apikey": ai_devs_key,
        "answer": final_answers      
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

    task_4_3_data_source = json_secrets["task_4_3_data_source"]
    task_4_3_question_source = json_secrets["task_4_3_question_source"].replace('TUTAJ-KLUCZ',ai_devs_key)
    ic(task_4_3_question_source)
    task_4_3_endpoint_url = json_secrets["task_4_3_endpoint_url"]

    session = requests.Session()

    
    if 'claude' in model:
        client = Anthropic(api_key=anthropic_api_key)
    if 'gpt' in model:
        client = OpenAI(api_key=open_ai_api_key)
    if model == '_local_model_':
        client = OpenAI(base_url="http://127.0.0.1:1234/v1/",api_key='local')

    
    execute_task_4_3(session, client, ai_devs_key
                     , task_name = 'softo'
                     , model = model
                     , data_source_url = task_4_3_data_source
                     , question_source = task_4_3_question_source
                     , endpoint_url = task_4_3_endpoint_url)

    