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
    
def execute_task_3_1(session, client, rag
                     , ai_devs_key:str 
                     , task_name:str = ''
                     , data_source_url:str= ''
                     , endpoint_url:str=''
                     , use_embedding:bool = True
                     , embedding_k:int = 15
                     , directive = '') -> None:

    l_o_p = [x for x in for_every_file_in_gen(local_folder,recursive=True, supported_formats = ('txt'), include_no_extension = False)]
    # and assuming no extension file is excluded as well
    l_o_t = [l for l in l_o_p if r'\facts' not in l]
    
    if use_embedding:
        texts = rag.load_documents(l_o_p)
        rag.create_vector_store(texts, persist_directory=None)
        ic(rag.get_document_count())
    

    # ic(l_o_p)
    whole_corpus = dict()
    target_content = dict()
    l_o_t_sim_scores = dict()

    for term in l_o_p:
        with open(term, 'r', encoding='utf-8') as file:
            content = file.read()
            whole_corpus[term] = "TITLE: \n" + os.path.basename(term) + "\n" + content
            # whole_corpus[term] = "TITLE: \n" + term + "\n" + content
            if term in l_o_t:
                target_content[term] = content
    if use_embedding:
        for target in target_content.keys(): # for every file in base, getting similarity to every target file
            l_o_t_sim_scores[target] = rag.vector_store.similarity_search_with_score(target_content[target], k=embedding_k)

    # for n in whole_corpus.keys():
    #     ic(whole_corpus[n])


    # calling..
    if not (use_embedding):
        directive_w_corpus = directive.replace('{DOCUMENT}',' --- '.join(list(whole_corpus.values())))

    list_of_calls = []
    for single_file in target_content.keys():

        print(f'Considering file: {target_content[single_file][0:250]}..')
        if use_embedding:
            corpus_directive = []
            for doc_c in l_o_t_sim_scores[single_file]:
                corpus_directive.append(doc_c[0].page_content)
            corpus_directive = ["TITLE: \n" + os.path.basename(single_file) + "\n" + x for x in corpus_directive]
            directive_w_corpus = directive.replace('{DOCUMENT}',' --- '.join(corpus_directive))
            print(f'Corpus with current documents included {len(directive_w_corpus)}')

        list_of_calls.append({'user':target_content[single_file], 'system':directive_w_corpus})
        
    my_answers = asyncio.run(gather_calls(list_of_calls,client = client, tempature=.3, model = model))

    map_objects = dict(zip([os.path.basename(p) for p in target_content.keys()], my_answers))


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
    # model = "gpt-4o"
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

                    Keeping above document - including its title, preceding it - as your knowledge, please consider user input and create as many as possible unique single word tags in polish about topic of user input. Do not mention things that are not connected in user input and are present only in your document.
                    EVERYTHING connected to people, locations, objects or events mentioned is required. Sektor from title of document is referring to location - a sector, and should be considered a location to be tagged as well.
                    
                    Names can be considered one common tag. 
                    Whenever recognizing named entity, do your best to include information about this named entity from given knowledge including their role, features and anything connected to other mentions in document you know of.
                    
                    Only reply with list of tags in polish and nothing else. Return in form of list without newlines. 
                    
                    Even seemingly not relevant things like weather conditions, location of discoveries of evidence on scene like fingerprints or blood, animals, specific technologies or colors should be mentioned. 
                    Be sure to mention technologies like ai or specific programming languages, and users of these technologies as in their job profiles, as that's also relevant.

                    <examples>
                    Example 1:
                    Document: "Tesla CEO Elon Musk announced new solar panel factory in Nevada desert. The construction began during sunny weather with temperatures reaching 40°C."
                    User input: "Elon Musk builds solar panels"
                    Tags: "dyrektor, elon musk, tesla, fabryka, nevada, pustynia, słoneczny, panel, budowa, temperatura, upał"
                    Example 2:
                    Document: "Marine biologists discovered new species of blue whale near Antarctica. The whale, spotted during snowfall, was accompanied by a pod of dolphins."
                    User input: "New whale found in Antarctica"
                    Tags: "biolog, morski, wieloryb, gatunek, antarktyda, niebieski, śnieg, delfin, stado"
                    Example 3:
                    Document: "TITLE: sektor_6_polis_report.csv Local police officer Sarah Johnson solved murder case using DNA evidence found by K9 unit dog Max during rainy evening in Central Park."
                    User input: "Officer Johnson solves murder with dog"
                    Tags: "policjantka, sarah johnson, morderstwo, dna, dowód, pies, max, k9, park, deszcz, wieczór, sektor_6"
                    Example 4:
                    Document: "Microsoft's quantum computing team led by Dr. Chen developed new algorithm using experimental hardware and Javascript in their underground laboratory, accidentally discovering quantum tunneling effect during power outage."
                    User input: "Microsoft quantum computing breakthrough"
                    Tags: "microsoft, dr chen, informatyka, kwantowy, algorytm, sprzęt, laboratorium, podziemny, odkrycie, efekt, awaria, Javascript, programista Javascript, programista"
                    Example 5:
                    Document: "Chef Maria Rodriguez won international cooking competition in Paris using traditional Mexican ingredients. Her red chili sauce impressed judges during unusually cold spring evening."
                    User input: "Mexican chef wins in Paris"
                    Tags: "kucharz, maria rodriguez, konkurs, paryż, meksykański, składniki, sos, chili, czerwony, sędzia, wiosna, zimno"
                    Example 6:
                    Document: "Archeologist team found ancient Roman artifacts buried under medieval church ruins. Discovery made by ground-penetrating radar during autumn excavation, while local cats watched from nearby trees."
                    User input: "Roman artifacts found under church"
                    Tags: "archeolog, rzym, artefakt, kościół, ruiny, średniowieczny, radar, wykop, jesień, kot, drzewo"
                    Example 7:
                    Document: "TITLE: sektor_3_xdxd.csv SpaceX Starship prototype SN15 successfully landed after test flight in foggy conditions. Bronze-colored rocket used new steel alloy in construction."
                    User input: "Starship lands successfully"
                    Tags: "spacex, starship, sn15, prototyp, lot, test, mgła, brązowy, stal, stop, konstrukcja, sektor_3"
                    Example 8:
                    Document: "Agricultural robot developed by Green Tech startup autonomously harvested strawberries during night using infrared sensors. Solar-powered machine worked through light rain."
                    User input: "Robot harvests strawberries"
                    Tags: "robot, rolnictwo, green tech, truskawka, noc, czujnik, podczerwień, słoneczny, deszcz, autonomiczny"
                    Example 9:
                    Document: "Famous painter Leonardo exhibited new collection in golden-decorated gallery. His cat inspired blue artwork was displayed near vintage wooden sculptures during summer exhibition."
                    User input: "Leonardo's new art exhibition"
                    Tags: "malarz, leonardo, wystawa, galeria, złoty, kot, niebieski, sztuka, rzeźba, drewno, lato"
                    Example 10:
                    Document: "Environmental scientists monitored brown bear population in pine forest using drones. Study conducted during snowy winter revealed increasing numbers near mountain streams."
                    User input: "Bear population study with drones"
                    Tags: "naukowiec, środowisko, niedźwiedź, brązowy, las, sosna, dron, zima, śnieg, góra, strumień"
                    </examples>
                    '''
    
    get_source_data_from_zip(data_source_url=task_3_1_data_source,directory_suffix=local_folder)
    
    execute_task_3_1(session, client, rag, ai_devs_key
                     , task_name = 'dokumenty'
                     , data_source_url = task_3_1_data_source
                     , endpoint_url = task_3_1_endpoint_url
                     , directive = directive
                     , use_embedding=False
                     , embedding_k = 12)

        # Query with customization
