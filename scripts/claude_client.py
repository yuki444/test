"""Anthropic Claude API client."""
import anthropic


class ClaudeClient:
    def __init__(self, model: str = "claude-opus-4-8"):
        self.client = anthropic.Anthropic()
        self.model = model

    def complete(self, system: str, user: str, max_tokens: int = 4096) -> str:
        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return message.content[0].text
