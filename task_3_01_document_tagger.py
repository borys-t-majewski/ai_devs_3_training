from openai import OpenAI
from anthropic import Anthropic
import json 
import os

import asyncio
import requests
from PIL import Image
from icecream import ic

from api_tasks.basic_poligon_u import load_from_json, post_request
from api_tasks.get_html_fragment import get_strings_re
from api_tasks.basic_open_ai_calls import gather_calls
from api_tasks.whisper_interactions import create_transcripts_from_audio
from utilities.read_save_text_functions import get_source_data_from_zip
from utilities.generic_utils import for_every_file_in_gen
from api_tasks.image_encoding_utilities import image_to_bytes
from api_tasks.rag_system_multimodal import RAGSystem


## IMPROVEMENT AREAS 

def task_splitter(file_path,extension_dictionary = {'txt':'text','png':'vision','mp3':'audio'},no_expansion_dict = 'text'):
    import os
    extension = os.path.splitext(file_path)
    if len(extension[1])==0:
        return no_expansion_dict
    else:
        return extension_dictionary[extension[1].replace('.','')]
    
def execute_task_3_1(session, client, rag, ai_devs_key:str ,task_name:str = '', data_source_url:str= '', endpoint_url:str='', directive = '') -> None:

    l_o_p = [x for x in for_every_file_in_gen(local_folder,recursive=True, supported_formats = ('txt'), include_no_extension = False)]
    # and assuming no extension file is excluded as well

    l_o_t = [l for l in l_o_p if r'\facts' not in l]
    
    
    texts = rag.load_documents(l_o_p)
   
    print('a')
    rag.create_vector_store(texts, persist_directory=None)
    print('b')
    ic(rag.get_document_count())
    

    


    # ic(l_o_p)
    whole_corpus = dict()
    target_content = dict()
    l_o_t_sim_scores = dict()

    # target_corpus_list = []

                # ic(f"l_o_t_sim_scores[{target}] = rag.vector_store.similarity_search_with_score({content}, k=10)")
  
    for term in l_o_p:
        with open(term, 'r', encoding='utf-8') as file:
            content = file.read()
            whole_corpus[term] = content
            if term in l_o_t:
                target_content[term] = content

    
    # l_o_t_sim_scores[term] = {}

    for target in target_content.keys(): # for every file in base, getting similarity to every target file
        l_o_t_sim_scores[target] = rag.vector_store.similarity_search_with_score(target_content[target], k=10)


    print('c')
    # ic(l_o_t_sim_scores)

    # ic(l_o_t_sim_scores[l_o_p[0]])
    ic(l_o_t_sim_scores[l_o_t[0]])
    ic(l_o_t_sim_scores[l_o_t[0]][0:3])

    # async def .............



    rest = False
    if rest:
        # directive_w_corpus = directive.replace('{DOCUMENT}',' --- '.join(whole_corpus))
        directive_w_corpus = directive.replace('{DOCUMENT}',' --- '.join(list(whole_corpus.values)))


        # calling..
        list_of_calls = []
        # for single_file in target_corpus_list:
        for single_file in target_content.keys():
            print(f'Considering file: {target_content[single_file][0:250]}..')
            list_of_calls.append({'user':target_content[single_file], 'system':directive_w_corpus})

        my_answers = asyncio.run(gather_calls(list_of_calls,client = client, tempature=.3, model = model))

        
        map_objects = dict(zip([os.path.basename(p) for p in target_content.keys()], my_answers))
        # ic(map_objects)
        ic(type(map_objects))
        for k in map_objects.keys():
            ic(k)
            ic(map_objects[k])

        json_apt_format = {
            "task": task_name,
            "apikey": ai_devs_key,
            "answer": map_objects
        }


        webhook_answer = post_request(endpoint_url, json.dumps(json_apt_format))
        if str(webhook_answer) == '<Response [200]>':
            print(get_strings_re(webhook_answer.content.decode(),pattern=r'{{FLG:(.*?)}}'))
        else:
            ic(webhook_answer)
            ic(webhook_answer.content.decode())

if __name__ == "__main__":
    local_model = False 
    # (only argument for completion, not for whisper call)

    local_folder = r'''C:\Projects\AI_DEVS_3\s_3_01_files'''
    json_secrets = load_from_json(filepath=rf'{os.path.dirname(__file__)}\config.json')

    open_ai_api_key = json_secrets["open_ai_api_key"]
    anthropic_api_key = json_secrets["anthropic_api_key"]
    ai_devs_key = json_secrets["api_key"]
    model = "gpt-4o-mini"
    rag = RAGSystem(open_ai_api_key, chunk_size = 5000, chunk_overlap =0)


    task_3_1_data_source = json_secrets["task_3_1_data_source"]
    task_3_1_endpoint_url = json_secrets["task_3_1_endpoint_url"]

    session = requests.Session()
    
    if 'claude' in model:
        client = Anthropic(api_key=anthropic_api_key)
    if 'gpt' in model:
        client = OpenAI(api_key=open_ai_api_key)
    if model == '_local_model_':
        client = OpenAI(base_url="http://127.0.0.1:1234/v1/",api_key='local')


    directive = '''
                    <document>
                    {DOCUMENT}
                    </document>

                    Keeping above document as your knowledge, please consider user input and create as many as possible unique single word tags in polish about topic of user input. Do not mention things that are not connected in user input and are present only in your document.
    
                    Names can be considered one common tag. 
                    Whenever recognizing named entity, do your best to include information about this named entity from given knowledge including their role, features and anything connected to other mentions in document you know of.
                    
                    Only reply with list of tags in polish and nothing else. Return in form of list without newlines.

                    <examples>
                    For document: "Donald Trump, president of USA, funds AI research as part of government initiatives. In other news, grass still green."
                    And user input: "Donald Trump spends 20 billion on AI"
                    return
                    "prezydent, donald trump, usa, badania, rząd, si, inicjatywa, money"

                    </examples>
                    '''
    
    get_source_data_from_zip(data_source_url=task_3_1_data_source,directory_suffix=local_folder)
    
    execute_task_3_1(session, client, rag, ai_devs_key, task_name = 'dokumenty', data_source_url = task_3_1_data_source, endpoint_url = task_3_1_endpoint_url, directive = directive)

        # Query with customization
