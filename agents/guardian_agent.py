from backend.gemini import audit_answer


class GuardianAgent:
    def run(self, question: str, answer: str, model: str = "gemini-2.5-flash"):
        return audit_answer(question=question, answer=answer, model=model)