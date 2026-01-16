"""
Interactive REPL test client for msg-agent server.
"""

import json
import uuid
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
from rich.table import Table

SERVER_URL = "http://127.0.0.1:8002"

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
    resume_response = send_resume(thread_id, approvals)
    handle_response(resume_response, thread_id)


def send_run(thread_id: str, user_request: str) -> dict:
    """Send request to /run endpoint."""
    with httpx.Client(timeout=120.0) as client:
        resp = client.post(
            f"{SERVER_URL}/run",
            json={"thread_id": thread_id, "user_request": user_request},
        )
        return resp.json()


def send_resume(thread_id: str, approvals: list) -> dict:
    """Send approvals to /resume endpoint."""
    with httpx.Client(timeout=120.0) as client:
        resp = client.post(
            f"{SERVER_URL}/resume",
            json={"thread_id": thread_id, "approvals": approvals},
        )
        return resp.json()


def handle_response(response: dict, thread_id: str) -> None:
    """Route response to appropriate handler."""
    status = response.get("status")

    if status == "success":
        handle_success(response)
    elif status == "oauth_required":
        handle_oauth(response)
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
