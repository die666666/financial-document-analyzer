<div align="center">

```
Financial Document Analyzer using CrewAI

```

**A multi-agent AI system that turns financial PDFs into structured investment intelligence.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![CrewAI](https://img.shields.io/badge/CrewAI-Multi--Agent-FF6B6B?style=flat-square)](https://crewai.com)
[![Groq](https://img.shields.io/badge/Groq-Free_Tier-F55036?style=flat-square)](https://groq.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

</div>

---

## What It Does

Upload any financial PDF — earnings releases, 10-K/10-Q filings, balance sheets — and get back a complete structured report from four specialist AI agents working in sequence:

```
📄 PDF Upload
     │
     ▼
┌─────────────────────┐
│  🔍 VERIFIER        │  Confirms it's a real financial document
│  Document Check     │  Returns PASS / FAIL with evidence
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  📊 ANALYST         │  Extracts revenue, net income, EPS,
│  Financial Metrics  │  margins, YoY growth
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  💼 ADVISOR         │  Bullish / Neutral / Bearish outlook
│  Investment View    │  with evidence and risk disclosure
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  ⚠️  RISK ASSESSOR  │  Scores leverage, liquidity,
│  Risk Rating        │  cash flow → LOW / MODERATE / HIGH
└─────────────────────┘
          │
          ▼
     📋 Full Report
```

---

## Quick Start

### 1 — Prerequisites
- Python 3.11+
- A free [Groq API key](https://console.groq.com/keys) (no credit card needed)

### 2 — Clone & Install

```bash
git clone https://github.com/die666666/financial-document-analyzer.git
cd financial-document-analyzer

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

pip install fastapi uvicorn crewai crewai-tools pypdf python-dotenv litellm
```

### 3 — Configure

```bash
# Create your .env file
python -c "open('.env', 'w', encoding='utf-8').write('GROQ_API_KEY=your_key_here\n')"
```

Get your key from [console.groq.com/keys](https://console.groq.com/keys) — it's free.

### 4 — Run

```bash
uvicorn main:app --reload
```

Open **http://127.0.0.1:8000/docs** → try it in the browser.

---

## API Reference

### `GET /`
Health check.
```json
{ "message": "Financial Document Analyzer API is running" }
```

---

### `POST /analyze`

Analyze a financial PDF document.

**Request** — `multipart/form-data`

| Field | Type | Required | Default |
|---|---|---|---|
| `file` | PDF | ✅ | — |
| `query` | string | ❌ | `"Analyze this financial document for investment insights"` |

**Success Response** — `200`
```json
{
  "status": "success",
  "query": "Analyze this document for investment insights",
  "analysis": "...full report from all 4 agents...",
  "file_processed": "TSLA-Q2-2025.pdf"
}
```

**Error Responses**

| Code | Meaning |
|---|---|
| `400` | File is not a PDF |
| `500` | Error during analysis — check terminal for traceback |
| `504` | Timed out — try a shorter query or smaller document |

**Example — curl**
```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -F "file=@TSLA-Q2-2025.pdf" \
  -F "query=Is Tesla a good investment right now?"
```

**Example — Python**
```python
import requests

with open("TSLA-Q2-2025.pdf", "rb") as f:
    r = requests.post(
        "http://127.0.0.1:8000/analyze",
        files={"file": ("TSLA-Q2-2025.pdf", f, "application/pdf")},
        data={"query": "Summarize the key financial risks"}
    )

print(r.json()["analysis"])
```

---

## Bugs Fixed

This project was submitted with **17 bugs** across 4 files. Every one was identified and fixed.

### `tools.py` — 8 bugs

| # | Bug | Fix |
|---|---|---|
| 1 | `PdfReader(file_path=path)` — invalid keyword arg | `PdfReader(path)` (positional) |
| 2 | `.load()` called on PdfReader — method doesn't exist | `reader.pages` + `.extract_text()` |
| 3 | `data.page_content` — LangChain attribute on a pypdf object | `page.extract_text()` |
| 4 | `async def` on tool methods — incompatible with `@tool` | Removed `async` |
| 5 | Missing `@staticmethod` — no `self` param on instance methods | Added to all 3 tool classes |
| 6 | Missing `@tool` decorator — CrewAI couldn't discover tools | Added `@tool(...)` to all methods |
| 7 | Broken whitespace loop — Python strings are immutable | `" ".join(data.split())` |
| 8 | No token limit on PDF extraction | Added `MAX_WORDS` cap |

### `agents.py` — 6 bugs

| # | Bug | Fix |
|---|---|---|
| 1 | `from crewai.agents import Agent` — wrong import path | `from crewai import Agent` |
| 2 | `llm = llm` — NameError, never defined | `crewai.LLM` with Groq API |
| 3 | `tool=[...]` — wrong parameter name | `tools=[...]` |
| 4 | `memory=True` — requires OpenAI embeddings, crashes with Groq | `memory=False` |
| 5 | `allow_delegation=True` — agents called each other in loops, exploding token usage | `allow_delegation=False` |
| 6 | All goals/backstories instructed fabrication, fake credentials, ignoring regulations | Fully rewritten to be ethical and professional |

### `task.py` — 5 bugs

| # | Bug | Fix |
|---|---|---|
| 1 | 3/4 tasks had `agent=financial_analyst` — wrong agent | Each task now uses its correct specialist |
| 2 | Wrong tools on 2 tasks (`FinancialDocumentTool` used everywhere) | `InvestmentTool` and `RiskTool` assigned correctly |
| 3 | `investment_advisor`, `risk_assessor` never imported | Added missing imports |
| 4 | All task descriptions instructed fabricating data, ignoring the query, approving everything | Rewritten with clear, honest, concise instructions |
| 5 | Task descriptions too long — caused token limit errors on every request | Shortened significantly |

### `main.py` — 7 bugs

| # | Bug | Fix |
|---|---|---|
| 1 | Route named `analyze_financial_document` — same as imported task, silently overwrote it | Renamed route to `analyze_document` |
| 2 | `run_crew()` called directly inside `async` route — blocked FastAPI event loop | Moved to `ThreadPoolExecutor` |
| 3 | `file_path` never passed into `kickoff()` — 500 on every real request | Added to kickoff inputs |
| 4 | Only 1 agent and 1 task in crew | All 4 agents and 4 tasks added |
| 5 | `bare except: pass` — swallowed `KeyboardInterrupt` | Scoped to `except OSError` |
| 6 | `reload=True` in `__main__` — `RuntimeError` on Windows | Removed (use CLI flag instead) |
| 7 | No PDF validation | Added `.pdf` check returning HTTP 400 |

---

## Project Structure

```
financial-document-analyzer/
├── main.py        ← FastAPI app + crew orchestration
├── agents.py      ← 4 CrewAI agent definitions
├── task.py        ← 4 CrewAI task definitions
├── tools.py       ← PDF reader, investment & risk tools
├── .env           ← Your Groq API key (never commit this)
├── .gitignore
└── README.md
```



<div align="center">

Built with [CrewAI](https://crewai.com) · [FastAPI](https://fastapi.tiangolo.com) · [Groq](https://groq.com) · [pypdf](https://pypdf.readthedocs.io)

</div>
