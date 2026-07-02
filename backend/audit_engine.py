from agents.generator_agent import GeneratorAgent
from agents.guardian_agent import GuardianAgent
from backend.models import WorkflowResult
from backend.scoring import RiskScorer


class AuditEngine:
    def __init__(self):
        self.generator = GeneratorAgent()
        self.guardian = GuardianAgent()
        self.scorer = RiskScorer()

    def run(
        self,
        question: str,
        model: str = "gemini-2.5-flash",
        domain: str = "Healthcare",
    ) -> WorkflowResult:
        generated = self.generator.run(prompt=question, model=model)

        audit = self.guardian.run(
            question=question,
            answer=generated.answer,
            model=model,
        )

        score, rule_hits = self.scorer.calculate_score(
            answer_text=generated.answer,
            audit=audit,
            domain=domain,
        )
        level = self.scorer.get_level(score)

        audit.risk_score = score
        audit.risk_level = level

        return WorkflowResult(
            prompt=question,
            generated_answer=generated,
            audit=audit,
            rule_hits=rule_hits,
            final_score=score,
            final_level=level,
        )

    # Backward compatibility
    def run_audit(
        self,
        question: str,
        model: str = "gemini-2.5-flash",
        domain: str = "Healthcare",
    ) -> WorkflowResult:
        return self.run(question=question, model=model, domain=domain)