"""
Pre-defined example tasks demonstrating all supported task types.
Run from project root: python examples/example_tasks.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from rich.console import Console
from rich.rule import Rule

load_dotenv()

from orchestrator import Orchestrator

console = Console()

EXAMPLE_TASKS = [
    {
        "name": "ChatGPT only — code explanation",
        "task": {
            "type": "chatgpt",
            "prompt": "Explain the difference between a list and a tuple in Python.",
            "system_prompt": "You are a concise Python tutor.",
        },
    },
    {
        "name": "Gemini only — creative writing",
        "task": {
            "type": "gemini",
            "prompt": "Write a two-sentence story about a robot learning to paint.",
        },
    },
    {
        "name": "Parallel — compare perspectives",
        "task": {
            "type": "parallel",
            "prompt": "What is the future of artificial intelligence in healthcare?",
        },
    },
    {
        "name": "Pipeline — draft then refine",
        "task": {
            "type": "pipeline",
            "prompt": "Describe the concept of recursion to a 10-year-old.",
            "system_prompt": "Keep explanations simple and engaging.",
        },
    },
]


def main():
    console.print("[bold cyan]Multi-AI Orchestrator — Example Tasks[/bold cyan]\n")

    orchestrator = Orchestrator()

    for i, example in enumerate(EXAMPLE_TASKS, 1):
        console.print(Rule(f"[bold]Example {i}: {example['name']}[/bold]"))
        result = orchestrator.run_task(example["task"])

        for key, value in result.items():
            if key in ("chatgpt_response", "chatgpt_draft", "gemini_response", "gemini_refined"):
                label = key.replace("_", " ").title()
                console.print(f"\n[bold]{label}:[/bold]")
                console.print(value)
        console.print()


if __name__ == "__main__":
    main()
