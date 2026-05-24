#!/usr/bin/env python3
import argparse
import sys
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich import box

load_dotenv()

console = Console()

DEMO_TASKS = [
    {
        "type": "chatgpt",
        "prompt": "Explain what a neural network is in two sentences.",
        "description": "Single ChatGPT call",
    },
    {
        "type": "gemini",
        "prompt": "What are three key benefits of Python for data science?",
        "description": "Single Gemini call",
    },
    {
        "type": "parallel",
        "prompt": "What is the most important skill for a software engineer?",
        "description": "Parallel call to both AIs",
    },
]


def print_result(result: dict):
    task_type = result.get("task_type", "unknown")
    prompt = result.get("prompt", "")
    meta = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    meta.add_row("[bold]Type[/bold]", task_type)
    meta.add_row("[bold]Prompt[/bold]", prompt)
    meta.add_row("[bold]Started[/bold]", result.get("started_at", ""))
    meta.add_row("[bold]Completed[/bold]", result.get("completed_at", ""))
    console.print(meta)

    if "error" in result:
        console.print(Panel(result["error"], title="[red]Error[/red]", border_style="red"))
        return

    if task_type == "chatgpt":
        console.print(Panel(result.get("chatgpt_response", ""), title="[green]ChatGPT[/green]", border_style="green"))

    elif task_type == "gemini":
        console.print(Panel(result.get("gemini_response", ""), title="[blue]Gemini[/blue]", border_style="blue"))

    elif task_type == "parallel":
        console.print(Panel(result.get("chatgpt_response", ""), title="[green]ChatGPT[/green]", border_style="green"))
        console.print(Panel(result.get("gemini_response", ""), title="[blue]Gemini[/blue]", border_style="blue"))

    elif task_type == "pipeline":
        console.print(Panel(result.get("chatgpt_draft", ""), title="[green]ChatGPT Draft[/green]", border_style="green"))
        console.print(Panel(result.get("gemini_refined", ""), title="[blue]Gemini Refined[/blue]", border_style="blue"))


def run_demo(orchestrator):
    console.print(Panel("[bold yellow]Running Demo Mode[/bold yellow]", border_style="yellow"))
    for i, demo in enumerate(DEMO_TASKS, 1):
        console.rule(f"[bold]Task {i}: {demo['description']}[/bold]")
        task = {k: v for k, v in demo.items() if k != "description"}
        result = orchestrator.run_task(task)
        print_result(result)
        console.print()


def run_interactive(orchestrator):
    console.print(Panel("[bold cyan]Multi-AI Orchestrator — Interactive Mode[/bold cyan]", border_style="cyan"))
    console.print("Task types: [green]chatgpt[/green], [blue]gemini[/blue], [yellow]parallel[/yellow], [magenta]pipeline[/magenta]")
    console.print("Type [bold]exit[/bold] to quit.\n")

    while True:
        task_type = Prompt.ask("[bold]Task type[/bold]").strip().lower()
        if task_type == "exit":
            break
        if task_type not in ("chatgpt", "gemini", "parallel", "pipeline"):
            console.print("[red]Invalid task type.[/red]")
            continue

        prompt = Prompt.ask("[bold]Prompt[/bold]").strip()
        if not prompt:
            console.print("[red]Prompt cannot be empty.[/red]")
            continue

        system_prompt_input = Prompt.ask("[bold]System prompt[/bold] (optional, press Enter to skip)", default="")
        task = {
            "type": task_type,
            "prompt": prompt,
        }
        if system_prompt_input:
            task["system_prompt"] = system_prompt_input

        console.print("\n[dim]Running...[/dim]")
        result = orchestrator.run_task(task)
        console.rule("[bold]Result[/bold]")
        print_result(result)
        console.print()


def main():
    parser = argparse.ArgumentParser(description="Multi-AI Orchestrator (Claude + ChatGPT + Gemini)")
    parser.add_argument("--demo", action="store_true", help="Run demo tasks instead of interactive mode")
    args = parser.parse_args()

    try:
        from orchestrator import Orchestrator
        orchestrator = Orchestrator()
    except ValueError as e:
        console.print(f"[red]Initialization error:[/red] {e}")
        console.print("Copy [bold].env.example[/bold] to [bold].env[/bold] and fill in your API keys.")
        sys.exit(1)

    if args.demo:
        run_demo(orchestrator)
    else:
        run_interactive(orchestrator)


if __name__ == "__main__":
    main()
