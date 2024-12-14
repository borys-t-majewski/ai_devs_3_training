from openai import OpenAI
import json 
import os
import io
from base64 import b64encode
import asyncio
from icecream import ic

from api_tasks.image_encoding_utilities import validate_and_convert_image
import time
import functools
from anthropic import RateLimitError, APIError

from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar, Coroutine, Hashable
from datetime import datetime, timedelta
T = TypeVar('T')

def make_hashable(value: Any) -> Hashable:
    """Convert a value into a hashable type for use as a cache key."""
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    elif isinstance(value, (list, set)):
        return tuple(make_hashable(v) for v in value)
    elif isinstance(value, dict):
        return tuple(sorted((k, make_hashable(v)) for k, v in value.items()))
    elif hasattr(value, '__dict__'):
        # For objects, use their id() as a fallback
        return id(value)
    else:
        # For any other types, convert to string representation
        return str(value)

def async_cached_result(
    ttl: Optional[timedelta] = None
) -> Callable:
    def decorator(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., Coroutine[Any, Any, T]]:
        cache: Dict[Hashable, tuple[T, datetime]] = {}
        locks: Dict[Hashable, asyncio.Lock] = {}
        
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Extract force_refresh from kwargs if present
            force_refresh = kwargs.pop('force_refresh', False)
            
            # Convert all arguments to hashable types
            hashable_args = tuple(make_hashable(arg) for arg in args)
            hashable_kwargs = make_hashable(kwargs)
            
            # Create a hashable cache key
            cache_key = (hashable_args, hashable_kwargs)
            
            current_time = datetime.now()
            
            # Create lock if it doesn't exist
            if cache_key not in locks:
                locks[cache_key] = asyncio.Lock()
            
            # Check cache before acquiring lock
            if not force_refresh and cache_key in cache:
                result, timestamp = cache[cache_key]
                if ttl is None or current_time - timestamp < ttl:
                    return result
            
            # Acquire lock to prevent concurrent calculations
            async with locks[cache_key]:
                # Check cache again after acquiring lock
                if not force_refresh and cache_key in cache:
                    result, timestamp = cache[cache_key]
                    if ttl is None or current_time - timestamp < ttl:
                        return result
                
                # Calculate new result and cache it
                result = await func(*args, **kwargs)
                cache[cache_key] = (result, current_time)
                return result
            
        return wrapper
    return decorator

def retry_ai_call(max_retries=3, delay=1, logging=True,fatal=False):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    response = await func(*args, **kwargs)
                    
                    # if not response.content:
                    # if len(response) == 0:
                    # to test if it fully works
                    if response is not None:
                        if logging:
                            print(f"Empty content received on attempt {retries + 1}")
                            print(f"Full response: {response}")
                        retries += 1
                        await asyncio.sleep(delay)
                        continue
                        
                    if logging:
                        if retries>0 and response is not None:
                            print(f"Successful response after {retries} retries")
                    
                    return response

                except RateLimitError as e:
                    if logging:
                        print(f"Rate limit hit on attempt {retries + 1}: {e}")
                    wait_time = delay * (2 ** retries)
                    if logging:
                        print(f"Waiting {wait_time} seconds before retry")
                    await asyncio.sleep(wait_time)
                    retries += 1
                except APIError as e:
                    if logging:
                        print(f"API error on attempt {retries + 1}: {e}")
                    await asyncio.sleep(delay)
                    retries += 1
                except Exception as e:
                    if logging:
                        print(f"Unexpected error: {type(e).__name__}: {e}")
                    raise

            if fatal:
                raise Exception(f"Failed to get valid response after {max_retries} attempts")
            else:
                print(f"Failed to get valid response after {max_retries} attempts")
        return wrapper
    return decorator

@async_cached_result(ttl=timedelta(hours=6))
# @retry_ai_call(max_retries=3, delay=1)
async def opai_call(user_message="Tell me anything"
                    , system_message="You're a helpful assistant. Reply briefly."
                    , assistant_message="You're helpful assistant."
                    , tools = None
                    , tool_choice = "auto"
                    , model = "gpt-4o-mini"
                    , client = None
                    , provider:str=''
                    , max_tokens = 4096
                    , temperature = 0.4):
    
    
    """
    Accepts either string, or LIST
      in user message. If more than two arguments, use a dictionary in such format:
    [{type: "text", text:"your actual message"},{type: "image", url: "actual_image_url"}]
    in any order.

    If local image, can apply transform function to get another local image , which is then contributed in 
    # {type: "image_local", local_path: "path 2 image"}
    # If url image, you can download it with x and then apply transfer function and continue as above

    """
    import copy

    if provider == '':
        if "gpt" in model or "local" in model:
            provider = 'openai'
        if "claude" in model:
            provider = 'anthropic'
    
    if tools is None:
        tool_choice = None

    if isinstance(user_message,list):
        user_message_l = copy.deepcopy(user_message)
        for query_part in user_message_l:
            if query_part["type"] == 'image':
                if provider == 'openai':
                    query_part["image_url"] = {}
                    query_part["image_url"]["url"] = query_part["url"]
                    query_part["image_url"]["detail"] = 'high'
                    del query_part["url"]
                    query_part["type"] = "image_url"

                if provider == 'anthropic':
                    query_part["source"] = {}
                    query_part["source"]["type"] = 'base64'
                    # query_part["source"]["media_type"] = 'image/png'
                    query_part["source"]["media_type"] = validate_and_convert_image(query_part["url"])[1]
                    query_part["source"]["data"] = validate_and_convert_image(query_part["url"])[0]
                    del query_part["url"]

        if query_part["type"] == "image_local":
            if provider == 'openai':
                query_part["image_url"] = {}
                query_part["image_url"]["url"] = "data:" + validate_and_convert_image(query_part["local_path"],local_image=True)[1] + f';base64,{validate_and_convert_image(query_part["local_path"],local_image=True)[0]}'
                query_part["image_url"]["detail"] = 'high'
                del query_part["local_path"]
                query_part["type"] = "image_url"
            if provider == 'anthropic':
                query_part["source"] = {}
                query_part["source"]["type"] = 'base64'
                # query_part["source"]["media_type"] = 'image/png'
                query_part["source"]["media_type"] = validate_and_convert_image(query_part["local_path"],local_image=True)[1]
                query_part["source"]["data"] = validate_and_convert_image(query_part["local_path"],local_image=True)[0]
                del query_part["local_path"]
                query_part["type"] = "image"
                
    # Dict passed - adding all this image boilerplate
    if isinstance(user_message,str):
        user_message_l = [{"type": "text","text": user_message}]

    if isinstance(assistant_message,str):
        assistant_message_l = [{"type": "text","text": assistant_message}]

    if isinstance(system_message,str):
        system_message_l = [{"type": "text","text": system_message}]

    if provider == 'openai':
        if tools is None:
            chat_completion = client.chat.completions.create(
                model=model
                ,temperature=temperature
                ,max_tokens = max_tokens
                ,messages=[
                        {"role":"user", "content": user_message_l}
                        ,{"role": "system", "content": system_message_l}
                        ,{"role": "assistant", "content": assistant_message_l}
                        ]
            ).choices[0].message.content

        else:
            chat_completion = client.chat.completions.create(
                model=model
                ,temperature=temperature
                ,max_tokens = max_tokens
                ,messages=[
                        {"role":"user", "content": user_message_l}
                        ,{"role": "system", "content": system_message_l}
                        ,{"role": "assistant", "content": assistant_message_l}
                        ]
                ,tools = tools
                ,tool_choice = tool_choice
            ).choices[0].message


            tool_choice = chat_completion.tool_calls
            # ic(tools)
            # ic(tool_choice)
            # ic(chat_completion)
            # ic(chat_completion)
            # for call in chat_completion:
            #     print(call)

        return chat_completion


    if provider == 'anthropic':
        chat_completion_obj = client.messages.create(
             model=model
            ,max_tokens = max_tokens
            ,temperature = temperature
            ,system = system_message_l
            ,messages=[
                    {"role":"user", "content": user_message_l}
                    ,{"role": "assistant", "content": assistant_message_l}
                    ]
        ).content

        chat_completion = chat_completion_obj.content
        try:
            chat_completion = chat_completion[0].text
        except:
            print('Can not convert')





    return chat_completion


async def gather_calls(list_of_calls, client = None, model = "gpt-4o-mini", tempature: float = 0.4, max_tokens:int = 4096, force_refresh = True, tools = None):
    # Run multiple fetches concurrently
    calls = [opai_call(**{k+'_message':v for k,v in lx.items() if v is not None}, client = client, model = model, temperature=tempature, max_tokens=max_tokens,force_refresh=force_refresh, tools = tools) for lx in list_of_calls]
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

