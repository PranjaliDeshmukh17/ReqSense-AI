# ReqSense-AI
AI-Powered Software Requirement Intelligence Agent using LLM, RAG and Agentic AI
# ReqSense AI — AI-Powered Software Requirement Intelligence Agent

## What this version does
1. Upload Previous SRS (V1) and Updated SRS (V2) in **Documents**.
2. The app automatically extracts the document text.
3. **Requirement Analysis** automatically shows the extracted V1 and V2. No duplicate copy-pasting is required.
4. The app detects requirement changes, potential conflicts, and affected areas.
5. **AI Assistant** answers questions using the analyzed requirement context.
6. **Reports** generates a downloadable Markdown report with the findings and an LLM explanation.

## AI / RAG / Agentic explanation
- **LLM:** Llama 3.2 3B via Ollama generates natural-language explanations.
- **RAG:** the app retrieves relevant requirement findings from the uploaded documents and supplies that context to the LLM.
- **Requirement analysis:** deterministic comparison identifies changes and potential impacts.
- **Agentic workflow:** the application coordinates document extraction → comparison → conflict/impact checks → LLM explanation → report generation.

## Run on Windows
Open PowerShell in this folder:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Ollama should be installed and the model should be available:

```powershell
ollama pull llama3.2:3b
```

You normally do not need to enter an API key. Ollama runs locally.

## Test documents
Use the files in `data/`:
- `sample_v1.txt`
- `sample_v2.txt`

## Demo questions
After analysis, open **AI Assistant** and ask:
- What changed in authentication?
- Which modules are affected?
- What changed in payment?
- Are there any conflicts?
- Summarize the important changes.

## Important UI note
The interface is intentionally dark. Text areas, pasted text, chat input, upload areas, buttons, alerts, and sidebar are styled with dark backgrounds and light text so pasted content remains visible.

