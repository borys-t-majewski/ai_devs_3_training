from openai import OpenAI
import json 
import os

import asyncio



async def opai_call(user_message="Tell me anything", system_message="You're a helpful assistant. Reply briefly.", assistant_message="You're helpful and over-enthusiastic assistant.", model = "gpt-4o-mini", client = None):
    chat_completion = client.chat.completions.create(
        model=model,
        messages=[
                 {"role":"user", "content": user_message}
                ,{"role": "system", "content": system_message}
                ,{"role": "assistant", "content": assistant_message}
                ]
    )
    return chat_completion.choices[0].message.content

async def gather_calls(list_of_calls, client = None, model = "gpt-4o-mini"):
    # Run multiple fetches concurrently
    calls = [opai_call(**{k+'_message':v for k,v in lx.items() if v is not None}, client = client, model = model) for lx in list_of_calls]
    results = await asyncio.gather(*calls)
    return results


if __name__ == "__main__":
    from basic_poligon_u import load_from_json

    json_secrets = load_from_json(filepath=rf'{os.path.dirname(__file__)}\..\config.json')
    api_key = json_secrets["open_ai_api_key"]
    client = OpenAI(
        api_key=api_key
    )


    list_of_queries = [
      {'user':'What is the capital of Poland?','system':'Reply only in lowercase.'}
    , {'user':'What is the capital of France?','system':'Reply only in uppercase and elaborate on the topic.'}
    , {'user':'What is the capital of Germany?'}
    
    ]

    print(asyncio.run(gather_calls(list_of_queries,client = client)))

