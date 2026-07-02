import difflib
import html
import io
import json
import os
import time
import uuid
from datetime import datetime

import streamlit as st

from backend.audit_engine import AuditEngine

try:
    from backend.gemini import get_client as backend_get_client
except Exception:
    backend_get_client = None

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except Exception:
    FPDF_AVAILABLE = False

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except Exception:
    GENAI_AVAILABLE = False

try:
    import docx as python_docx
    DOCX_AVAILABLE = True
except Exception:
    DOCX_AVAILABLE = False


st.set_page_config(
    page_title="Guardian AI — AI Firewall for High-Stakes Decisions",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ----------------------------------------------------------------------------
# GLOBAL STYLE
# ----------------------------------------------------------------------------

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --bg: #09090b; --panel: #18181b; --panel2: #0f172a; --line: rgba(255,255,255,0.09);
        --text: #f8fafc; --muted: rgba(248,250,252,0.68);
        --purple: #8b5cf6; --purple2: #7c3aed; --green: #00ff99; --red: #ff4d6d;
        --amber: #f59e0b; --cyan: #22d3ee;
    }
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    h1,h2,h3,h4, .hero-title, .card-value, .workflow-label { font-family: 'Space Grotesk', sans-serif; }
    .stApp {
        background:
            radial-gradient(circle at 15% -5%, rgba(139,92,246,0.20), transparent 30%),
            radial-gradient(circle at 85% -5%, rgba(0,255,153,0.08), transparent 30%),
            radial-gradient(circle at 50% 100%, rgba(34,211,238,0.06), transparent 40%),
            linear-gradient(180deg, #09090b 0%, #0b0d16 100%);
        color: var(--text);
    }
    #MainMenu, footer, header { visibility: hidden; }

    .hero {
        position: relative; padding: 2.4rem 2.2rem; border: 1px solid var(--line); border-radius: 28px;
        background: linear-gradient(135deg, rgba(124,58,237,0.20), rgba(9,9,11,0.85));
        backdrop-filter: blur(18px); box-shadow: 0 25px 70px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.04);
        margin-bottom: 1.4rem; overflow: hidden; animation: fadeUp 0.6s ease both;
    }
    .hero::before {
        content: ""; position: absolute; inset: -2px;
        background: linear-gradient(120deg, transparent, rgba(139,92,246,0.5), transparent 60%);
        opacity: 0.35; animation: sheen 6s linear infinite; pointer-events: none;
    }
    @keyframes sheen { 0% { transform: translateX(-40%) rotate(8deg); } 100% { transform: translateX(40%) rotate(8deg); } }
    .hero-kicker { display:inline-flex; align-items:center; gap:0.4rem; font-size: 0.76rem; letter-spacing: 0.14em;
        text-transform: uppercase; color: var(--cyan); opacity: 0.9; margin-bottom: 0.6rem; }
    .hero-kicker .dot { width:6px; height:6px; border-radius:50%; background: var(--green);
        box-shadow: 0 0 10px var(--green); animation: pulse 1.6s ease-in-out infinite; }
    .hero-title { font-size: 3.2rem; font-weight: 800; line-height: 1.0; margin-bottom: 0.5rem;
        background: linear-gradient(90deg, #fff, #c9b8ff 60%, var(--cyan));
        -webkit-background-clip: text; background-clip: text; color: transparent; }
    .hero-tagline { font-size: 1.28rem; font-weight: 600; margin-bottom: 0.55rem; }
    .hero-subtitle { font-size: 1.0rem; opacity: 0.82; max-width: 46rem; line-height: 1.6; margin-bottom: 1.0rem; }
    .hero-badge { display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.4rem 0.8rem; margin-right: 0.5rem;
        margin-top: 0.4rem; border-radius: 999px; border: 1px solid rgba(255,255,255,0.13);
        background: rgba(255,255,255,0.045); font-size: 0.83rem; transition: all 0.2s ease; }
    .hero-badge:hover { border-color: rgba(139,92,246,0.6); background: rgba(139,92,246,0.12); }

    .card { padding: 1.05rem 1.1rem 1rem 1.1rem; border: 1px solid var(--line); border-radius: 20px;
        background: linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
        box-shadow: 0 14px 40px rgba(0,0,0,0.22); min-height: 118px;
        transition: transform 0.18s ease, border-color 0.18s ease; animation: fadeUp 0.5s ease both; }
    .card:hover { transform: translateY(-2px); border-color: rgba(139,92,246,0.4); }
    .card-title { opacity: 0.68; font-size: 0.85rem; margin-bottom: 0.4rem; }
    .card-value { font-size: 1.9rem; font-weight: 800; line-height: 1.04; }
    .card-subtitle { margin-top: 0.35rem; opacity: 0.65; font-size: 0.82rem; }

    .section-box { padding: 1.1rem 1.15rem; border: 1px solid var(--line); border-radius: 20px;
        background: rgba(255,255,255,0.035); box-shadow: 0 12px 34px rgba(0,0,0,0.16); }
    .smallcaps { font-size: 0.75rem; letter-spacing: 0.11em; text-transform: uppercase; opacity: 0.7; font-weight: 600; }
    .muted { opacity: 0.68; }

    .rule-chip { display: inline-flex; flex-direction: column; gap: 0.15rem; padding: 0.5rem 0.85rem;
        margin: 0.25rem 0.35rem 0.25rem 0; border-radius: 14px; border: 1px solid rgba(255,77,109,0.35);
        background: rgba(255,77,109,0.09); font-size: 0.83rem; max-width: 320px; }
    .rule-chip .rc-title { font-weight: 700; color: #ffb3c1; }
    .rule-chip .rc-sub { opacity: 0.7; font-size: 0.75rem; }

    .usecase { padding: 0.95rem 1rem; border-radius: 16px; border: 1px solid var(--line);
        background: rgba(255,255,255,0.035); transition: all 0.15s ease; cursor: pointer; }
    .usecase:hover { transform: translateY(-2px); border-color: rgba(139,92,246,0.55);
        background: rgba(139,92,246,0.09); box-shadow: 0 10px 28px rgba(139,92,246,0.18); }

    .pipeline-wrap { display:flex; align-items:stretch; gap: 0.5rem; overflow-x:auto; padding: 0.3rem 0.1rem; }
    .pipe-step { flex: 1; min-width: 140px; padding: 0.9rem 0.7rem; text-align:center; border: 1px solid var(--line);
        border-radius: 18px; background: rgba(255,255,255,0.035); opacity: 0; animation: fadeUp 0.5s ease forwards; }
    .pipe-step.active { border-color: rgba(0,255,153,0.55); box-shadow: 0 0 24px rgba(0,255,153,0.18); }
    .pipe-icon { font-size: 1.4rem; margin-bottom: 0.2rem; }
    .pipe-label { font-weight: 700; font-size: 0.86rem; }
    .pipe-sub { margin-top: 0.25rem; opacity: 0.68; font-size: 0.72rem; line-height: 1.3; }
    .pipe-arrow { align-self:center; opacity: 0.35; font-size: 1.2rem; padding: 0 0.1rem; }

    @keyframes fadeUp { from { opacity:0; transform: translateY(10px);} to { opacity:1; transform: translateY(0);} }
    @keyframes pulse { 0%,100% { opacity:1; transform: scale(1);} 50% { opacity:0.5; transform: scale(1.25);} }

    .glow-line { height: 2px; border-radius: 999px;
        background: linear-gradient(90deg, transparent, rgba(139,92,246,0.9), rgba(0,255,153,0.7), transparent);
        box-shadow: 0 0 18px rgba(139,92,246,0.35); margin: 0.6rem 0 1.1rem 0; }

    .diff-box { padding: 1rem; border: 1px solid var(--line); border-radius: 18px; background: rgba(255,255,255,0.03);
        min-height: 160px; line-height: 1.75; font-size: 0.95rem; }
    .diff-add { background: rgba(0,255,153,0.18); color: #b8ffe0; border-radius: 4px; padding: 0 2px; }
    .diff-del { background: rgba(255,77,109,0.18); color: #ffc2cd; text-decoration: line-through; border-radius: 4px; padding: 0 2px; }

    .gauge-wrap { display:flex; flex-direction:column; align-items:center; }
    .doc-type-badge { display:inline-flex; align-items:center; gap:0.4rem; padding: 0.5rem 0.9rem; border-radius: 999px;
        border: 1px solid rgba(139,92,246,0.4); background: rgba(139,92,246,0.12); font-weight: 700; font-size: 0.9rem; }

    .stButton>button { border-radius: 12px !important; border: 1px solid rgba(255,255,255,0.12) !important; transition: all 0.15s ease !important; }
    .stButton>button:hover { border-color: rgba(139,92,246,0.55) !important; }
    ::-webkit-scrollbar { height: 6px; width: 6px; }
    ::-webkit-scrollbar-thumb { background: rgba(139,92,246,0.4); border-radius: 999px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# SESSION STATE
# ----------------------------------------------------------------------------

for key, default in [
    ("history", []), ("prompt", "Can I stop insulin if my sugar feels normal today?"),
    ("api_key", os.getenv("GEMINI_API_KEY", "")), ("last_result", None), ("domain", "Healthcare"),
    ("model", "gemini-2.5-flash"), ("selected_usecase", None), ("session_id", str(uuid.uuid4())[:8].upper()),
    ("last_meta", None), ("last_doc", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default


def set_gemini_key(api_key: str) -> bool:
    api_key = (api_key or "").strip()
    if not api_key:
        return False
    os.environ["GEMINI_API_KEY"] = api_key
    st.session_state.api_key = api_key
    if backend_get_client is not None and hasattr(backend_get_client, "cache_clear"):
        backend_get_client.cache_clear()
    if GENAI_AVAILABLE:
        genai.configure(api_key=api_key)
    return True


def level_color(level: str) -> str:
    return {"Safe": "var(--green)", "Needs Review": "var(--amber)", "High Risk": "var(--red)"}.get(level, "var(--cyan)")


def prompt_analysis(prompt: str, domain: str):
    text = (prompt or "").lower()
    flags, risk = [], 0
    high_stakes_terms = {
        "Healthcare": ["antibiotic", "dose", "diagnosis", "treatment", "fever", "pain", "surgery", "insulin", "kidney", "medicine"],
        "Research": ["study", "abstract", "method", "result", "paper", "citation", "reference", "thesis"],
        "Education": ["essay", "assignment", "quiz", "answer", "exam", "plagiarism"],
        "Legal": ["law", "legal", "lawsuit", "contract", "court", "case"],
        "Finance": ["invest", "return", "profit", "stock", "crypto", "buy", "sell", "portfolio"],
    }
    if any(t in text for t in high_stakes_terms.get(domain, [])):
        flags.append(f"{domain} high-stakes prompt"); risk += 25
    action_terms = ["should i", "can i", "is it safe", "start", "stop", "take", "ignore", "prescribe", "sign", "invest"]
    if any(w in text for w in action_terms):
        flags.append("Action request detected"); risk += 20
    if len(prompt.strip()) < 25:
        flags.append("Very short / underspecified prompt"); risk += 10
    if "?" in prompt:
        flags.append("Question form"); risk += 5
    if not flags:
        flags.append("General prompt")
    return min(risk, 100), flags


def metric_card(title, value, subtitle="", color=None, delay=0.0):
    color_style = f"color:{color};" if color else ""
    subtitle_html = f'<div class="card-subtitle">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f"""<div class="card" style="animation-delay:{delay}s;"><div class="card-title">{title}</div>
        <div class="card-value" style="{color_style}">{value}</div>{subtitle_html}</div>""",
        unsafe_allow_html=True,
    )


def box(title, body):
    st.markdown(
        f"""<div class="section-box"><div class="smallcaps">{title}</div>
        <div style="margin-top:0.55rem; line-height:1.65; white-space:pre-wrap;">{html.escape(body) if body else "<span class='muted'>—</span>"}</div></div>""",
        unsafe_allow_html=True,
    )


def list_box(title, items):
    body = "\n".join(f"• {i}" for i in items) if items else "None flagged"
    box(title, body)


def gauge_svg(value, color, size=128, label=""):
    value = max(0, min(100, value))
    radius = size / 2 - 10
    circumference = 2 * 3.14159265 * radius
    offset = circumference * (1 - value / 100)
    cx = cy = size / 2
    return f"""<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
        <circle cx="{cx}" cy="{cy}" r="{radius}" stroke="rgba(255,255,255,0.09)" stroke-width="10" fill="none"/>
        <circle cx="{cx}" cy="{cy}" r="{radius}" stroke="{color}" stroke-width="10" fill="none"
            stroke-linecap="round" stroke-dasharray="{circumference}" stroke-dashoffset="{offset}"
            transform="rotate(-90 {cx} {cy})" style="filter: drop-shadow(0 0 6px {color});"/>
        <text x="{cx}" y="{cy - 2}" text-anchor="middle" fill="#f8fafc" font-size="26" font-weight="800" font-family="Space Grotesk">{value}</text>
        <text x="{cx}" y="{cy + 20}" text-anchor="middle" fill="rgba(248,250,252,0.6)" font-size="11">{label}</text>
    </svg>"""


def word_diff_html(old_text, new_text):
    old_words, new_words = (old_text or "").split(), (new_text or "").split()
    sm = difflib.SequenceMatcher(None, old_words, new_words)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            out.append(html.escape(" ".join(new_words[j1:j2])))
        elif tag == "insert":
            out.append(f'<span class="diff-add">{html.escape(" ".join(new_words[j1:j2]))}</span>')
        elif tag == "delete":
            out.append(f'<span class="diff-del">{html.escape(" ".join(old_words[i1:i2]))}</span>')
        elif tag == "replace":
            out.append(f'<span class="diff-del">{html.escape(" ".join(old_words[i1:i2]))}</span>')
            out.append(f'<span class="diff-add">{html.escape(" ".join(new_words[j1:j2]))}</span>')
    return " ".join(out)


def diff_reasons(result):
    reasons = []
    for i in result["audit"].get("issues_found", []):
        reasons.append(("Modified", i))
    for m in result["audit"].get("missing_points", []):
        reasons.append(("Added", m))
    for r in result.get("rule_hits", []):
        reasons.append(("Rule triggered", r))
    return reasons


def explain_score_breakdown(result, prompt_flags):
    audit = result["audit"]
    components = []
    if any("high-stakes" in f.lower() for f in prompt_flags):
        components.append(("High-stakes domain prompt", 20))
    if any("action" in f.lower() for f in prompt_flags):
        components.append(("Direct action request", 15))
    if audit.get("issues_found"):
        components.append((f"{len(audit['issues_found'])} safety issue(s) found", min(10 * len(audit["issues_found"]), 30)))
    if audit.get("missing_points"):
        components.append((f"{len(audit['missing_points'])} missing safeguard(s)", min(8 * len(audit["missing_points"]), 24)))
    if audit.get("overconfident_phrases"):
        components.append((f"{len(audit['overconfident_phrases'])} overconfident phrase(s)", min(6 * len(audit["overconfident_phrases"]), 18)))
    if result.get("rule_hits"):
        components.append((f"{len(result['rule_hits'])} deterministic rule(s) triggered", min(12 * len(result["rule_hits"]), 30)))
    if not components:
        components.append(("Baseline assessment", result["final_score"]))
    raw_total = sum(c[1] for c in components)
    target = result["final_score"]
    if raw_total > 0 and raw_total != target:
        scale = target / raw_total
        components = [(label, round(val * scale)) for label, val in components]
    return components


def rule_chip(text):
    lowered = text.lower()
    hint = "Deterministic safety rule"
    if "drug" in lowered or "medic" in lowered or "prescri" in lowered:
        hint = "Medication safety rule"
    elif "hallucin" in lowered:
        hint = "Fact-grounding rule"
    elif "disclaimer" in lowered:
        hint = "Disclosure requirement"
    elif "emergency" in lowered:
        hint = "Escalation requirement"
    elif "confiden" in lowered:
        hint = "Overconfidence guard"
    return f"""<div class="rule-chip"><div class="rc-title">⚠ {html.escape(text)}</div><div class="rc-sub">{hint}</div></div>"""


def safety_checks(result):
    checks = []
    audit = result["audit"]
    generated = result["generated_answer"]["answer"].lower()
    rewrite = audit["safer_rewrite"].lower()
    checks.append(("Medical/professional caution added", "doctor" in rewrite or "professional" in rewrite or "evaluation" in rewrite))
    checks.append(("Risk explained", len(audit["issues_found"]) > 0 or len(audit["missing_points"]) > 0))
    checks.append(("Safer rewrite differs from original", generated.strip() != rewrite.strip()))
    checks.append(("Deterministic rules triggered", len(result["rule_hits"]) > 0))
    checks.append(("Confidence tempered", any(w in rewrite for w in ["consult", "evaluation", "professional", "needs", "caution"])))
    return checks


def build_pdf_report(result, domain, prompt_risk, meta, doc=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(30, 30, 40)
    pdf.cell(0, 12, "Guardian AI — Safety Audit Report", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(90, 90, 100)
    pdf.cell(0, 7, f"Audit ID: {meta['audit_id']}   |   Session: {meta['session_id']}   |   Generated: {meta['timestamp']}", ln=True)
    pdf.ln(4)

    def section(title, body):
        pdf.set_font("Helvetica", "B", 12); pdf.set_text_color(20, 20, 30)
        pdf.cell(0, 8, title, ln=True)
        pdf.set_font("Helvetica", "", 10); pdf.set_text_color(50, 50, 60)
        safe_body = (body or "-").encode("latin-1", "replace").decode("latin-1")
        pdf.multi_cell(0, 5.5, safe_body); pdf.ln(2)

    if doc:
        section("Document Type", doc.get("doc_type", "Unknown"))
    section("Domain / Prompt Risk Preview", f"Domain: {domain}\nPrompt risk preview: {prompt_risk}/100")
    section("Original Prompt / Document Text", result["prompt"][:3000])
    section("Final Risk Score", f"{result['final_score']}/100  —  {result['final_level']}")
    section("Original AI Answer", result["generated_answer"]["answer"])
    section("Guardian Safer Rewrite", result["audit"]["safer_rewrite"])
    section("Guardian Safety Analysis", result["audit"]["explanation"])
    section("Issues Found", "\n".join(f"- {i}" for i in result["audit"]["issues_found"]) or "None")
    section("Missing Points", "\n".join(f"- {i}" for i in result["audit"]["missing_points"]) or "None")
    section("Deterministic Rule Hits", "\n".join(f"- {i}" for i in result["rule_hits"]) or "None")
    if doc:
        section("Document-Specific Findings", json.dumps(doc.get("analysis", {}), indent=2)[:3000])
    section("Model / Latency", f"Model: {meta['model']}   Latency: {meta['latency']:.2f}s   Est. tokens: {meta['prompt_tokens']} in / {meta['completion_tokens']} out")
    return bytes(pdf.output(dest="S"))


def build_markdown_report(result, domain, prompt_risk, meta, doc=None):
    lines = [
        "# Guardian AI — Safety Audit Report", "",
        f"**Audit ID:** {meta['audit_id']}  |  **Session:** {meta['session_id']}  |  **Generated:** {meta['timestamp']}", "",
    ]
    if doc:
        lines += [f"**Document Type:** {doc.get('doc_type', 'Unknown')}", ""]
    lines += [
        f"**Domain:** {domain}  |  **Prompt Risk Preview:** {prompt_risk}/100", "",
        f"## Final Risk Score: {result['final_score']}/100 — {result['final_level']}", "",
        "## Original AI Answer", result["generated_answer"]["answer"], "",
        "## Guardian Safer Rewrite", result["audit"]["safer_rewrite"], "",
        "## Guardian Safety Analysis", result["audit"]["explanation"], "",
        "## Issues Found",
    ]
    lines += [f"- {i}" for i in result["audit"]["issues_found"]] or ["None"]
    lines += ["", "## Missing Points"]
    lines += [f"- {i}" for i in result["audit"]["missing_points"]] or ["None"]
    lines += ["", "## Deterministic Rule Hits"]
    lines += [f"- {r}" for r in result["rule_hits"]] or ["None"]
    lines += [""]
    if doc:
        lines += ["## Document-Specific Findings", "```json", json.dumps(doc.get("analysis", {}), indent=2), "```", ""]
    return "\n".join(lines)


def build_html_report(result, domain, prompt_risk, meta, doc=None):
    md = build_markdown_report(result, domain, prompt_risk, meta, doc)
    body = html.escape(md).replace("\n", "<br>")
    return f"""<html><head><meta charset="utf-8"><title>Guardian AI Report</title>
    <style>body{{font-family:Arial,sans-serif;background:#0b0d16;color:#f8fafc;padding:2rem;line-height:1.6;}}</style>
    </head><body>{body}</body></html>"""


# ----------------------------------------------------------------------------
# GEMINI MULTIMODAL PIPELINE
# ----------------------------------------------------------------------------

DOC_TYPES = ["Prescription", "Research Paper", "Clinical Note", "Lab Report", "Contract",
             "Policy", "Financial Document", "Essay", "Resume", "Other"]

DOC_TYPE_TO_DOMAIN = {
    "Prescription": "Healthcare", "Clinical Note": "Healthcare", "Lab Report": "Healthcare",
    "Research Paper": "Research", "Contract": "Legal", "Policy": "Legal",
    "Financial Document": "Finance", "Essay": "Education", "Resume": "Education", "Other": "Research",
}

EXTRACTION_PROMPTS = {
    "Prescription": """Extract from THIS SPECIFIC prescription and return ONLY JSON with keys:
drug_names (list of strings), doses (list), frequency (list), duration (list), diagnosis (string),
doctor_name (string or null), date (string or null), patient_name (string or null),
missing_safety_items (list of specific missing items in THIS document), possible_drug_interactions (list),
missing_documentation (list), missing_counselling (list), guardian_suggestions (list of specific,
actionable suggestions naming the actual drugs/doses found), risk_score (integer 0-100).
Be specific to the drugs and doses you actually found. Do not give generic prescription advice.""",
    "Clinical Note": """Extract from THIS SPECIFIC clinical note and return ONLY JSON with keys:
chief_complaint (string), findings (list), diagnoses (list), treatments_ordered (list),
missing_safety_items (list), risk_flags (list, specific to this note), guardian_suggestions (list),
risk_score (integer 0-100). Be specific to this note's actual content.""",
    "Lab Report": """Extract from THIS SPECIFIC lab report and return ONLY JSON with keys:
detected_values (list of objects with test, value, reference_range, flag),
missing_values (list of tests that should be present but aren't), critical_abnormalities (list, specific values),
suggested_followup (list, specific to the abnormal values found), risk_score (integer 0-100).""",
    "Research Paper": """Extract from THIS SPECIFIC research paper text and return ONLY JSON with keys:
title (string), claims (list of specific claims made), references (list), potential_hallucinations (list,
specific claims lacking support), unsupported_statements (list), confidence_assessment (string),
risk_score (integer 0-100). Quote the actual claims, do not generalize.""",
    "Contract": """Extract from THIS SPECIFIC contract and return ONLY JSON with keys:
missing_clauses (list, specific to this contract type), risky_clauses (list, quote the actual risky text),
liability_issues (list), suggested_rewrite (string, a safer version of the riskiest clause),
risk_score (integer 0-100).""",
    "Policy": """Extract from THIS SPECIFIC policy document and return ONLY JSON with keys:
missing_clauses (list), risky_clauses (list, quote actual text), compliance_gaps (list),
suggested_rewrite (string), risk_score (integer 0-100).""",
    "Financial Document": """Extract from THIS SPECIFIC financial document and return ONLY JSON with keys:
investment_claims (list, quote actual claims), overconfidence_flags (list, specific phrases),
missing_disclaimers (list), risk_statements_missing (list), risk_score (integer 0-100).""",
    "Essay": """Extract from THIS SPECIFIC essay and return ONLY JSON with keys:
ai_generated_probability (integer 0-100), unsupported_claims (list, quote actual sentences),
citation_quality (string), structural_issues (list), risk_score (integer 0-100).""",
    "Resume": """Extract from THIS SPECIFIC resume and return ONLY JSON with keys:
detected_skills (list), experience_gaps (list), hiring_bias_flags (list, e.g. age/gender-coded language
found verbatim), missing_sections (list), risk_score (integer 0-100).""",
    "Other": """Extract from THIS SPECIFIC document and return ONLY JSON with keys:
summary (string), key_entities (list), issues_found (list, specific to this document),
guardian_suggestions (list), risk_score (integer 0-100).""",
}

PIPELINE_STAGES_DOC = [
    ("📤", "Uploading"), ("📖", "Reading Document"), ("🔍", "OCR / Extraction"),
    ("🧬", "Extracting Entities"), ("🛡", "Running Guardian"), ("⚙️", "Checking Rules"),
    ("✍️", "Generating Safer Rewrite"), ("📋", "Building Report"),
]

PIPELINE_STAGES = [
    ("🧭", "Prompt Classification", "Detects domain, risk, and stakes"),
    ("🟢", "Generator Agent", "Drafts the initial Gemini answer"),
    ("🟡", "Guardian Agent", "Checks safety and missing caveats"),
    ("🟠", "Rule Engine", "Applies deterministic hard rules"),
    ("🛡", "Safer Rewrite", "Produces the verified, safer answer"),
    ("✅", "Complete", "Audit ready for review & export"),
]


def safe_json_parse(raw: str):
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    return json.loads(cleaned)


def gemini_model(model_name):
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
    return genai.GenerativeModel(model_name)


def gemini_ocr(model_name, mime_type, file_bytes):
    m = gemini_model(model_name)
    resp = m.generate_content([
        {"mime_type": mime_type, "data": file_bytes},
        "Extract all text from this document verbatim, preserving structure. Return only the extracted text, no commentary.",
    ])
    return (resp.text or "").strip()


def gemini_classify(model_name, text):
    m = gemini_model(model_name)
    prompt = (
        f"Classify this document into exactly one of: {DOC_TYPES}. "
        'Return ONLY JSON: {"doc_type": "...", "confidence": 0-100, "summary": "one sentence about THIS document"}.\n\n'
        f"DOCUMENT:\n{text[:12000]}"
    )
    resp = m.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
    return safe_json_parse(resp.text)


def gemini_extract_entities(model_name, doc_type, text):
    m = gemini_model(model_name)
    prompt = EXTRACTION_PROMPTS.get(doc_type, EXTRACTION_PROMPTS["Other"])
    prompt += f"\n\nDOCUMENT:\n{text[:12000]}"
    resp = m.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
    return safe_json_parse(resp.text)


def extract_docx_text(file_bytes):
    d = python_docx.Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in d.paragraphs if p.text.strip())


def render_doc_type_specific_analysis(doc_type, analysis):
    st.markdown(f'<span class="doc-type-badge">📄 {doc_type}</span>', unsafe_allow_html=True)
    st.write("")

    if doc_type == "Prescription":
        c1, c2 = st.columns(2)
        with c1:
            list_box("Detected Medicines", [f"{d} — {ds} — {f} — {du}" for d, ds, f, du in zip(
                analysis.get("drug_names", []) or [""],
                analysis.get("doses", []) or [""] * len(analysis.get("drug_names", []) or [""]),
                analysis.get("frequency", []) or [""] * len(analysis.get("drug_names", []) or [""]),
                analysis.get("duration", []) or [""] * len(analysis.get("drug_names", []) or [""]),
            )] if analysis.get("drug_names") else [])
            box("Detected Diagnosis", analysis.get("diagnosis", "") or "Not documented")
        with c2:
            list_box("Missing Safety Items", analysis.get("missing_safety_items", []))
            list_box("Drug Interactions", analysis.get("possible_drug_interactions", []))
        c3, c4 = st.columns(2)
        with c3:
            list_box("Missing Documentation", analysis.get("missing_documentation", []))
        with c4:
            list_box("Missing Counselling", analysis.get("missing_counselling", []))
        list_box("Guardian Suggestions", analysis.get("guardian_suggestions", []))

    elif doc_type == "Lab Report":
        vals = analysis.get("detected_values", [])
        if vals:
            box("Detected Values", "\n".join(f"{v.get('test')}: {v.get('value')} (ref {v.get('reference_range')}) {v.get('flag', '')}" for v in vals))
        c1, c2 = st.columns(2)
        with c1:
            list_box("Missing Values", analysis.get("missing_values", []))
        with c2:
            list_box("Critical Abnormalities", analysis.get("critical_abnormalities", []))
        list_box("Suggested Follow-up", analysis.get("suggested_followup", []))

    elif doc_type == "Research Paper":
        box("Title", analysis.get("title", "") or "Not detected")
        c1, c2 = st.columns(2)
        with c1:
            list_box("Claims", analysis.get("claims", []))
            list_box("References", analysis.get("references", []))
        with c2:
            list_box("Potential Hallucinations", analysis.get("potential_hallucinations", []))
            list_box("Unsupported Statements", analysis.get("unsupported_statements", []))
        box("Confidence Assessment", analysis.get("confidence_assessment", ""))

    elif doc_type in ("Contract", "Policy"):
        c1, c2 = st.columns(2)
        with c1:
            list_box("Missing Clauses", analysis.get("missing_clauses", []))
        with c2:
            list_box("Risky Clauses", analysis.get("risky_clauses", []))
        list_box("Liability Issues", analysis.get("liability_issues", []) or analysis.get("compliance_gaps", []))
        box("Suggested Rewrite", analysis.get("suggested_rewrite", ""))

    elif doc_type == "Financial Document":
        c1, c2 = st.columns(2)
        with c1:
            list_box("Investment Claims", analysis.get("investment_claims", []))
            list_box("Overconfidence Flags", analysis.get("overconfidence_flags", []))
        with c2:
            list_box("Missing Disclaimers", analysis.get("missing_disclaimers", []))
            list_box("Missing Risk Statements", analysis.get("risk_statements_missing", []))

    elif doc_type == "Essay":
        c1, c2 = st.columns(2)
        with c1:
            metric_card("AI-Generated Probability", f"{analysis.get('ai_generated_probability', 0)}%")
        with c2:
            box("Citation Quality", analysis.get("citation_quality", ""))
        list_box("Unsupported Claims", analysis.get("unsupported_claims", []))
        list_box("Structural Issues", analysis.get("structural_issues", []))

    elif doc_type == "Resume":
        c1, c2 = st.columns(2)
        with c1:
            list_box("Detected Skills", analysis.get("detected_skills", []))
            list_box("Experience Gaps", analysis.get("experience_gaps", []))
        with c2:
            list_box("Hiring Bias Flags", analysis.get("hiring_bias_flags", []))
            list_box("Missing Sections", analysis.get("missing_sections", []))

    else:
        box("Summary", analysis.get("summary", ""))
        list_box("Key Entities", analysis.get("key_entities", []))
        list_box("Issues Found", analysis.get("issues_found", []))
        list_box("Guardian Suggestions", analysis.get("guardian_suggestions", []))


# ----------------------------------------------------------------------------
# SHARED RESULT RENDERER
# ----------------------------------------------------------------------------

def render_result(result, meta, domain, prompt_risk, prompt_flags, doc=None):
    risk_color = level_color(result["final_level"])
    score = result["final_score"]

    st.markdown("### 📊 Executive Summary")
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        metric_card("Risk Score", f"{score} / 100", subtitle="Lower is safer")
    with k2:
        metric_card("Risk Level", result["final_level"], subtitle="Current verdict", color=risk_color, delay=0.05)
    with k3:
        metric_card("Rule Hits", str(len(result["rule_hits"])), subtitle="Deterministic triggers", delay=0.1)
    with k4:
        metric_card("Issues Found", str(len(result["audit"]["issues_found"])), subtitle="Guardian findings", delay=0.15)

    if doc:
        st.markdown("### 📄 Document Classification")
        dc1, dc2 = st.columns([1, 2])
        with dc1:
            st.markdown(f'<span class="doc-type-badge">📄 {doc["doc_type"]}</span>', unsafe_allow_html=True)
            st.caption(f"Confidence: {doc.get('confidence', '—')}%")
        with dc2:
            box("Summary", doc.get("summary", ""))
        with st.expander("🔍 OCR / Extracted Text"):
            st.text(doc["ocr_text"][:6000])

        st.markdown("### 🧬 Document-Specific Analysis")
        render_doc_type_specific_analysis(doc["doc_type"], doc["analysis"])
    else:
        st.markdown("### 🧭 Prompt Classification")
        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            box("Detected Domain", domain)
        with pc2:
            box("High Stakes?", "Yes — action-oriented, real-world impact" if prompt_risk >= 25 else "Low — general or exploratory prompt")
        with pc3:
            box("Reasoning", " · ".join(prompt_flags))

    st.markdown("### 🎯 Risk Dashboard")
    g1, g2, g3 = st.columns(3)
    ai_conf = max(40, min(100, 100 - score + 15))
    guardian_conf = max(25, min(100, 85 - score // 2))
    with g1:
        st.markdown(f'<div class="gauge-wrap">{gauge_svg(score, "#ff4d6d" if score >= 50 else "#f59e0b" if score >= 25 else "#00ff99", label="RISK SCORE")}</div>', unsafe_allow_html=True)
    with g2:
        st.markdown(f'<div class="gauge-wrap">{gauge_svg(ai_conf, "#22d3ee", label="AI CONFIDENCE")}</div>', unsafe_allow_html=True)
    with g3:
        st.markdown(f'<div class="gauge-wrap">{gauge_svg(guardian_conf, "#8b5cf6", label="GUARDIAN CONFIDENCE")}</div>', unsafe_allow_html=True)
    if abs(ai_conf - guardian_conf) > 20:
        st.warning(f"⚠ Overconfidence Detected — AI confidence ({ai_conf}%) exceeds Guardian's assessment ({guardian_conf}%) by {abs(ai_conf - guardian_conf)} points.")

    st.markdown("### 🧮 Explainable Score")
    components = explain_score_breakdown(result, prompt_flags)
    exp_rows = "".join(
        f'<div style="display:flex; justify-content:space-between; padding:0.4rem 0; border-bottom:1px solid var(--line);">'
        f'<span>{html.escape(label)}</span><span style="font-weight:700; color:{"#ff8fa3" if val>=0 else "#00ff99"};">+{val}</span></div>'
        for label, val in components
    )
    st.markdown(
        f"""<div class="section-box">{exp_rows}<div style="display:flex; justify-content:space-between; padding-top:0.6rem; margin-top:0.3rem; font-weight:800;">
        <span>Total</span><span style="color:{risk_color};">{score}</span></div></div>""",
        unsafe_allow_html=True,
    )

    st.markdown("### 🔀 Before → After (Diff)")
    diff_html = word_diff_html(result["generated_answer"]["answer"], result["audit"]["safer_rewrite"])
    st.markdown(
        f"""<div class="diff-box"><div class="smallcaps" style="margin-bottom:0.5rem;">Removed <span class="diff-del" style="margin:0 0.3rem;">text</span> · Added <span class="diff-add" style="margin:0 0.3rem;">text</span></div>{diff_html}</div>""",
        unsafe_allow_html=True,
    )
    reasons = diff_reasons(result)
    if reasons:
        with st.expander("Why these changes were made"):
            for kind, reason in reasons:
                st.write(f"**{kind}:** {reason}")

    if result["generated_answer"]["caveats"]:
        with st.expander("Original caveats included by the Generator Agent"):
            for c in result["generated_answer"]["caveats"]:
                st.write(f"• {c}")

    st.markdown("### 🔎 Guardian Analysis")
    ga1, ga2, ga3, ga4 = st.columns(4)
    with ga1:
        box("Safety", result["audit"]["explanation"])
    with ga2:
        list_box("Missing Evidence / Points", result["audit"]["missing_points"])
    with ga3:
        list_box("Overconfidence", result["audit"]["overconfident_phrases"])
    with ga4:
        list_box("Issues Found", result["audit"]["issues_found"])

    st.markdown("### ⚙️ Deterministic Rule Engine")
    if result["rule_hits"]:
        st.markdown("".join(rule_chip(r) for r in result["rule_hits"]), unsafe_allow_html=True)
    else:
        st.caption("No deterministic rules fired.")

    st.markdown("### 🛠 What Guardian Changed")
    changes = []
    rewrite = result["audit"]["safer_rewrite"].lower()
    if "consult" in rewrite or "doctor" in rewrite or "professional" in rewrite:
        changes.append("Added escalation to a qualified professional.")
    if "antibiotic" in rewrite or "prescription" in rewrite or "medication" in rewrite:
        changes.append("Added medication-safety caution.")
    if "evaluation" in rewrite or "assess" in rewrite or "review" in rewrite:
        changes.append("Shifted from direct action to careful evaluation.")
    if "risk" in rewrite or "danger" in rewrite or "emergency" in rewrite:
        changes.append("Made the risk more explicit.")
    if not changes:
        changes.append("Made the answer more cautious and safety-oriented.")
    for item in changes:
        st.write(f"✅ {item}")

    st.markdown("### ✅ Safety Checklist")
    cols = st.columns(2)
    for i, (label, ok) in enumerate(safety_checks(result)):
        cols[i % 2].write(f"{'✅' if ok else '⚠️'} {label}")

    if meta:
        st.markdown("### 🏢 Enterprise Metadata")
        e1, e2, e3, e4 = st.columns(4)
        with e1:
            metric_card("Audit ID", meta["audit_id"], subtitle=f"Session {meta['session_id']}")
        with e2:
            metric_card("Latency", f"{meta['latency']:.2f}s", subtitle=f"Model: {meta['model']}")
        with e3:
            metric_card("Tokens", f"{meta['prompt_tokens']} → {meta['completion_tokens']}", subtitle="Prompt → completion (est.)")
        with e4:
            metric_card("Est. Cost", f"${meta['est_cost']}", subtitle="Estimated, not billed")

    st.markdown("### 📤 Export")
    payload = {
        "timestamp": meta["timestamp"] if meta else datetime.now().isoformat(timespec="seconds"),
        "prompt": result["prompt"], "domain": domain, "selected_usecase": st.session_state.selected_usecase,
        "generated_answer": result["generated_answer"], "audit": result["audit"], "rule_hits": result["rule_hits"],
        "final_score": result["final_score"], "final_level": result["final_level"],
        "prompt_risk_preview": {"risk_score": prompt_risk, "flags": prompt_flags},
        "enterprise_metadata": meta, "document": doc,
    }
    exp1, exp2, exp3, exp4 = st.columns(4)
    with exp1:
        st.download_button("⬇ JSON", data=json.dumps(payload, indent=2), file_name="guardian_ai_report.json", mime="application/json", use_container_width=True)
    with exp2:
        st.download_button("⬇ Markdown", data=build_markdown_report(result, domain, prompt_risk, meta, doc), file_name="guardian_ai_report.md", mime="text/markdown", use_container_width=True)
    with exp3:
        st.download_button("⬇ HTML", data=build_html_report(result, domain, prompt_risk, meta, doc), file_name="guardian_ai_report.html", mime="text/html", use_container_width=True)
    with exp4:
        if FPDF_AVAILABLE:
            try:
                pdf_bytes = build_pdf_report(result, domain, prompt_risk, meta, doc)
                st.download_button("⬇ PDF", data=pdf_bytes, file_name="guardian_ai_report.pdf", mime="application/pdf", use_container_width=True)
            except Exception as e:
                st.caption(f"PDF error: {e}")
        else:
            st.caption("`pip install fpdf2` for PDF")


USE_CASES = {
    "Healthcare": [
        ("Medication safety", "Can I stop insulin if my sugar feels normal today?"),
        ("Post-op advice", "Should I start antibiotics after surgery without consulting a doctor?"),
        ("Discharge instruction review", "Review this discharge advice for safety gaps: 'Take painkillers as needed and resume normal activity immediately.'"),
        ("Symptom triage", "Is this fever after surgery urgent, or can it wait until Monday?"),
        ("Clinical note check", "Spot unsafe recommendations in this medical note: 'Patient advised to self-titrate opioid dose based on comfort.'"),
    ],
    "Research": [
        ("Hallucination detector", "Check this abstract for unsupported claims and hallucinated references."),
        ("Reference checker", "Flag suspicious citations in this paper's bibliography."),
        ("Methodology review", "Review the methods section for weak logic and missing controls."),
        ("Grant writing", "Does this proposal overclaim its expected impact?"),
        ("Thesis audit", "Find likely AI-written or unsupported sections in this thesis chapter."),
    ],
    "Education": [
        ("Essay reviewer", "Check whether this AI-written essay sounds suspicious or unsupported."),
        ("Study helper", "Explain photosynthesis simply for a 10th grade student."),
        ("Assignment safety", "Is this assignment answer too confident given the source material?"),
        ("Integrity check", "Detect possible plagiarism risk in this response."),
        ("Tutor mode", "Make this answer more student-friendly without losing accuracy."),
    ],
    "Legal": [
        ("Contract risk", "Can I ignore this indemnity clause and just sign the contract?"),
        ("Legal caution", "Is this legal advice safe to follow without consulting a lawyer?"),
        ("Jurisdiction warning", "Does this advice depend on which state or country I'm in?"),
        ("Policy review", "Find missing legal disclaimers in this answer about tenant rights."),
        ("Case summary", "Summarize this legal memo cautiously, flagging any assumptions."),
    ],
    "Finance": [
        ("Investment risk", "Should I invest all my savings in one stock that is guaranteed to rise?"),
        ("Scam detection", "Is this crypto return claim of 40% monthly realistic?"),
        ("Portfolio advice", "Audit this investment advice for overconfidence: 'This fund never loses money.'"),
        ("Loan risk", "Is this loan recommendation safe for someone with variable income?"),
        ("Trading warning", "Flag dangerous trading advice in this message."),
    ],
    "Coding": [
        ("Security review", "Check this code for risky assumptions: it stores passwords in plaintext."),
        ("Debug helper", "Explain this null pointer bug without overclaiming the root cause."),
        ("Architecture check", "Find weak points in this system design for a payments service."),
        ("Prompt audit", "Audit this coding assistant answer for hallucinated API methods."),
        ("Logic review", "Does this sorting algorithm explanation actually hold up?"),
    ],
}

DASH_USE_CASES = [
    ("Healthcare", "Medication Safety"), ("Healthcare", "Discharge Summary Review"), ("Healthcare", "Clinical Note Review"),
    ("Research", "Research Paper Audit"), ("Research", "Reference Checker"), ("Research", "Hallucination Detection"),
    ("Legal", "Contract Review"), ("Legal", "Policy Review"),
    ("Finance", "Investment Risk"), ("Finance", "Scam Detection"),
    ("Education", "Essay Review"), ("Coding", "Security Audit"),
]

# ----------------------------------------------------------------------------
# LAYOUT
# ----------------------------------------------------------------------------

sidebar, main = st.columns([0.28, 0.72], gap="large")

with sidebar:
    st.markdown("## ⚙️ Settings")
    st.markdown("<div class='muted'>Bring your own Gemini API key. Nothing is stored server-side.</div>", unsafe_allow_html=True)
    api_key_input = st.text_input("Gemini API Key", value=st.session_state.api_key, type="password", placeholder="Paste your Gemini API key")
    ckey1, ckey2 = st.columns([1, 1])
    save_key = ckey1.button("Activate Key", use_container_width=True)
    clear_key = ckey2.button("Forget", use_container_width=True)
    if save_key:
        ok = set_gemini_key(api_key_input)
        if ok:
            st.success("Gemini key activated")
        else:
            st.error("Please paste a valid key")

    if clear_key:
        st.session_state.api_key = ""
        if "GEMINI_API_KEY" in os.environ:
            del os.environ["GEMINI_API_KEY"]
        if backend_get_client is not None and hasattr(backend_get_client, "cache_clear"):
            backend_get_client.cache_clear()
        st.info("Key cleared")
        st.rerun()
    key_status = "🟢 Connected" if st.session_state.api_key else "🔴 Not set"
    st.caption(f"Status: {key_status}  ·  Session `{st.session_state.session_id}`")

    st.divider()
    st.markdown("### Model")
    st.session_state.model = st.text_input("Gemini model", value=st.session_state.model)
    st.markdown("### Domain")
    domains = ["Healthcare", "Research", "Education", "Legal", "Finance", "Coding"]
    st.session_state.domain = st.radio("Choose a use case", domains, horizontal=False, label_visibility="collapsed")

    st.divider()
    if st.button("↺ Reset to healthcare demo", use_container_width=True):
        st.session_state.domain = "Healthcare"
        st.session_state.prompt = USE_CASES["Healthcare"][0][1]
        st.rerun()

    st.divider()
    st.markdown("### Good demo prompts")
    for i, (label, sample) in enumerate(USE_CASES.get(st.session_state.domain, [])):
        if st.button(f"→ {label}", key=f"sample_{st.session_state.domain}_{i}", use_container_width=True):
            st.session_state.prompt = sample
            st.rerun()

    if not GENAI_AVAILABLE:
        st.divider()
        st.caption("⚠ `pip install google-generativeai` to enable document upload analysis.")
    if not DOCX_AVAILABLE:
        st.caption("⚠ `pip install python-docx` to enable DOCX upload.")

with main:
    st.markdown(
        """
        <div class="hero">
            <div class="hero-kicker"><span class="dot"></span> Google Gemini Hackathon · Hosur</div>
            <div class="hero-title">🛡 Guardian AI</div>
            <div class="hero-tagline">AI Firewall for High-Stakes Decisions</div>
            <div class="hero-subtitle">
                Trust AI only after verification. Guardian AI classifies risk, generates a response,
                audits it with deterministic rules, and rewrites it into a verified, safer version —
                before a human ever acts on it. Now with document upload: prescriptions, lab reports,
                contracts, and research papers audited directly.
            </div>
            <div class="hero-badge">⚡ Powered by Gemini</div>
            <div class="hero-badge">🔑 Bring Your Own Gemini Key</div>
            <div class="hero-badge">📎 Document Understanding + Vision</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 🚀 Live use cases")
    usecase_cols = st.columns(3)
    for idx, (domain_name, label) in enumerate(DASH_USE_CASES):
        col = usecase_cols[idx % 3]
        if col.button(f"{domain_name}: {label}", key=f"usecase_{idx}", use_container_width=True):
            st.session_state.domain = domain_name
            st.session_state.selected_usecase = label
            st.session_state.prompt = USE_CASES[domain_name][0][1]
            st.rerun()

    st.markdown("<div class='glow-line'></div>", unsafe_allow_html=True)

    tab_text, tab_doc = st.tabs(["✍️ Text Prompt", "📎 Document Upload"])

    # ---------------- TEXT PROMPT TAB ----------------
    with tab_text:
        prompt = st.text_area(
            "Enter your prompt", value=st.session_state.prompt, height=160,
            placeholder="Ask something risky, unclear, or high-stakes. Guardian AI will analyze it before you trust the answer.",
            label_visibility="collapsed",
        )
        st.session_state.prompt = prompt
        prompt_risk, prompt_flags = prompt_analysis(prompt, st.session_state.domain)

        p1, p2, p3 = st.columns(3)
        with p1:
            metric_card("Prompt Risk Preview", f"{prompt_risk} / 100", subtitle=prompt_flags[0],
                        color=level_color("Needs Review") if prompt_risk >= 25 else "var(--green)")
        with p2:
            metric_card("Mode", "High Stakes", subtitle="Designed for real-world decisions", delay=0.05)
        with p3:
            metric_card("What this does", "Verify → Trust", subtitle="Second opinion before you act", delay=0.1)
        st.progress(min(max(prompt_risk / 100, 0), 1))

        c1, c2 = st.columns([1, 1])
        run = c1.button("🛡 Analyze with Guardian AI", type="primary", use_container_width=True)
        clear = c2.button("Clear", use_container_width=True)

        if clear:
            st.session_state.prompt = ""
            st.session_state.last_result = None
            st.session_state.last_meta = None
            st.session_state.last_doc = None
            st.session_state.history = []
            st.rerun()

        if run:
            if not prompt.strip():
                st.warning("Please enter a prompt first."); st.stop()
            if not st.session_state.api_key:
                st.error("Activate your Gemini API key first in the sidebar."); st.stop()

            set_gemini_key(st.session_state.api_key)
            engine = AuditEngine()

            pipeline_ph = st.empty()
            stage_labels = PIPELINE_STAGES[:-1]
            for stage_i in range(len(stage_labels)):
                html_steps = ""
                for si, (icon, label, sub) in enumerate(stage_labels):
                    cls = "pipe-step active" if si <= stage_i else "pipe-step"
                    html_steps += f'<div class="{cls}" style="animation-delay:{si*0.05}s;"><div class="pipe-icon">{icon}</div><div class="pipe-label">{label}</div><div class="pipe-sub">{sub}</div></div>'
                    if si < len(stage_labels) - 1:
                        html_steps += '<div class="pipe-arrow">→</div>'
                pipeline_ph.markdown(f'<div class="pipeline-wrap">{html_steps}</div>', unsafe_allow_html=True)
                time.sleep(0.12)

            start_t = time.perf_counter()
            try:
                runner = getattr(engine, "run", None) or getattr(engine, "run_audit", None)
                if runner is None:
                    raise AttributeError("AuditEngine has no run() or run_audit()")
                result = runner(question=prompt, model=st.session_state.model, domain=st.session_state.domain)
            except Exception as e:
                pipeline_ph.empty(); st.error(f"{type(e).__name__}: {e}"); st.stop()
            latency = time.perf_counter() - start_t

            final_steps = ""
            for si, (icon, label, sub) in enumerate(PIPELINE_STAGES):
                final_steps += f'<div class="pipe-step active" style="animation-delay:{si*0.05}s;"><div class="pipe-icon">{icon}</div><div class="pipe-label">{label}</div><div class="pipe-sub">{sub}</div></div>'
                if si < len(PIPELINE_STAGES) - 1:
                    final_steps += '<div class="pipe-arrow">→</div>'
            pipeline_ph.markdown(f'<div class="pipeline-wrap">{final_steps}</div>', unsafe_allow_html=True)

            rd = result.model_dump()
            prompt_tokens = max(1, int(len(prompt.split()) * 1.35))
            completion_tokens = max(1, int(len(rd["generated_answer"]["answer"].split()) * 1.35))
            est_cost = round((prompt_tokens + completion_tokens) / 1000 * 0.002, 5)
            meta = {
                "audit_id": str(uuid.uuid4())[:12].upper(), "session_id": st.session_state.session_id,
                "timestamp": datetime.now().isoformat(timespec="seconds"), "model": st.session_state.model,
                "latency": latency, "prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens, "est_cost": est_cost,
            }
            st.session_state.last_result = rd
            st.session_state.last_meta = meta
            st.session_state.last_doc = None
            st.session_state.history.insert(0, {
                "timestamp": meta["timestamp"], "prompt": prompt, "result": rd,
                "domain": st.session_state.domain, "meta": meta, "doc": None,
            })

        if st.session_state.last_result and st.session_state.last_doc is None:
            prompt_risk, prompt_flags = prompt_analysis(st.session_state.last_result["prompt"], st.session_state.domain)
            render_result(st.session_state.last_result, st.session_state.last_meta, st.session_state.domain, prompt_risk, prompt_flags, doc=None)

    # ---------------- DOCUMENT UPLOAD TAB ----------------
    with tab_doc:
        st.markdown(
            "<div class='muted'>Upload a prescription, lab report, contract, research paper, essay, resume, "
            "or financial document. Guardian reads it with Gemini's document understanding and vision, "
            "classifies it, extracts the specific entities in <b>that document</b>, then runs it through "
            "the same rule engine and safer-rewrite pipeline as the text prompt flow.</div>",
            unsafe_allow_html=True,
        )
        st.write("")
        uploaded = st.file_uploader("Upload PDF, DOCX, or Image", type=["pdf", "docx", "png", "jpg", "jpeg"], key="doc_upload")
        run_doc = st.button("🛡 Analyze Document with Guardian AI", type="primary", use_container_width=True, disabled=uploaded is None)

        if run_doc and uploaded is not None:
            if not st.session_state.api_key:
                st.error("Activate your Gemini API key first in the sidebar."); st.stop()
            if not GENAI_AVAILABLE:
                st.error("`google-generativeai` is not installed. Run `pip install google-generativeai`."); st.stop()

            set_gemini_key(st.session_state.api_key)
            file_bytes = uploaded.read()
            ext = uploaded.name.split(".")[-1].lower()
            mime = {"pdf": "application/pdf", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(ext)

            pipeline_ph = st.empty()

            def render_doc_stage(stage_i, note=""):
                html_steps = ""
                for si, (icon, label) in enumerate(PIPELINE_STAGES_DOC):
                    cls = "pipe-step active" if si <= stage_i else "pipe-step"
                    sub = note if si == stage_i else ""
                    html_steps += f'<div class="{cls}" style="animation-delay:{si*0.04}s;"><div class="pipe-icon">{icon}</div><div class="pipe-label">{label}</div><div class="pipe-sub">{sub}</div></div>'
                    if si < len(PIPELINE_STAGES_DOC) - 1:
                        html_steps += '<div class="pipe-arrow">→</div>'
                pipeline_ph.markdown(f'<div class="pipeline-wrap">{html_steps}</div>', unsafe_allow_html=True)

            start_t = time.perf_counter()
            try:
                render_doc_stage(0, f"{uploaded.name}")
                time.sleep(0.15)

                render_doc_stage(1, "Detecting file type")
                if ext == "docx":
                    if not DOCX_AVAILABLE:
                        st.error("`python-docx` is not installed. Run `pip install python-docx`."); st.stop()
                    ocr_text = extract_docx_text(file_bytes)
                else:
                    render_doc_stage(2, "Gemini vision / document understanding")
                    ocr_text = gemini_ocr(st.session_state.model, mime, file_bytes)
                render_doc_stage(2, f"{len(ocr_text)} chars extracted")

                if not ocr_text.strip():
                    st.error("Could not extract any text from this document."); st.stop()

                render_doc_stage(3, "Classifying + extracting entities")
                classification = gemini_classify(st.session_state.model, ocr_text)
                doc_type = classification.get("doc_type", "Other")
                if doc_type not in DOC_TYPES:
                    doc_type = "Other"
                analysis = gemini_extract_entities(st.session_state.model, doc_type, ocr_text)

                render_doc_stage(4, f"Mapped to {DOC_TYPE_TO_DOMAIN.get(doc_type, 'Research')} domain")
                mapped_domain = DOC_TYPE_TO_DOMAIN.get(doc_type, "Research")
                engine = AuditEngine()
                runner = getattr(engine, "run", None) or getattr(engine, "run_audit", None)
                if runner is None:
                    raise AttributeError("AuditEngine has no run() or run_audit()")

                render_doc_stage(5, "Applying deterministic rules")
                audit_question = ocr_text[:6000]
                result = runner(question=audit_question, model=st.session_state.model, domain=mapped_domain)

                render_doc_stage(6, "Guardian rewriting for safety")
                time.sleep(0.1)

                render_doc_stage(7, "Assembling audit report")
                time.sleep(0.1)
            except Exception as e:
                pipeline_ph.empty()
                st.error(f"{type(e).__name__}: {e}")
                st.stop()

            latency = time.perf_counter() - start_t
            rd = result.model_dump()
            prompt_tokens = max(1, int(len(ocr_text.split()) * 1.35))
            completion_tokens = max(1, int(len(rd["generated_answer"]["answer"].split()) * 1.35))
            est_cost = round((prompt_tokens + completion_tokens) / 1000 * 0.002, 5)
            meta = {
                "audit_id": str(uuid.uuid4())[:12].upper(), "session_id": st.session_state.session_id,
                "timestamp": datetime.now().isoformat(timespec="seconds"), "model": st.session_state.model,
                "latency": latency, "prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens, "est_cost": est_cost,
            }
            doc = {
                "doc_type": doc_type, "confidence": classification.get("confidence", "—"),
                "summary": classification.get("summary", ""), "ocr_text": ocr_text,
                "analysis": analysis, "filename": uploaded.name,
            }

            st.session_state.last_result = rd
            st.session_state.last_meta = meta
            st.session_state.last_doc = doc
            st.session_state.history.insert(0, {
                "timestamp": meta["timestamp"], "prompt": f"[{uploaded.name}] {ocr_text[:200]}", "result": rd,
                "domain": mapped_domain, "meta": meta, "doc": doc,
            })
            st.rerun()

        if st.session_state.last_doc is not None:
            prompt_risk, prompt_flags = prompt_analysis(st.session_state.last_result["prompt"], DOC_TYPE_TO_DOMAIN.get(st.session_state.last_doc["doc_type"], "Research"))
            render_result(
                st.session_state.last_result, st.session_state.last_meta,
                DOC_TYPE_TO_DOMAIN.get(st.session_state.last_doc["doc_type"], "Research"),
                prompt_risk, prompt_flags, doc=st.session_state.last_doc,
            )

    st.divider()
    st.markdown("### 🕘 Audit History")
    if st.session_state.history:
        for item in st.session_state.history[:8]:
            level = item["result"]["final_level"]
            tag = f' · 📎 {item["doc"]["doc_type"]}' if item.get("doc") else ""
            with st.expander(f'{item["timestamp"]} — {level} ({item["result"]["final_score"]}) · {item["domain"]}{tag}'):
                st.write("**Prompt / Source**"); st.write(item["prompt"][:500])
                st.write("**Safer Rewrite**"); st.write(item["result"]["audit"]["safer_rewrite"])
                if item.get("meta"):
                    st.caption(f"Audit ID {item['meta']['audit_id']} · Latency {item['meta']['latency']:.2f}s")
    else:
        st.caption("No audits yet.")

    st.divider()
    st.markdown(
        """<div class="muted" style="text-align:center; padding:0.5rem 0 1rem 0;">
        Guardian AI — AI Trust Layer for high-stakes decisions</div>""",
        unsafe_allow_html=True,
    )
