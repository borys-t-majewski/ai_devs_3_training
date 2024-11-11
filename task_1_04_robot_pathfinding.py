from openai import OpenAI
import json 
import os

import asyncio
import requests
from api_tasks.basic_poligon_u import load_from_json, post_request
from api_tasks.get_html_fragment import get_strings_re
from api_tasks.website_interactions import scrape_site
from api_tasks.basic_open_ai_calls import gather_calls
from utilities.read_save_text_functions import save_text_to_json, read_text_from_json

## IMPROVEMENT AREAS
# Create a version that will use embedding over prompt injection
# Change config to env variable
# Try local model

# Talking here
def communicate_with_bot(session, client, endpoint_url='',extra_bs:str='',system_message = "You're a helpful assistant") -> None:

    respond_with_instructions = [
        {
         'user': extra_bs
        ,'system':system_message
        ,'assistant': ""
        }
        ]
    
    
    return asyncio.run(gather_calls(respond_with_instructions,client = client))[0]


if __name__ == "__main__":
    json_secrets = load_from_json(filepath=rf'{os.path.dirname(__file__)}\config.json')
    open_ai_api_key = json_secrets["open_ai_api_key"]
    instr_url = json_secrets["task_1_2_instr_url"]
    endpoint_url = json_secrets["task_1_2_endpoint_url"]

    session = requests.Session()
    client = OpenAI(api_key=open_ai_api_key)

    
# If you can not make legitimate move, instead of result just communicate "GIVEUP". There is no reason to be in that position if you have legitimate moves that are not repeat to previous position.
    extra_bs = '''
    Consider map:
    <real map> 
    {1,1:S}{1,2:W}{1,3:S}{1,4:S}{1,5:S}{1,6:S}
    {2,1:S}{2,2:S}{2,3:S}{2,4:W}{2,5:S}{2,6:S}
    {3,1:S}{3,2:W}{3,3:S}{3,4:W}{3,5:S}{3,6:S}
    {4,1:R}{4,2:W}{4,3:S}{4,4:S}{4,5:S}{4,6:T}
    </real map>

    <rules>
    Generate following reasoning: from point of the map R, you can exchange positions of R and S or R and T spaces. This is considered onestep. You can only move to adjacent space, so coordinates of R space can only change by 1, and only one element. For example:
    R space on {4,1} can be exchanged with S or T space on {3,1} or {4,2}. That means {3,1} and {4,2} are adjacent.
    R space on {3,3} can be exchanged with S or T space on {3,2} or {2,3} or {3,4} or {4,3}. That means {3,3} and {3,2} are adjacent, and {3,3} and {3,4} are adjacent, and {3,3} and {4,3} are adjacent, and {3,3} and {2,3} are adjacent.

    <logging>
    DOWN - when R is exchanged with S or T above it, ie. {3,5:R} with {4,5:S}. DOWN is when you move R to space with lower first parameter. 
    UP - when R is exchanged with S or T below it, ie. {3,5:R} with {2,5:S}. UP is when you move R to space with higher first parameter. 
    RIGHT - when R is exchanged with S or T left of it, ie. {3,5:R} with {3,6:S}. RIGHT is when you move R to space with higher second parameter. 
    LEFT - when R is exchanged with S or T right of, ie. {3,5:R} with {3,4:S}. LEFT is when you move R to space with lower second parameter. 
    </logging>

    You can never exchange with a W space. Exchange of R with W is illegal.
    Write out every step you are making, without the map.
    In case of a two viable directions, go to one that's closer to T space (minimize sum of differences for their coordinates) that's not a W space.
    
    Finish the procedure after exchanging R space with T space.
    Do not show the map except at the start and finish of the process.

    <onestep> 
    Decide on one of the 4 above that will exchange an R space and adjacent S space or R space and adjacent T space (you CANNOT exchange R and W space), so that we do not get to previous position and possibly minimize distance to T space, and generate a map that will exactly reflect initial map (if it's the first onestep) or created in previous onestep.
    CAREFULLY check if you are not moving into a W space. Reconfirm you are not moving into a W space.
    If you're adjacent to a W space, you need to ignore this direction in a onestep.

    Be sure you aligned the direction of movement with logging section.
    
    </onestep>

    </rules>
    Repeat onestep, until you exchange R space with an adjacent T space. Once you do, share all exchanges you have made in following form:

    <RESULT> { "steps": "list_of_steps" } </RESULT>

    When list_of_steps is comma delimited string made from any number of strings "UP", "RIGHT", "LEFT", "DOWN". 


    '''

    extra_bs_2 = '''
    Consider map:
    <real map> 
    {1,1:S}{1,2:W}{1,3:S}{1,4:S}{1,5:S}{1,6:S}
    {2,1:S}{2,2:S}{2,3:S}{2,4:W}{2,5:S}{2,6:S}
    {3,1:S}{3,2:W}{3,3:S}{3,4:W}{3,5:S}{3,6:S}
    {4,1:R}{4,2:W}{4,3:S}{4,4:S}{4,5:S}{4,6:T}
    </real map>

    <rules>
    Generate following reasoning:
 
    Each block on grid has Y and X parameter delimited by comma, and category. For example, {3,1:S} means Y = 3, X = 1, and category = "S".
    At start of the process, change the map so that parameters of every space with category W is changed to {9,9:W}. 
    Your task is to create iterative steps that will select new spaces that fulfill space condition, in "onesteps"
    
    <conditions>
    From point of the map R, you can move only move to S space or T space. This is considered "onestep". You can only move to adjacent space, so coordinates between initial position and previous position differ by 1 either in Y or X parameter.
    Mark your position with category R, and position that you left with S.
    R space on {4,1} can be moved to S or T space on {3,1} or {4,2}. That means {3,1} and {4,2} are adjacent.
    R space on {3,3} can be moved to S or T space on {3,2} or {2,3} or {3,4} or {4,3}. That means {3,3} and {3,2} are adjacent, and {3,3} and {3,4} are adjacent, and {3,3} and {4,3} are adjacent, and {3,3} and {2,3} are adjacent.
    </conditions>


    You can never step into a W space. Step to W is illegal.
    Write out every step you are making, without the map.

    In case of a two viable directions, go to one that's closer to T space (minimize sum of differences for their coordinates) that's not a W space.
    
    Finish the procedure after reaching T space.
    Do not show the map except at the start and finish of the process.

    <onestep> 
    Decide on one of the 4 below that will move an R space to adjacent S space or adjacent T space (not W space).
    If you're adjacent to a W space, you need to ignore this direction in a onestep.

    Note your movements:
    DOWN - when R is moved to  S or T above it, ie. {3,5:R} with {4,5:S}
    UP - when R is moved to  S or T below it, ie. {3,5:R} with {2,5:S}
    RIGHT - when R is moved to  S or T left of it, ie. {3,5:R} with {3,6:S}
    LEFT - when R is moved to  S or T right of, ie. {3,5:R} with {3,4:S}

    </onestep>

    </rules>
    Repeat onestep, until you exchange R space with an adjacent T space. Once you do, share all exchanges you have made in following form:

    <RESULT> { "steps": "list_of_steps" } </RESULT>

    When list_of_steps is comma delimited string made from any number of strings "UP", "RIGHT", "LEFT", "DOWN". 


    '''

    # answer1 = communicate_with_bot(session, client, endpoint_url=endpoint_url,extra_bs=extra_bs)
    helper1 = communicate_with_bot(session, client, endpoint_url=endpoint_url,extra_bs=extra_bs
                                   ,system_message='''
                                     Instead of answering prompt directly, try to generate best possible prompt that would help LLM accomplish given task.
                                     Create clear instructions, convey all the rules.
                                     Make sure to highlight how to denote movements and what UP, DOWN, LEFT, RIGHT mean in context of difference of paramater values, and that there is no point in going back to already visited space.
                                     Be sure to also convey data for this task.'''
                                     )
    answer2 = communicate_with_bot(session, client, endpoint_url=endpoint_url,extra_bs=helper1)

    # communicate_with_bot(session, client, endpoint_url=endpoint_url,extra_bs=extra_bs_2)
    # print(answer1)
    # print(helper1)

    save_text_to_json(helper1, file_path=rf'''{os.path.dirname(__file__)}\prompts''', file_name = 'helper1_message.json', add_timestamp = False)
    save_text_to_json(answer2, file_path=rf'''{os.path.dirname(__file__)}\prompts''', file_name = 'answer2_message.json', add_timestamp = False)
    
    
    print(answer2)

    # success metrics..
    # find result ("RIGHT, RIGHT, DOWN, DOWN")