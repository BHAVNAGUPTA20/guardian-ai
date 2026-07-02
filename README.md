# 🛡️ Guardian AI
### AI Firewall for High-Stakes Decisions

Guardian AI is an AI safety firewall that verifies, audits, and rewrites AI-generated responses before they are acted upon in high-risk domains such as healthcare, legal, finance, research, education, and software engineering.

Unlike traditional chatbots, Guardian AI does not simply generate answers. It performs a second layer of deterministic safety verification to identify hallucinations, missing safeguards, overconfidence, missing evidence, unsafe recommendations, and domain-specific risks before presenting a safer response.

Built for the **Google Gemini Hackathon**.

---

# 🚀 Features

- AI Response Safety Audit
- Deterministic Rule Engine
- Hallucination Detection
- Missing Evidence Detection
- Explainable Risk Scoring
- Confidence Analysis
- Before → After Response Comparison
- Document Upload & OCR
- Prescription Review
- Research Paper Audit
- Clinical Note Review
- Discharge Summary Review
- Legal Contract Review
- Policy Review
- Essay Review
- Investment Risk Review
- Secure BYO Gemini API Key

---

# 📄 Document Intelligence

Guardian AI supports:

- PDF
- DOCX
- Images
- Prescriptions
- Research Papers
- Clinical Notes
- Legal Contracts
- Policies
- Essays

The system automatically

- extracts text
- classifies the document
- detects important entities
- performs domain-specific analysis
- identifies missing safety items
- detects interactions
- explains every modification

---

# 🧠 How It Works

```
User Prompt / Document
          │
          ▼
    Gemini Generation
          │
          ▼
 Guardian AI Rule Engine
          │
 ├── Risk Detection
 ├── Missing Evidence
 ├── Hallucination Checks
 ├── Domain Rules
 ├── Safety Audit
 └── Rewrite Engine
          │
          ▼
 Explainable Safe Output
```

---

# 🏥 Supported Domains

- Healthcare
- Research
- Education
- Legal
- Finance
- Software Engineering

---

# 📊 Dashboard

Guardian AI produces:

- Executive Summary
- Risk Score
- Explainable Score
- Confidence Levels
- Rule Hits
- Missing Safety Items
- Drug Interactions
- Missing Documentation
- Missing Counselling
- Guardian Suggestions
- Before → After Diff
- Final Safe Response

---

# 🔒 Why Guardian AI?

Large Language Models are powerful, but they can:

- hallucinate
- omit important information
- sound overconfident
- provide unsafe advice
- miss critical warnings

Guardian AI acts as an **AI Firewall**, ensuring AI responses are verified before users rely on them.

---

# ⚙️ Tech Stack

- Python
- Streamlit
- Google Gemini
- Google AI Studio API
- OCR
- Deterministic Rule Engine
- Docker
- Docker Compose
- GitHub

---

# 📦 Installation

Clone the repository

```bash
git clone https://github.com/BHAVNAGUPTA20/guardian-ai.git
```

Install dependencies

```bash
pip install -r requirements.txt
```

Create a `.env`

```text
GEMINI_API_KEY=YOUR_API_KEY
```

Run

```bash
streamlit run app.py
```

---

# 📁 Project Structure

```
guardian-ai/

├── agents/
├── backend/
├── utils/
├── app.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

# 🎯 Future Roadmap

- Multi-agent verification
- Retrieval-Augmented Verification (RAG)
- Medical guideline integration
- PubMed evidence retrieval
- FHIR/EHR integration
- Audit logs
- Enterprise deployment
- Human approval workflows
- Explainable AI dashboard
- API version

---

# 👩‍⚕️ Author

**Dr. Bhavna Gupta**

AI • Healthcare • Patient Safety • Clinical Decision Support

GitHub:
https://github.com/BHAVNAGUPTA20

---

# 📜 License

MIT License

---

> **Guardian AI** — Trust AI only after verification.
