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
    
def execute_task_3_2(session, client, rag
                     , ai_devs_key:str 
                     , task_name:str = ''
                     , data_source_url:str= ''
                     , endpoint_url:str=''
                     , use_embedding:bool = True
                     , embedding_k:int = 15
                     , searched_content:str = ''
                     , end_query:str = '') -> None:

    l_o_p = [x for x in for_every_file_in_gen(local_folder,recursive=True, supported_formats = ('txt'), include_no_extension = False)]

    texts = rag.load_documents(l_o_p)
    rag.create_vector_store(texts, persist_directory=None)
    ic(rag.get_document_count())
    
    l_o_t_sim_score_to_query = rag.vector_store.similarity_search_with_score(searched_content, k=embedding_k)


    ic(l_o_t_sim_score_to_query[0][0].page_content)
    ic(l_o_t_sim_score_to_query[0][0].metadata['source'])
    
    query = [{'user':f'''<Metadata> TITLE: {l_o_t_sim_score_to_query[0][0].metadata['source']}  </metadata> <content> {l_o_t_sim_score_to_query[0][0].page_content} </content>''', 'system':end_query}]
    my_answers = asyncio.run(gather_calls(query, client = client, tempature=.2, model = model))
    ic(my_answers[0])

    json_apt_format = {
        "task": task_name,
        "apikey": ai_devs_key,
        "answer": my_answers[0]
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

    local_folder = r'''C:\Projects\AI_DEVS_3\s_3_02_files\weapons_test\do-not-share'''
    json_secrets = load_from_json(filepath=rf'{os.path.dirname(__file__)}\config.json')

    open_ai_api_key = json_secrets["open_ai_api_key"]
    anthropic_api_key = json_secrets["anthropic_api_key"]
    ai_devs_key = json_secrets["api_key"]
    model = "gpt-4o-mini"
    rag = RAGSystem(open_ai_api_key, chunk_size = 5000, chunk_overlap =0)


    task_3_2_data_source = json_secrets["task_3_2_data_source"]
    task_3_2_endpoint_url = json_secrets["task_3_2_endpoint_url"]

    session = requests.Session()
    
    if 'claude' in model:
        client = Anthropic(api_key=anthropic_api_key)
    if 'gpt' in model:
        client = OpenAI(api_key=open_ai_api_key)
    if model == '_local_model_':
        client = OpenAI(base_url="http://127.0.0.1:1234/v1/",api_key='local')


    searched_content = '''W raporcie, z którego dnia znajduje się wzmianka o kradzieży prototypu broni?'''
    
    end_query = '''Using data given in user query, including metadata, can you reply what date was the document from? Date is in the title, ignore dates mentioned in body of document. Do reply in YYYY-MM-DD format, and reply only with the date.'''

    execute_task_3_2(session, client, rag, ai_devs_key
                     , task_name = 'wektory'
                     , data_source_url = task_3_2_data_source
                     , endpoint_url = task_3_2_endpoint_url
                     , searched_content = searched_content
                     , end_query = end_query
                     , use_embedding=True
                     , embedding_k = 1)

        # Query with customization
