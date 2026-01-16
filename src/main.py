"""
Entrypoint for the FastAPI server.
"""

import logging
from fastapi import FastAPI, Response, status
from langgraph.types import Command
from utils.models import RunBody, ResumeBody, AgentResponse
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


@app.post('/run', response_model=AgentResponse)
async def run(body: RunBody, response: Response):
    """
    Initiate a fresh user request.
    """
    final_state = await run_graph(
        thread_id=body.thread_id,
        initial_request=body.user_request
    )

    pending = final_state.get('pending_action', NO_ACTION)

    if pending['kind'] == 'confirmation':
        response.status_code = status.HTTP_202_ACCEPTED
        return AgentResponse(
            status="confirmation_required",
            thread_id=body.thread_id,
            pending_action=pending
        )

    if pending['kind'] == 'oauth_url':
        response.status_code = status.HTTP_202_ACCEPTED
        return AgentResponse(
            status="oauth_required",
            response=final_state['final_response'],
            url=pending['url']
        )

    return AgentResponse(
        status="success",
        response=final_state['final_response']
    )


@app.post('/resume', response_model=AgentResponse)
async def resume(body: ResumeBody, response: Response):
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

        if pending['kind'] == 'confirmation':
            response.status_code = status.HTTP_202_ACCEPTED
            return AgentResponse(
                status="confirmation_required",
                thread_id=body.thread_id,
                pending_action=pending
            )

        if pending['kind'] == 'oauth_url':
            response.status_code = status.HTTP_202_ACCEPTED
            return AgentResponse(
                status="oauth_required",
                response=final_state.get('final_response'),
                url=pending['url']
            )

        return AgentResponse(
            status="success",
            response=final_state.get('final_response', 'Action completed.')
        )

    except Exception as e:
        logging.error(f"Resume error: {e}")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return AgentResponse(
            status="error",
            message=str(e)
        )

