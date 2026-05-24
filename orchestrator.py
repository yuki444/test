import concurrent.futures
from datetime import datetime
from agents import OpenAIAgent, GeminiAgent


class Orchestrator:
    def __init__(self):
        self.openai_agent = OpenAIAgent()
        self.gemini_agent = GeminiAgent()

    def run_task(self, task: dict) -> dict:
        task_type = task.get("type")
        prompt = task.get("prompt", "")
        system_prompt = task.get("system_prompt", None)
        started_at = datetime.utcnow().isoformat()

        if task_type == "chatgpt":
            result = self._run_chatgpt(prompt, system_prompt)
        elif task_type == "gemini":
            result = self._run_gemini(prompt, system_prompt)
        elif task_type == "parallel":
            result = self._run_parallel(prompt, system_prompt)
        elif task_type == "pipeline":
            result = self._run_pipeline(prompt, system_prompt)
        else:
            result = {"error": f"Unknown task type: {task_type!r}"}

        return {
            "task_type": task_type,
            "prompt": prompt,
            "started_at": started_at,
            "completed_at": datetime.utcnow().isoformat(),
            **result,
        }

    def _run_chatgpt(self, prompt: str, system_prompt: str) -> dict:
        response = self.openai_agent.call(prompt, system_prompt=system_prompt)
        return {"chatgpt_response": response}

    def _run_gemini(self, prompt: str, system_prompt: str) -> dict:
        response = self.gemini_agent.call(prompt, system_prompt=system_prompt)
        return {"gemini_response": response}

    def _run_parallel(self, prompt: str, system_prompt: str) -> dict:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_chatgpt = executor.submit(self.openai_agent.call, prompt, "gpt-4o-mini", system_prompt)
            future_gemini = executor.submit(self.gemini_agent.call, prompt, "gemini-1.5-flash", system_prompt)
            chatgpt_response = future_chatgpt.result()
            gemini_response = future_gemini.result()
        return {
            "chatgpt_response": chatgpt_response,
            "gemini_response": gemini_response,
        }

    def _run_pipeline(self, prompt: str, system_prompt: str) -> dict:
        chatgpt_response = self.openai_agent.call(prompt, system_prompt=system_prompt)
        refinement_prompt = (
            f"Original request: {prompt}\n\n"
            f"Draft response:\n{chatgpt_response}\n\n"
            "Please refine and improve the above response."
        )
        gemini_response = self.gemini_agent.call(refinement_prompt, system_prompt=system_prompt)
        return {
            "chatgpt_draft": chatgpt_response,
            "gemini_refined": gemini_response,
        }
