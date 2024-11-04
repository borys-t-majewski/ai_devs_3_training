from openai import OpenAI
import json 
import os
from api_tasks.basic_poligon import load_from_json
import asyncio

json_secrets = load_from_json(filepath=rf'{os.path.dirname(__file__)}\config.json')
api_key = json_secrets["open_ai_api_key"]

model = "gpt-4o-mini"

client = OpenAI(
    api_key=api_key
)

async def opai_call(user_message="Tell me anything", system_message="You're a helpful assistant. Reply briefly.", assistant_message="You're helpful and over-enthusiastic assistant."):
    chat_completion = client.chat.completions.create(
        model=model,
        messages=[
                 {"role":"user", "content": user_message}
                ,{"role": "system", "content": system_message}
                ,{"role": "assistant", "content": assistant_message}
                ]
    )
    return chat_completion.choices[0].message.content

async def gather_calls(list_of_calls):
    # Run multiple fetches concurrently
    calls = [opai_call(**{k+'_message':v for k,v in lx.items() if v is not None}) for lx in list_of_calls]
    results = await asyncio.gather(*calls)
    print(results) 

list_of_queries = [
      {'user':'What is the capital of Poland?','system':'Reply only in lowercase.'}
    , {'user':'What is the capital of France?','system':'Reply only in uppercase and elaborate on the topic.'}
    , {'user':'What is the capital of Germany?'}]

asyncio.run(gather_calls(list_of_queries))

