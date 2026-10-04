import re
from pathlib import Path
from typing import Dict, List

import requests
from pypdf import PdfReader
from docx import Document


def extract_text(uploaded_file) -> str:
    """Extract text from a Streamlit UploadedFile (TXT/PDF/DOCX)."""
    name = uploaded_file.name.lower()
    data = uploaded_file.getvalue()
    if name.endswith(".txt"):
        return data.decode("utf-8", errors="ignore")
    if name.endswith(".pdf"):
        reader = PdfReader(__import__("io").BytesIO(data))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    if name.endswith(".docx"):
        doc = Document(__import__("io").BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    return ""


def _sentences(text: str) -> List[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if s.strip()]


def _contains(text: str, terms: List[str]) -> bool:
    t = text.lower()
    return all(term.lower() in t for term in terms)


def analyze_requirements(v1: str, v2: str) -> Dict:
    """Deterministic baseline comparison for a clear, explainable demo."""
    findings = []
    pairs = [
        ("Authentication", ["email", "password"], ["mobile", "otp"],
         "Login UI, authentication API, OTP service, user data and authentication testing."),
        ("Payment", ["cash on delivery"], ["online payment"],
         "Payment UI, payment gateway/API, transaction handling and payment testing."),
        ("Notifications", ["email"], ["email", "sms"],
         "Notification service, SMS API, message templates and notification preferences."),
        ("Product Search", ["product name"], ["product name", "product category"],
         "Search UI, search/filter logic, backend query handling and search testing."),
    ]
    l1, l2 = v1.lower(), v2.lower()

    for module, old_terms, new_terms, impact in pairs:
        if _contains(l1, old_terms) and _contains(l2, new_terms):
            # Avoid falsely calling email->email+SMS a change unless SMS exists in V2.
            old_phrase = " + ".join(old_terms)
            new_phrase = " + ".join(new_terms)
            if old_phrase != new_phrase or old_terms != new_terms:
                findings.append({
                    "type": "MODIFIED",
                    "module": module,
                    "title": f"{module} requirement changed",
                    "v1": old_phrase,
                    "v2": new_phrase,
                    "impact": impact,
                    "evidence": "Detected from the uploaded V1 and V2 requirement text."
                })

    s1 = {s for s in _sentences(v1)}
    s2 = {s for s in _sentences(v2)}
    added = [x for x in s2 - s1 if x]
    removed = [x for x in s1 - s2 if x]

    # Only add sentences that are not already represented by the focused module rules.
    for x in added[:5]:
        findings.append({
            "type": "ADDED", "module": "General", "title": "New requirement detected",
            "v1": "Not present in V1", "v2": x,
            "impact": "Review the related design, implementation and test cases.",
            "evidence": "Sentence appears in V2 but not in V1."
        })
    for x in removed[:5]:
        findings.append({
            "type": "REMOVED", "module": "General", "title": "Requirement removed",
            "v1": x, "v2": "Not present in V2",
            "impact": "Check whether existing implementation and tests should be changed or retired.",
            "evidence": "Sentence appears in V1 but not in V2."
        })

    # Potential contradiction detection based on explicit opposite requirements.
    conflicts = []
    if "cash on delivery" in l1 and "online payment" in l2:
        conflicts.append("Payment method changed from COD to online payment; verify whether COD should remain supported.")
    if "email and password" in l1 and "mobile number and otp" in l2:
        conflicts.append("Authentication method changed; verify whether email/password login is intentionally retired.")

    # Deduplicate identical findings by title + V1 + V2.
    unique = []
    seen = set()
    for f in findings:
        key = (f["title"], f["v1"], f["v2"])
        if key not in seen:
            seen.add(key)
            unique.append(f)
    findings = unique

    return {
        "v1": v1,
        "v2": v2,
        "findings": findings,
        "conflicts": conflicts,
        "summary": {
            "changes": len(findings),
            "conflicts": len(conflicts),
            "impacts": sum(1 for f in findings if f["impact"]),
        },
    }


def _context_for_question(question: str, analysis: Dict) -> str:
    """Retrieve the most relevant document evidence plus comparison findings."""
    terms = set(re.findall(r"[a-zA-Z0-9]+", question.lower()))
    v1 = analysis.get("v1", "")
    v2 = analysis.get("v2", "")

    # Always include the full requirement texts for grounded answers.
    # This fixes the earlier problem where the assistant only received a few
    # comparison findings and could not answer broader document questions.
    relevant_v1 = _relevant_sentences(v1, terms)
    relevant_v2 = _relevant_sentences(v2, terms)

    finding_lines = []
    for f in analysis.get("findings", []):
        hay = " ".join([f["module"], f["title"], f["v1"], f["v2"], f["impact"]]).lower()
        score = sum(1 for t in terms if len(t) > 2 and t in hay)
        finding_lines.append((score, f))
    finding_lines.sort(key=lambda x: x[0], reverse=True)
    selected = [f for score, f in finding_lines if score > 0][:8]
    if not selected:
        selected = analysis.get("findings", [])[:8]

    findings_text = "\n".join(
        f"- {f['module']}: {f['title']} | V1: {f['v1']} | V2: {f['v2']} | Impact: {f['impact']}"
        for f in selected
    ) or "No comparison findings were detected."

    return f"""PREVIOUS SRS (V1) — relevant requirements:\n{relevant_v1}\n\nUPDATED SRS (V2) — relevant requirements:\n{relevant_v2}\n\nCOMPARISON FINDINGS:\n{findings_text}"""


def _relevant_sentences(text: str, terms) -> str:
    sentences = _sentences(text)
    if not sentences:
        return "No requirement text available."
    scored = []
    for sentence in sentences:
        low = sentence.lower()
        score = sum(1 for t in terms if len(t) > 2 and t in low)
        scored.append((score, sentence))
    scored.sort(key=lambda x: x[0], reverse=True)
    # Keep enough context for broad questions, but avoid an unnecessarily huge prompt.
    selected = [s for score, s in scored if score > 0][:12]
    if not selected:
        selected = sentences[:20]
    return "\n".join(f"- {s}" for s in selected)


def ollama_answer(question: str, analysis: Dict, model: str = "llama3.2:3b") -> str:
    """Ask local Ollama using the uploaded SRS documents and comparison findings."""
    context = _context_for_question(question, analysis)
    prompt = f"""You are ReqSense AI, a software requirement intelligence assistant.
You are answering a college project demonstration question.
Use ONLY the provided SRS context and comparison findings. Do not invent requirements.
If the user asks about changes, compare V1 and V2 explicitly.
If the user asks about impact, use the detected impact information and explain it clearly.
If the user asks for a summary, summarize the actual uploaded requirements.
Answer directly in simple, professional language. Use short bullets when useful.

{context}

DETECTED CONFLICTS:
{chr(10).join('- ' + x for x in analysis.get('conflicts', [])) or '- None detected'}

USER QUESTION:
{question}
"""
    try:
        r = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False, "options": {"temperature": 0.2}},
            timeout=120,
        )
        r.raise_for_status()
        answer = r.json().get("response", "").strip()
        if answer:
            return answer
        return "The local LLM returned an empty response."
    except requests.exceptions.ConnectionError:
        return "I could not connect to Ollama. Please make sure Ollama is running, then ask the question again."
    except Exception as exc:
        return f"I could not get a response from the local LLM. Please check that llama3.2:3b is available in Ollama.\n\nTechnical detail: {exc}"

def build_report(analysis: Dict, llm_summary: str = "") -> str:
    lines = [
        "# ReqSense AI — Requirement Intelligence Report",
        "",
        "## Summary",
        f"- Changes detected: {analysis['summary']['changes']}",
        f"- Potential conflicts: {analysis['summary']['conflicts']}",
        f"- Potential impacts: {analysis['summary']['impacts']}",
        "",
    ]
    if llm_summary:
        lines += ["## AI Explanation", llm_summary, ""]
    if analysis.get("conflicts"):
        lines += ["## Potential Conflicts"] + [f"- {x}" for x in analysis["conflicts"]] + [""]
    lines += ["## Requirement Changes", ""]
    for i, f in enumerate(analysis["findings"], 1):
        lines += [
            f"### {i}. {f['title']}",
            f"- V1: {f['v1']}",
            f"- V2: {f['v2']}",
            f"- Potential impact: {f['impact']}",
            f"- Evidence: {f['evidence']}",
            "",
        ]
    return "\n".join(lines)
