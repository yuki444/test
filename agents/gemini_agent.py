import os
import google.generativeai as genai


class GeminiAgent:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        genai.configure(api_key=api_key)

    def call(self, prompt: str, model: str = "gemini-1.5-flash", system_prompt: str = None) -> str:
        try:
            generation_config = {}
            model_kwargs = {"model_name": model}
            if system_prompt:
                model_kwargs["system_instruction"] = system_prompt

            gen_model = genai.GenerativeModel(**model_kwargs)
            response = gen_model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"[Gemini Error] {e}"
