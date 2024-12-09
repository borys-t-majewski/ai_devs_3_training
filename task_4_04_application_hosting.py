
# Set up logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    from task_4_04_map_journey import flight_evaluator
    logger.info(f"Successfully imported flight_evaluator: {flight_evaluator}")
except Exception as e:
    logger.error(f"Failed to import flight_evaluator: {str(e)}", exc_info=True)

import subprocess
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from pydantic import BaseModel
import uvicorn
import asyncio
import sys
import datetime
from datetime import datetime, timezone
import json
import os

from logging.handlers import TimedRotatingFileHandler

app = FastAPI()

class DroneInstruction(BaseModel):
    instruction: str

def setup_additional_logging():
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Create a new logger for detailed API monitoring
    api_logger = logging.getLogger('api_monitor')
    api_logger.setLevel(logging.INFO)
    
    # Create handlers with time-based rotation
    # Rotate every minute
    detailed_handler = TimedRotatingFileHandler(
        filename='logs/detailed_api.log',
        when='M',  # M for minutes
        interval=1,  # Rotate every 1 minute
        backupCount=1440,  # Keep 24 hours worth of logs (60 min * 24 hours)
        encoding='utf-8'
    )
    
    # Create error handler with time-based rotation
    error_handler = TimedRotatingFileHandler(
        filename='logs/detailed_errors.log',
        when='M',
        interval=1,
        backupCount=1440,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s\n'
        'Request ID: %(request_id)s\n'
        '-------------------\n'
    )
    
    # Set formatters
    detailed_handler.setFormatter(detailed_formatter)
    error_handler.setFormatter(detailed_formatter)
    
    # Add handlers to logger
    api_logger.addHandler(detailed_handler)
    api_logger.addHandler(error_handler)
    
    return api_logger

# Create the additional logger
api_monitor = setup_additional_logging()

async def detailed_request_logging(request: Request, call_next):
    # Generate unique request ID using datetime
    current_time = datetime.now(timezone.utc)
    request_id = f"{current_time.strftime('%Y%m%d_%H%M%S')}_{id(request)}"
    
    # Create logging context with request ID
    log_context = {'request_id': request_id}
    
    # Log request details
    request_log = f"""
    === Incoming Request ===
    Method: {request.method}
    URL: {request.url}
    Client: {request.client.host}
    Headers: {dict(request.headers)}
    """
    api_monitor.info(request_log, extra=log_context)
    
    # Log request body for POST requests
    if request.method == "POST":
        try:
            body = await request.body()
            api_monitor.info(f"Request Body: {body.decode()}", extra=log_context)
        except Exception as e:
            api_monitor.error(f"Error reading request body: {str(e)}", extra=log_context)
    
    # Process the request and capture response
    try:
        response = await call_next(request)
        
        # Create a copy of response body
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk
        
        # Log response details
        response_log = f"""
        === Outgoing Response ===
        Status: {response.status_code}
        Headers: {dict(response.headers)}
        Body: {response_body.decode()}
        """
        api_monitor.info(response_log, extra=log_context)
        
        # Return a new response with the captured body
        return JSONResponse(
            content=json.loads(response_body),
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    except Exception as e:
        api_monitor.error(
            f"Error processing request: {str(e)}", 
            extra=log_context,
            exc_info=True
        )
        raise
app.middleware("http")(detailed_request_logging)

async def setup_ssh_tunnel():
    logger.info("Attempting to establish SSH tunnel...")

    import os 
    import socket
    import time
    
    async def wait_for_port(port, max_attempts=4, delay=4):
        """Wait for port to become available, return True if successful"""
        for attempt in range(max_attempts):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                if result == 0:
                    logger.info(f"Port {port} is now open (attempt {attempt + 1})")
                    return True
                logger.debug(f"Port {port} not ready yet (attempt {attempt + 1})")
                await asyncio.sleep(delay)
            except Exception as e:
                logger.error(f"Error checking port: {str(e)}")
                sock.close()
        return False

    home = os.path.expanduser("~")
    key_path = os.path.join(home, ".ssh", "my_key")
    
    if not os.path.exists(key_path):
        logger.error(f"SSH key not found at {key_path}")
        return None
    
    # Initial port check
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('', azyl_agent_port))
        logger.info(f"Initial check: Port {azyl_agent_port} is available")
    except socket.error as e:
        logger.error(f"Initial port check failed: {e}")
        return None
    finally:
        sock.close()
        logger.info("Socket closed properly after initial check")

    ssh_command = [
        'ssh',
        '-v',
        '-N',  # Added to prevent executing remote commands
        '-p', '5022',
        '-i', key_path,
        '-o', 'PreferredAuthentications=publickey',
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'ServerAliveInterval=60',  # Keep connection alive
        '-o', 'ServerAliveCountMax=3',
        '-R', f'{azyl_agent_port}:{localhost}:{local_port}',
        f'agent{azyl_agent_id}@azyl.ag3nts.org'
    ]
    
    logger.debug(f"Starting SSH tunnel with command: {' '.join(ssh_command)}")
    
    process = await asyncio.create_subprocess_exec(
        *ssh_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    if not process:
        logger.error("Failed to start SSH process")
        return None

    logger.info(f"SSH process started with PID: {process.pid}")

    # Wait for the tunnel to be established
    # if not await wait_for_port(azyl_agent_port):
    #     logger.error("Tunnel failed to establish in time")
    #     # process.terminate()
    #     await process.wait()
    #     return None

    # Set up output monitoring
    async def read_output(stream, name):
        while True:
            line = await stream.readline()
            if not line:
                break
            logger.debug(f"{name}: {line.decode().strip()}")

    asyncio.create_task(read_output(process.stdout, "SSH STDOUT"))
    asyncio.create_task(read_output(process.stderr, "SSH STDERR"))
    
    logger.info("SSH tunnel successfully established")
    return process

    # except Exception as e:
    #     logger.error(f"Failed to establish SSH tunnel: {str(e)}")
    #     return None
    
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up FastAPI server")
    app.state.ssh_tunnel = await setup_ssh_tunnel()
    if app.state.ssh_tunnel:
        # Add this
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # try:
        #     result = sock.connect_ex(('localhost', azyl_agent_port))
        #     print(f"sock connect error {result}")
        #     if result == 0:
        #         logger.info(f"Port {azyl_agent_port} is open")
        #     else:
        #         logger.error(f"Port {azyl_agent_port} is not open")
        # finally:
        #     sock.close()

        result = sock.connect_ex(('localhost', azyl_agent_port))
        print(f"sock connect error {result}")
        if result == 0:
            logger.info(f"Port {azyl_agent_port} is open")
        else:
            logger.error(f"Port {azyl_agent_port} is not open")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down FastAPI server")
    if hasattr(app.state, 'ssh_tunnel') and app.state.ssh_tunnel:
        logger.info("Terminating SSH tunnel")
        app.state.ssh_tunnel.terminate()
        await app.state.ssh_tunnel.wait()


@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Add more detailed request logging
    logger.info(f"=== Incoming {request.method} request to {request.url} ===")
    logger.info(f"Headers: {dict(request.headers)}")
    
    if request.method == "POST":
        body = await request.body()
        logger.info(f"Request body: {body}")
    
    try:
        response = await call_next(request)
        logger.info(f"Response status code: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        raise


@app.post("/")
async def handle_instruction(drone_input: DroneInstruction):
    import os 
    import requests
    from openai import OpenAI
    from api_tasks.basic_poligon_u import load_from_json, post_request


    json_secrets = load_from_json(filepath=rf'{os.path.dirname(__file__)}\config.json')
    model = "gpt-4o-mini" 
    open_ai_api_key = json_secrets["open_ai_api_key"]
    client = OpenAI(api_key=open_ai_api_key)
    result = await flight_evaluator(client, model, drone_input.instruction)
    real_answer = result[0]

    return {"status": "success", "description": real_answer}

    # try:
    #     logger.info("=== POST Request Details ===")
    #     logger.info(f"Client Host: {Request.client.host}")
    #     logger.info(f"Request URL: {Request.url}")
    #     logger.info(f"Headers: {dict(Request.headers)}")
    #     logger.info(f"Instruction: {drone_input.instruction}")
        
    #     result = await flight_evaluator(client, model, drone_input.instruction)
    #     return {"status": "success", "instruction": result}
    # except Exception as e:
    #     logger.error(f"Error processing POST request: {str(e)}", exc_info=True)
    #     raise HTTPException(status_code=500, detail=str(e))
    
    
    
@app.get("/")  # Added GET handler for root path
async def root():
    return {"status": "ok", "message": "API is running"}

@app.get("/health")
async def health():
    return {"status": "ok", "time": datetime.now().isoformat()}


@app.get("/test")
async def test_endpoint():
    try:
        logger.info("Test endpoint accessed")
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error in test endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import os 
    import requests
    from openai import OpenAI

    from api_tasks.basic_poligon_u import load_from_json, post_request
    
    local_model = False 

    json_secrets = load_from_json(filepath=rf'{os.path.dirname(__file__)}\config.json')

    open_ai_api_key = json_secrets["open_ai_api_key"]
    anthropic_api_key = json_secrets["anthropic_api_key"]
    ai_devs_key = json_secrets["api_key"]
    model = "gpt-4o-mini" 


    task_4_4_data_source = json_secrets["task_4_4_data_source"]
    task_4_4_endpoint_url = json_secrets["task_4_4_endpoint_url"]
    task_4_4_map_image = json_secrets["task_4_4_map_image"]
    task_4_4_azyl_url = json_secrets["task_4_4_azyl_url"]
    azyl_agent_id = int(json_secrets["azyl_agent_id"])
    azyl_agent_port = int(json_secrets["azyl_agent_port"])
    local_port = 8000
    localhost = 'localhost'
    localhost = '127.0.0.1'

    session = requests.Session()
    client = OpenAI(api_key=open_ai_api_key)
    uvicorn.run(app, port=local_port)

    # launch this and run task_4_04_map_journey.py from terminal