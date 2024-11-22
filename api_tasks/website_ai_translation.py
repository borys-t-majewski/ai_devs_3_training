
def get_website_and_describe_with_ai(client, model:str = '', data_source_url:str = '', local_folder:str = '')-> list[str]:
    import re 
    import io 
    import os
    import asyncio
    from icecream import ic 
    
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
                {'type':'text','text':'Please describe the picture below, including location if possible.'}
                ,{'type':'image','url':img}
                ],'system':'Reply briefly but do try to describe all apparent features. If it is possible to determine location, include it in your description.'
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