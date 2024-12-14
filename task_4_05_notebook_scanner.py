from openai import OpenAI
from anthropic import Anthropic
import json 
import os
from neo4j import GraphDatabase

import asyncio
import requests
from PIL import Image
from icecream import ic

from api_tasks.basic_poligon_u import load_from_json, post_request, download_data
from api_tasks.get_html_fragment import get_strings_re
from api_tasks.basic_open_ai_calls import gather_calls
from utilities.read_save_text_functions import get_source_data_from_zip
from utilities.generic_utils import for_every_file_in_gen
from api_tasks.website_ai_translation import get_website_and_describe_with_ai
from api_tasks.image_encoding_utilities import convert_local_picture, image_to_bytes
from api_tasks.rag_system_multimodal import RAGSystem
from api_tasks.pdf_solutions import download_pdf, extract_with_pymupdf, extract_pages_as_images, extract_text_from_pdf

from api_tasks.task_4_05_prompts import *

# any way / need to recontextualize with whole document?
## IMPROVEMENT AREAS 

def trier(task_name, ai_devs_key, answers_to_questions, endpoint_url):
    json_apt_format = {
        "task": task_name,
        "apikey": ai_devs_key,
        "answer": answers_to_questions      
    }

    webhook_answer = post_request(endpoint_url, json.dumps(json_apt_format))
    if str(webhook_answer) == '<Response [200]>':
        print(get_strings_re(webhook_answer.content.decode(),pattern=r'{{FLG:(.*?)}}'))
    else:
        ic(webhook_answer)
        ic(webhook_answer.content.decode())

    return json.loads(webhook_answer.content)
    
    
def frustrated_retrier(feedback_received, answers_given_so_far_with_feedbacks,  max_iter):

    pass


def execute_task_4_5(session, client, rag
                     , ai_devs_key
                     , task_name:str
                     , model:str
                     , strong_model:str = None
                     , embedding_k:int = 5
                     , data_source_url:str= ''
                     , question_source:str = ''
                     , endpoint_url:str=''
                     , local_folder:str = "pdf_pages"
                     , temperature = 0.1
                     , reprocess_pdf_to_image = False
                     , use_the_rag = True
                     , use_timeline = True) -> None:



    questions = json.loads(download_data(question_source).decode())
    
    # transcriptions
    # this should maintain order.. Ideally
    text_actual_script = extract_text_from_pdf(data_source_url)
    annotated_actual_script = {i+1: s for i, s in enumerate(text_actual_script)}
    for en, t_key in enumerate(annotated_actual_script.keys()):
        print(f'File {en} {t_key}')


    # vision
    if reprocess_pdf_to_image:
        images = extract_pages_as_images(data_source_url,output_dir=local_folder)
    list_of_images = for_every_file_in_gen(local_folder)

    vision_dict = dict()
    for ky in annotated_actual_script.keys():
        vision_dict[ky] = os.path.join(local_folder,f'page_{ky}.png')

    # get vision descriptors
    vision_ai_call_list = [evaluate_image(vision_dict[x]) for x in vision_dict.keys()]
    vision_model_answers = asyncio.run(gather_calls(vision_ai_call_list,client = client, model = model, tempature=temperature,force_refresh=False))
    # ic(vision_model_answers)

    # merging
    to_merge_ai_call_list = [] 
    for en, t_key in enumerate(annotated_actual_script.keys()):
        to_merge_ai_call_list.append(merge_pages(annotated_actual_script[t_key], vision_model_answers[en]))

    merged_answers = asyncio.run(gather_calls(to_merge_ai_call_list,client = client, model = model, tempature=temperature,force_refresh=False))

    annotated_merged_answers = {i+1: s for i, s in enumerate(merged_answers)}
    document_list = []
    for t_key in annotated_merged_answers.keys():
        # ic(f'{t_key} \n {annotated_merged_answers[t_key]}')


        with open(f'redone_queries/page_merged_vis_{t_key}.txt', 'w' ,encoding='utf-8') as f:
            f.write(annotated_merged_answers[t_key])
        document_list.append(f'redone_queries/page_merged_vis_{t_key}.txt')

    if use_the_rag:
        documents = rag.load_documents(document_list)
        rag.create_vector_store(documents, persist_directory=None)
        ic(rag.get_document_count())


    
    whole_document = '-------------\n'.join([f"PAGE {key}:    {value}" for key, value in annotated_merged_answers.items()])
    if use_timeline:
        timeline_question = establish_timeline_year_claude_version(whole_document)
        timeline_answer = asyncio.run(gather_calls([timeline_question],client = client, model = strong_model, tempature=temperature,force_refresh=False))[0]
        print(f'Timeline: {timeline_answer}')
        with open(f'redone_queries/s_04_05_timeline.txt', 'w' ,encoding='utf-8') as f:
            f.write(timeline_answer)
    # Question breakdown
    answers_to_questions_tt = dict()
    answers_to_questions = dict()
    for nq, q in enumerate(questions.keys(),1):

            

        question = questions[q]
        print(f'Evaluate question {nq}: {question}')    
        input_category = asyncio.run(gather_calls([decide_on_way(question)],client = client, model = model, tempature=temperature,force_refresh=False))[0]
        ic(f'Question {question} category {input_category}')

        # decide-rags
        if use_the_rag:
            l_o_t_sim_score_to_query = rag.vector_store.similarity_search_with_score(question, k=embedding_k)
            context_list = '-------------\n'.join(['PAGE ' + x[0].metadata['source'] + ":      " + x[0].page_content for x in l_o_t_sim_score_to_query])
        else:
            context_list = '-------------\n'.join([f"PAGE {key}:    {value}" for key, value in annotated_merged_answers.items()])
        
        if use_the_rag:
            print(f"Documents for question {question}")
            print("\n")
            print("----------------")
            print("\n")
            print(context_list)

        if use_timeline:

            # context_list = context_list + '-------------\n TIMELINE:' + timeline_answer
            if input_category == 'YEAR':
                context_list = 'TIMELINE:' + timeline_answer

        q_thoughts = think_it_through(context_list, question)
        q_thoughts_answer = asyncio.run(gather_calls([q_thoughts],client = client, model = strong_model, tempature=temperature,force_refresh=False))
        answers_to_questions_tt[q] = q_thoughts_answer

        q_best_guesses = extract_best_guesses(q_thoughts_answer[0], question)
        q_best_guesses_answer = asyncio.run(gather_calls([q_best_guesses],client = client, model = strong_model, tempature=temperature,force_refresh=False))
        answers_to_questions[q] = q_best_guesses_answer[0]



    for en, t_key in enumerate(answers_to_questions_tt.keys()):
        print(f'Question extended {en} {t_key}: {answers_to_questions_tt[t_key]}')

    for en, t_key in enumerate(answers_to_questions.keys()):
        print(f'Question {en} {t_key}: {answers_to_questions[t_key]}')




    # for pn, page in enumerate(text_actual_script):
    #     ic(f'page {pn} : {page}')
    # ic(questions)
    # final_answers = dict()

    # queries = []
    # context = '\n'.join(text_actual_script)
    
    # test = evaluate_image(os.path.join(local_folder,'page_19.png'))
    # img_descr = asyncio.run(gather_calls([test], client = client, model = model, tempature=temperature, model = model))
    # print(img_descr)

    # questions = {'q1':'Rafał opisuje swój ruch po śniegu, tworząc znak krzyża swoimi śladami - o jakim miejscu może teraz myśleć? Czy masz pomysł na jakieś fizyczne miejsce w okolicach Grudziądza?'}




    # for nq, q in enumerate(questions.keys(),1):
    #     print(q)
    #     queries.append({"system": f''' You are a information extraction engine. Considering following document <document> {context} </document> try to elaborate and answer user question, consider different possibilities. Question will be in polish and you should also answer in polish''', "user": questions[q]})
    
    # scanner_answers = asyncio.run(gather_calls(queries, client = client, model = model, tempature=temperature, model = model))
    # ic(scanner_answers)


    status = trier(task_name, ai_devs_key, answers_to_questions, endpoint_url)
    print(status["code"])
    print(status["message"])

    iteration = 0
    max_iterations = 76

    while True:
        if int(status["code"]) != 200 and iteration < max_iterations:
            iteration = iteration + 1
            print(f'---------------------ITERATION {iteration} --------------------')
            
            
            cong_feedback = f'''
            *** WARNING: To the same question, answer was validated before as incorect. ***
            Incorrect answer provided: "{status["debug"]} " was not correct : {status['message']}. 
            Please resolve it with a different answer. HINT: {status["hint"]} 
            '''
            # Wskazówka: {status["hint"]} 

            cong_feedback = f''' 
            *** OSTRZEŻENIE - na to samo pytanie, odpowiedź jest już uznana za nieprawidłową *** 
            Nieprawidłowa odpowiedź: "{status["debug"].split(':')[1:]} " nie była poprawna. 
            Użyj innej odpowiedzi niż "{status["debug"].split(':')[1:]} " !!! Weź pod uwagę różne możliwości.
            Wskazówka: {status["hint"]} 
            '''
            
            print(cong_feedback) 
            q = status["message"].split(' ')[3]
            
            ic(questions[q])

            answers_to_questions_tt[q][0] =  answers_to_questions_tt[q][0] + cong_feedback
            ic(answers_to_questions_tt[q])
            q_best_guesses = extract_best_guesses(answers_to_questions_tt[q][0], questions[q])

            q_best_guesses_answer = asyncio.run(gather_calls([q_best_guesses],client = client, model = strong_model, tempature=temperature,force_refresh=False))
            answers_to_questions[q] = q_best_guesses_answer[0]
            with open(f'redone_queries/s_04_05_answer_{q}_{iteration}.txt', 'w' ,encoding='utf-8') as f:
                f.write(q_best_guesses_answer[0])
            with open(f'redone_queries/s_04_05_question_{q}_{iteration}.txt', 'w' ,encoding='utf-8') as f:
                f.write(q_best_guesses["user"])
            with open(f'redone_queries/s_04_05_input_{q}_{iteration}.txt', 'w' ,encoding='utf-8') as f:
                # f.write(q_best_guesses["user"]) # user to pytanie 
                f.write(q_best_guesses["system"])
            status = trier(task_name, ai_devs_key, answers_to_questions, endpoint_url)
        else:
            break


    # new query - answer above, and try again with cong_feedback.

    # json_apt_format = {
    #     "task": task_name,
    #     "apikey": ai_devs_key,
    #     "answer": answers_to_questions      
    # }

    # webhook_answer = post_request(endpoint_url, json.dumps(json_apt_format))
    # if str(webhook_answer) == '<Response [200]>':
    #     print(get_strings_re(webhook_answer.content.decode(),pattern=r'{{FLG:(.*?)}}'))
    # else:
    #     ic(webhook_answer)
    #     ic(webhook_answer.content.decode())

if __name__ == "__main__":
    local_model = False 

    json_secrets = load_from_json(filepath=rf'{os.path.dirname(__file__)}\config.json')
    open_ai_api_key = json_secrets["open_ai_api_key"]
    anthropic_api_key = json_secrets["anthropic_api_key"]
    ai_devs_key = json_secrets["api_key"]
    model = "gpt-4o-mini"
    strong_model = "gpt-4o-mini"

    # model = "claude-3-5-sonnet-20241022"
    
    task_4_5_data_source = json_secrets["task_4_5_data_source"]
    task_4_5_question_source = json_secrets["task_4_5_question_source"].replace('TUTAJ-KLUCZ',ai_devs_key)
    task_4_5_endpoint_url = json_secrets["task_4_5_endpoint_url"]
 
    rag = RAGSystem(open_ai_api_key, chunk_size = 5000, chunk_overlap =0)

    session = requests.Session()

    
    if 'claude' in model:
        client = Anthropic(api_key=anthropic_api_key)
    if 'gpt' in model:
        client = OpenAI(api_key=open_ai_api_key)
    if model == '_local_model_':
        client = OpenAI(base_url="http://127.0.0.1:1234/v1/",api_key='local')

    

    # rag_sizes = [3,5,7,9]
    # for rag_size in rag_sizes:
    execute_task_4_5(session, client, rag, ai_devs_key
                    , task_name = 'notes'
                    , model = model
                    , strong_model = strong_model
                    , data_source_url = task_4_5_data_source
                    , question_source = task_4_5_question_source
                    , endpoint_url = task_4_5_endpoint_url
                    , embedding_k = 6
                    , use_the_rag=False
                    , temperature = 0.5
                    ,use_timeline = True
                    )
    


    # k_5 works except for first question..

    # 2.15 before running huh
    # odwołania do wydarzen - seperate history/timeline context??