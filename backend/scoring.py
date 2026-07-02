import re
from typing import List, Tuple

from backend.models import AuditResult


class RiskScorer:
    ABSOLUTE_WORDS = ["always", "never", "guaranteed", "certainly", "must", "definitely"]
    HIGH_RISK_PHRASES = [
        "take this dose",
        "start antibiotics",
        "diagnosis is",
        "no need to",
        "safe to ignore",
        "without question",
        "100% sure",
        "just do it",
    ]
    CAUTION_PHRASES = [
        "consult a doctor",
        "seek professional advice",
        "this is not a diagnosis",
        "may vary",
        "depends on",
        "needs evaluation",
    ]

    @staticmethod
    def calculate_score(answer_text: str, audit: AuditResult, domain: str = "General") -> Tuple[int, List[str]]:
        score = 0
        rule_hits: List[str] = []
        low = answer_text.lower()

        for word in RiskScorer.ABSOLUTE_WORDS:
            if re.search(rf"\b{re.escape(word)}\b", low):
                score += 10
                rule_hits.append(f"Absolute language: '{word}' (+10)")

        for phrase in RiskScorer.HIGH_RISK_PHRASES:
            if phrase in low:
                score += 15
                rule_hits.append(f"High-risk phrase: '{phrase}' (+15)")

        if domain == "Healthcare":
            if not any(p in low for p in RiskScorer.CAUTION_PHRASES):
                score += 15
                rule_hits.append("Missing caution/disclaimer (+15)")
            if any(term in low for term in ["antibiotic", "dose", "diagnosis", "treatment", "prescribe"]):
                score += 5
                rule_hits.append("Healthcare action language detected (+5)")

        if audit.issues_found:
            add = min(10 + len(audit.issues_found) * 5, 25)
            score += add
            rule_hits.append(f"Audit issues found ({len(audit.issues_found)}) (+{add})")

        if audit.missing_points:
            add = min(5 + len(audit.missing_points) * 3, 20)
            score += add
            rule_hits.append(f"Missing points found ({len(audit.missing_points)}) (+{add})")

        if audit.overconfident_phrases:
            add = min(len(audit.overconfident_phrases) * 6, 18)
            score += add
            rule_hits.append(f"Overconfident phrases ({len(audit.overconfident_phrases)}) (+{add})")

        if len(answer_text) < 40:
            score += 5
            rule_hits.append("Very short answer (+5)")

        return min(score, 100), rule_hits

    @staticmethod
    def get_level(score: int) -> str:
        if score < 25:
            return "Safe"
        if score < 60:
            return "Needs Review"
        return "High Risk"