from openai import OpenAI
import json 
import os
from api_tasks.basic_poligon import load_from_json


json_secrets = load_from_json(filepath=rf'{os.path.dirname(__file__)}\config.json')
api_key = json_secrets["open_ai_api_key"]

client = OpenAI(
    api_key=api_key
)

chat_completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Can you tell me a joke?"}
             ,{"role": "system", "content": "Reply in English only."}
             ,{"role": "assistant", "content": "You're helpful and over-enthusiastic assistant. Anything requested, try to do at least 2 times."}
             ]
)

print(chat_completion.choices[0].message.content)
# print(chat_completion.usage)
# print(chat_completion.usage)