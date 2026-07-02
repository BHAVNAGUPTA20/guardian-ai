from backend.gemini import generate_main_answer


class GeneratorAgent:
    def run(self, prompt: str, model: str = "gemini-2.5-flash"):
        return generate_main_answer(prompt=prompt, model=model)