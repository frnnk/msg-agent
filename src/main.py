"""
Entrypoint for the FastAPI server.
"""

import logging
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from langgraph.types import Command
from utils.models import RunBody, ResumeBody
from agentic.graph import run_graph, graph
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

    pending = final_state.get('pending_action', NO_ACTION)

    if pending['kind'] == 'confirmation':
        return JSONResponse(
            content={
                "status": "confirmation_required",
                "thread_id": body.thread_id,
                "pending_action": pending
            },
            status_code=status.HTTP_202_ACCEPTED
        )

    if pending['kind'] == 'oauth_url':
        return JSONResponse(
            content={
                "status": "oauth_required",
                "response": final_state['final_response'],
                "url": pending['url']
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
async def resume(body: ResumeBody):
    """
    Resume a paused graph execution with user approval decisions.

    Used to continue after human_confirmation interrupt.
    """
    approval_data = [
        {
            'call_id': a.call_id,
            'approved': a.approved,
            'feedback': a.feedback
        }
        for a in body.approvals
    ]

    try:
        final_state = await graph.ainvoke(
            Command(resume=approval_data),
            config={"configurable": {"thread_id": body.thread_id}}
        )

        pending = final_state.get('pending_action', NO_ACTION)

        # Check if we hit another interrupt (e.g., more tools need confirmation)
        if pending['kind'] == 'confirmation':
            return JSONResponse(
                content={
                    "status": "confirmation_required",
                    "thread_id": body.thread_id,
                    "pending_action": pending
                },
                status_code=status.HTTP_202_ACCEPTED
            )

        # Handle OAuth URL if it comes up during resumed execution
        if pending['kind'] == 'oauth_url':
            return JSONResponse(
                content={
                    "status": "oauth_required",
                    "response": final_state.get('final_response'),
                    "url": pending['url']
                },
                status_code=status.HTTP_202_ACCEPTED
            )

        return JSONResponse(
            content={
                "status": "success",
                "response": final_state.get('final_response', 'Action completed.')
            },
            status_code=status.HTTP_200_OK
        )

    except Exception as e:
        logging.error(f"Resume error: {e}")
        return JSONResponse(
            content={"status": "error", "message": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

