
def understand_agent(input):
    directive = f'''
    You will receive a log of agentic AI. Try to establish it's goal and tools used within. List all tools, purposes, and api names. Prepare correct examples of api calls in separate section.
    '''

    return {"system": directive, "user": input}


def get_plan(task, tools, tool_context_use):
    directive = f'''
    You have access to several tools that you MUST use to complete tasks:
    - filterer: Use this to remove items from lists. INPUT: list, condition OUTPUT: list without elements with condition. It only works on specific conditions.
    - get_coords: Use this to get coordinates with ids. INPUT: id OUTPUT: coordinates
    - go_through_names_list: Use this to process names, and find names existing in given location OR locations that have given names. It's not useful for filtering observations. INPUT: names of location OUTPUT: people in location OR INPUT: names of people OUTPUT: location with these people 
    - sql_framing: Use this for SQL queries, in particular, getting ids connected to names (usernames). That will require to get both ids and usernames, unique, in one table. This does not have locations!! Use this for SQL queries ONLY for getting people ids connected to people's names (usernames). 
    Always use these tools when relevant instead of describing what you would do. BE SURE TO HIGHLIGHT TO ONLY OUTPUT SQL QUERY AND NO OTHER ADDITIONAL TEXT BEFORE OR AFTER, OR QUERY WILL NOT WORK. INPUT: plain words query OUTPUT: a distinct list of pairs of id and usernames

    <tools>
    {tools}
    </tools>
    First, think which step would be the right one to start with to fulfill the query. Keep in mind we want to have our target included in search results.
    Decide in which order to answer user query, step by step, naming the api. Write out in detail input and output you will have. Keep in mind conditions to functions, what key parameters you will have to set, ie. people or places in go_through_name_list !!!
    You will have to use ALL the tools. Be sure to enumerate it (first task starts with 1., second with 2. etc.)

    Use only one step for one purpose - ie. if you filter out something in one step, do not filter it in another. Instructions will be executed in chain and thus it's redundant. 

    REMEMBER OUTPUT HAS TO HAVE NAME AND ID, SO MAINTAINING NAME IS IMPERATIVE
    '''
    # print({"system": directive, "user": task})
    return {"system": directive, "user": task}


def put_plan_to_tools(task, tools):
    directive = f'''
    You have access to several tools that you MUST use to complete tasks:
    - filterer: Use this to remove items from lists
    - get_coords: Use this to get coordinates with ids
    - go_through_names_list: Use this to process names
    - sql_framing: Use this for SQL queries, in particular, getting people ids connected to people's names (usernames)

    Always use these tools when relevant instead of describing what you would do.

    <tools>
    {tools}
    </tools>

    User message will create a process you have to put into functions, step by step, matching the api. List APIs in order matching You will have to use ALL the tools. 
    '''
    # print({"system": directive, "user": task})
    return {"system": directive, "user": task}

def tool_guesser(task):
    directive = f'''
    From recommendation, get which tool is it that you are supposed to use from this closed list 
     [filterer, get_coords, go_through_names_list, sql_framing]. Tool IS MENTIONED BY USER. PICK THAT ONE
    '''
    # print({"system": directive, "user": task})
    return {"system": directive, "user": task}


def put_step_to_tool(task, tools, specific_tool):
    directive = f'''
    You have access to only one tool! {specific_tool}
 
    User message will require matching one of above functions. 
    See below overview of tools for reference on how you will use it, of which you are only allowed to use {specific_tool}

    <tools>
    {tools}
    </tools>
    '''
    # print({"system": directive, "user": task})
    return {"system": directive, "user": task}




    # and example of logs
    # <tools_example>
    # {tool_context_use}
    # </tools_example>, especially example selection write out which tools should be used,



def get_api_url(input, example_of_other_urls):
    directive = f'''
    You will receive a log of agentic AI. Return only url that is used to receive coordinates. Return nothing but url. If it is a relative url, find base for absolute url in body of text and concatenate them.
    There are examples of other urls used for api this application:
    {','.join(example_of_other_urls)}
    And this one should have similar structure.
    '''
    return {"system": directive, "user": input}

def get_tool_plan(plan):
    '''Consider plan from this '''
def write_code(summary):
    directive = f'''
    For all instructions, 
    '''