"""
Entrypoint for the FastAPI server.
"""

import logging
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from utils.models import RunBody
from agentic.graph import run_graph
from agentic.state import NO_ACTION

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


app = FastAPI()
@app.get('/health-check')
async def health():
    return "Server is healthy"

@app.post('/run')
async def run(body: RunBody):
    final_state = await run_graph(
        thread_id=body.thread_id,
        initial_request=body.user_request
    )

    if final_state.get('pending_action', NO_ACTION)['kind'] == 'oauth_url':
        return JSONResponse(
            content={
                "status": "oauth_required",
                "response": final_state['final_response'],
                "url": final_state['pending_action']['url']
            },
            status_code=status.HTTP_202_ACCEPTED
        )
    
    return JSONResponse(
        content={
            "status": "success",
            "response": final_state['final_response'],
        },
        status_code=status.HTTP_200_OK
    )

@app.post('/resume')
async def resume():
    pass

