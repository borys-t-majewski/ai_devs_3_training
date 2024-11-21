from openai import OpenAI
from anthropic import Anthropic
import json 
import os

from icecream import ic 

import asyncio
import requests


from api_tasks.get_html_fragment import get_strings_re
from api_tasks.basic_poligon_u import load_from_json, post_request
from api_tasks.basic_open_ai_calls import gather_calls
from api_tasks.whisper_interactions import create_transcripts_from_audio
from utilities.read_save_text_functions import get_source_data_from_zip
from utilities.generic_utils import for_every_file_in_gen
from utilities.html_splitter import parse_html_elements
from api_tasks.image_encoding_utilities import image_to_bytes
from api_tasks.website_interactions import download_webpage, download_and_chunk_webpage, sanitize_filename
from api_tasks.url_resolver import resolve_urls, normalize_download_links
from PIL import Image
from pyquery import PyQuery

## IMPROVEMENT AREAS 



def execute_task_2_5(session, client, ai_devs_key:str ,task_name:str = '', data_source_url:str= '', endpoint_url:str='', local_folder:str = '') -> None:
    

    def get_website_and_describe_with_ai(client, data_source_url:str = '', local_folder:str = '')-> list[str]:
        import re 
        import io 
        import requests
        import tempfile
        from api_tasks.basic_open_ai_calls import gather_calls
        from api_tasks.whisper_interactions import create_transcripts_from_audio
        from utilities.html_splitter import parse_html_elements
        from api_tasks.website_interactions import download_and_chunk_webpage
        from api_tasks.url_resolver import resolve_urls, normalize_download_links
        from pyquery import PyQuery

        output_list = []
        _, chunk_list = download_and_chunk_webpage(data_source_url,output_folder = local_folder)

        for chunk_nr, chunk in enumerate(chunk_list):
            x = PyQuery(normalize_download_links(chunk))
            pattern = r'"([^"]*)"'
            
            img_url = str(x('img'))
            audio_url = str(x('a'))
            img_unprocessed_urls = parse_html_elements(img_url)["images"]
            audio_unprocessed_urls = parse_html_elements(audio_url)["downloads"]

            img_unprocessed_urls = [x.replace(r'"/>',r'">') for x in img_unprocessed_urls if len(x) > 0] 
            audio_unprocessed_urls = [x.replace(r'"/>',r'">') for x in audio_unprocessed_urls if len(x) > 0]

            img_url = resolve_urls(data_source_url, img_url)
            audio_url = resolve_urls(data_source_url, audio_url)

            img_list = re.findall(pattern, img_url)
            audio_list = re.findall(pattern, audio_url)

            if len(img_list) > 0:
                pic_questions = []
                for img in img_list:
                    pic_question = {
                    'user':[
                    {'type':'text','text':'Please describe the picture below.'}
                    ,{'type':'image','url':img}
                    ],'system':'Reply briefly but do try to describe all apparent features.'
                    }
                    pic_questions.append(pic_question)

                my_answers = asyncio.run(gather_calls(pic_questions,client = client, tempature=.4, model = model, force_refresh=False))

                for i, img in enumerate(img_unprocessed_urls):
                    chunk = chunk.replace(img, my_answers[i])
            
            if len(audio_list) > 0:
                audio_questions = []
                for file in [f for f in audio_list if len(f) > 0]:

                    temp_dir = tempfile.gettempdir()
                    temp_path = os.path.join(temp_dir, "temp_audio.mp3")
                    
                    response = requests.get(file, stream=True)
                    response.raise_for_status()  # Raises an HTTPError if the status is 4xx, 5xx
                    
                    # Save to temporary file
                    with open(temp_path, 'wb') as f:
                        for sub_file in response.iter_content(chunk_size=8192):
                            if sub_file:
                                f.write(sub_file)

                    create_transcripts_from_audio(client, transcript_suffix = '_transcript', local_folder=temp_dir)
                    print(temp_dir)
                    with open(os.path.join(temp_dir,'transcripts','temp_audio_transcript.txt'), encoding='utf-8') as f:
                        transcript = f.read()

                    audio_questions.append(transcript)
                for s, script in enumerate(audio_unprocessed_urls):

                    chunk = chunk.replace(script.replace('''download="">''','''download>'''), audio_questions[s])


            ic(f'''
            Images processed {img_unprocessed_urls}
            Files processed {audio_unprocessed_urls}
            ''')
            outcome = PyQuery(chunk).text()
            ic(outcome)
            output_list.append(outcome)

        return output_list
    output_list = get_website_and_describe_with_ai(client, data_source_url = data_source_url, local_folder = local_folder)
        

        

        



    # for each chunk:
    #     check if they have links to images or audio
    #     if they do, add short description of images / transcription as replacement for links
    #     would be nice to have it be a generic function that reads in text html and returns text html with realize links for the future
            # extract unique links 
            # describe'em 
            # substitute them in text reprsentation with some tags like [IMAGE] [/IMAGE] - not to confuse with html tags ideally, although they should be cleaned already/
    # add pyquery(htmlstring).text() to convert to raw text after we get rid of html tags

    # then add all of them to rag? without rag we'll have to actually have some kind of loop by questions, to see if it's answered - make model say if there's no info
    # for each page:
        # for each question:
    # would be nicer if it was a rag though




    # json_apt_format = {
    #     "task": task_name,
    #     "apikey": ai_devs_key,
    #     "answer": final_answer
    # }
    # print(json.dumps(json_apt_format))

    # webhook_answer = post_request(endpoint_url, json.dumps(json_apt_format))
    # if str(webhook_answer) == '<Response [200]>':
    #     print(get_strings_re(webhook_answer.content.decode(),pattern=r'{{FLG:(.*?)}}'))
    # else:
    #     print(webhook_answer)

    #     print(webhook_answer.content)

if __name__ == "__main__":
    local_model = False 
    # (only argument for completion, not for whisper call)

    local_folder = r'''C:\Projects\AI_DEVS_3\s_2_05_website'''
    json_secrets = load_from_json(filepath=rf'{os.path.dirname(__file__)}\config.json')

    open_ai_api_key = json_secrets["open_ai_api_key"]
    anthropic_api_key = json_secrets["anthropic_api_key"]
    ai_devs_key = json_secrets["api_key"]
    data_source = json_secrets["task_2_5_data_source"]
    questions = json_secrets["task_2_5_questions"].replace('KLUCZ-API',ai_devs_key)
    endpoint_url = json_secrets["task_2_5_endpoint_url"]
    
    model = "gpt-4o-mini"
    task_name = 'arxiv'
    session = requests.Session()
    
    if 'claude' in model:
        client = Anthropic(api_key=anthropic_api_key)
    if 'gpt' in model:
        client = OpenAI(api_key=open_ai_api_key)
    if model == '_local_model_':
        client = OpenAI(base_url="http://127.0.0.1:1234/v1/",api_key='local')

    execute_task_2_5(session, client, ai_devs_key = ai_devs_key ,task_name = task_name, data_source_url = data_source, endpoint_url = endpoint_url, local_folder = local_folder)



    