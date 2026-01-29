"""
Interactive REPL test client for msg-agent server.
"""

import os
import json
import uuid
import httpx
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
from rich.table import Table

load_dotenv()
DOMAIN = os.getenv('SERVER_DOMAIN')
SERVER_URL = f"https://{DOMAIN}" if "localhost" not in DOMAIN else f"http://{DOMAIN}"

console = Console()


def display_tool_call(tc: dict) -> None:
    """Display a tool call with its arguments in a table."""
    console.print(f"\n[bold cyan]Tool:[/bold cyan] {tc['tool_name']}")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Parameter", style="dim")
    table.add_column("Value")

    for key, value in tc["arguments"].items():
        if isinstance(value, (dict, list)):
            value_str = json.dumps(value, indent=2)
        else:
            value_str = str(value)
        table.add_row(key, value_str)

    console.print(table)


def display_clarification(clarification: dict) -> None:
    """Display a clarification request."""
    question = clarification.get("question", "No question provided")
    context = clarification.get("context", "")

    console.print(f"\n[bold cyan]Question:[/bold cyan] {question}")
    if context:
        console.print(f"[dim]Context: {context}[/dim]")


def handle_success(response: dict) -> None:
    """Display successful response."""
    console.print(
        Panel(
            response.get("response", "No response content"),
            title="[green]SUCCESS[/green]",
            border_style="green",
        )
    )


def handle_oauth(response: dict) -> None:
    """Display OAuth requirement with URL."""
    url = response.get("url", "No URL provided")
    message = response.get("response", "Authentication required")

    console.print(
        Panel(
            f"[bold]{message}[/bold]\n\n[link={url}]{url}[/link]",
            title="[yellow]OAuth Required[/yellow]",
            border_style="yellow",
        )
    )


def handle_error(response: dict) -> None:
    """Display error message."""
    console.print(
        Panel(
            response.get("message", "Unknown error"),
            title="[red]ERROR[/red]",
            border_style="red",
        )
    )


def handle_confirmation(response: dict, thread_id: str) -> None:
    """Handle confirmation flow with user approval prompts."""
    console.print(
        Panel(
            "The agent wants to perform the following action(s):",
            title="[yellow]CONFIRMATION REQUIRED[/yellow]",
            border_style="yellow",
        )
    )

    tool_calls = response["pending_action"]["tool_calls"]
    approvals = []

    for tc in tool_calls:
        display_tool_call(tc)

        approved = Confirm.ask("\nApprove this action?")
        approval = {"call_id": tc["call_id"], "approved": approved}

        if not approved:
            feedback = Prompt.ask("Reason for rejection")
            approval["feedback"] = feedback

        approvals.append(approval)

    console.print("\n[dim]Sending approval decisions...[/dim]")
    resume_response = send_resume(thread_id, approvals=approvals)
    handle_response(resume_response, thread_id)


def handle_clarification(response: dict, thread_id: str) -> None:
    """Handle clarification flow with user input prompts."""
    console.print(
        Panel(
            "The agent needs clarification:",
            title="[yellow]CLARIFICATION REQUIRED[/yellow]",
            border_style="yellow",
        )
    )

    clarifications = response["pending_action"]["clarifications"]
    responses = []

    for clarification in clarifications:
        display_clarification(clarification)

        user_response = Prompt.ask("\nYour response")
        responses.append({
            "call_id": clarification["call_id"],
            "response": user_response
        })

    console.print("\n[dim]Sending clarification responses...[/dim]")
    resume_response = send_resume(thread_id, clarification_responses=responses)
    handle_response(resume_response, thread_id)


def send_run(thread_id: str, user_request: str) -> dict:
    """Send request to /run endpoint."""
    with httpx.Client(timeout=120.0) as client:
        resp = client.post(
            f"{SERVER_URL}/run",
            json={"thread_id": thread_id, "user_request": user_request},
        )
        return resp.json()


def send_resume(
    thread_id: str,
    approvals: list = None,
    clarification_responses: list = None
) -> dict:
    """Send approvals or clarification responses to /resume endpoint."""
    payload = {"thread_id": thread_id}
    if approvals is not None:
        payload["approvals"] = approvals
    if clarification_responses is not None:
        payload["clarification_responses"] = clarification_responses

    with httpx.Client(timeout=120.0) as client:
        resp = client.post(f"{SERVER_URL}/resume", json=payload)
        return resp.json()


def handle_response(response: dict, thread_id: str) -> None:
    """Route response to appropriate handler."""
    status = response.get("status")

    if status == "success":
        handle_success(response)
    elif status == "oauth_required":
        handle_oauth(response)
    elif status == "clarification_required":
        handle_clarification(response, thread_id)
    elif status == "confirmation_required":
        handle_confirmation(response, thread_id)
    elif status == "error":
        handle_error(response)
    else:
        console.print(f"[red]Unknown status: {status}[/red]")
        console.print(Syntax(json.dumps(response, indent=2), "json"))


def main() -> None:
    """Run the REPL loop."""
    thread_id = str(uuid.uuid4())

    console.print(
        Panel(
            f"[bold]MSG-Agent Test Client[/bold]\n\n"
            f"Server: [cyan]{SERVER_URL}[/cyan]\n"
            f"Thread: [dim]{thread_id}[/dim]\n\n"
            f"Type [bold]exit[/bold] or [bold]quit[/bold] to exit.",
            border_style="blue",
        )
    )

    while True:
        try:
            user_input = Prompt.ask("\n[bold green]>[/bold green]")

            if user_input.lower() in ("exit", "quit"):
                console.print("[dim]Goodbye![/dim]")
                break

            if not user_input.strip():
                continue

            console.print("[dim]Sending request...[/dim]")
            response = send_run(thread_id, user_input)
            handle_response(response, thread_id)

        except KeyboardInterrupt:
            console.print("\n[dim]Interrupted. Goodbye![/dim]")
            break
        except httpx.ConnectError:
            console.print(
                f"[red]Could not connect to server at {SERVER_URL}[/red]\n"
                "[dim]Make sure the server is running: "
                "uv run uvicorn src.main:app --port 8002[/dim]"
            )
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


if __name__ == "__main__":
    main()
