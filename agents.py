## Importing libraries and files
import os
from dotenv import load_dotenv
load_dotenv()

from crewai import Agent, LLM
from tools import search_tool, FinancialDocumentTool, InvestmentTool, RiskTool

### Loading LLM — Groq API
from crewai import LLM

llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.2,
)


# ── Agent 1: Financial Analyst ───────────────────────────────────────────────
financial_analyst = Agent(
    role="Senior Financial Analyst",
    goal=(
        "Provide accurate, evidence-based investment analysis for the query: {query}. "
        "Base all conclusions strictly on the content of the financial documents provided. "
        "Clearly state assumptions, limitations, and any uncertainties in your analysis."
    ),
    verbose=True,
    memory=False,           # Fix: memory=True requires OpenAI embeddings internally —
                            # causes 'OPENAI_API_KEY is required' error with Groq
    backstory=(
        "You are a CFA charterholder with 15 years of experience in equity research and "
        "fundamental analysis at a tier-1 asset management firm. You read financial reports "
        "thoroughly and base every recommendation on verified data. You are careful to "
        "distinguish between what the numbers show and what is speculative. You always "
        "remind users that past performance does not guarantee future results, and you "
        "operate strictly within regulatory and ethical guidelines."
    ),
    tools=[FinancialDocumentTool.read_data_tool],
    llm=llm,
    max_iter=3,             # Fix: was 5 — each iteration costs tokens; 3 is enough
    max_rpm=3,              # Fix: was 10 — Groq free tier is ~30 RPM total across all
                            # agents; dividing by 4 agents gives ~7, use 3 to be safe
    allow_delegation=False  # Fix: was True — delegation causes agents to call each
                            # other repeatedly, multiplying token usage and hitting
                            # rate limits almost immediately on the free tier
)


# ── Agent 2: Document Verifier ───────────────────────────────────────────────
verifier = Agent(
    role="Financial Document Verifier",
    goal=(
        "Carefully verify that uploaded documents are legitimate financial reports "
        "(e.g. earnings releases, 10-K/10-Q filings, balance sheets). "
        "Confirm the document's structure, completeness, and consistency before passing "
        "it to downstream agents. Reject or flag any document that does not meet these criteria."
    ),
    verbose=True,
    memory=False,           # Fix: same as above — memory=True requires OpenAI
    backstory=(
        "You are a former financial compliance officer with deep experience in SEC filing "
        "standards, GAAP/IFRS reporting requirements, and document authenticity review. "
        "You read every document carefully before approving it for analysis. You flag "
        "inconsistencies, missing disclosures, and non-standard formatting. Accuracy and "
        "regulatory compliance are your top priorities."
    ),
    tools=[FinancialDocumentTool.read_data_tool],
    llm=llm,
    max_iter=3,
    max_rpm=3,
    allow_delegation=False  # Fix: same as above — no delegation on free tier
)


# ── Agent 3: Investment Advisor ──────────────────────────────────────────────
investment_advisor = Agent(
    role="Registered Investment Advisor",
    goal=(
        "Provide objective, suitability-based investment recommendations grounded in the "
        "financial document analysis. Consider the investor's risk profile, time horizon, "
        "and the actual financial health of the company. Always disclose risks clearly and "
        "recommend strategies that align with the client's documented financial goals."
    ),
    verbose=True,
    memory=False,           # Fix: same as above
    backstory=(
        "You are a Registered Investment Advisor (RIA) registered with the SEC, with a "
        "fiduciary duty to act in your clients' best interests at all times. You have 12 "
        "years of experience in portfolio construction and wealth management. You base "
        "recommendations strictly on documented financial data and established valuation "
        "frameworks. You clearly disclose all fees, conflicts of interest, and relevant "
        "risks, and you do not recommend products for which you receive undisclosed "
        "compensation. You always comply with FINRA and SEC regulations."
    ),
    tools=[InvestmentTool.analyze_investment_tool],
    llm=llm,
    max_iter=3,
    max_rpm=3,
    allow_delegation=False
)


# ── Agent 4: Risk Assessor ───────────────────────────────────────────────────
risk_assessor = Agent(
    role="Quantitative Risk Assessment Specialist",
    goal=(
        "Conduct a rigorous, data-driven risk assessment of the company based on the "
        "financial document provided. Evaluate leverage, liquidity, cash flow stability, "
        "interest coverage, and macroeconomic exposure. Provide a balanced, evidence-based "
        "risk rating and clearly explain the factors driving it."
    ),
    verbose=True,
    memory=False,           # Fix: same as above
    backstory=(
        "You hold an FRM (Financial Risk Manager) certification and have 10 years of "
        "experience in institutional risk management at a major investment bank. You apply "
        "established frameworks (VaR, stress testing, ratio analysis) to assess financial "
        "risk objectively. You understand that both over-stating and under-stating risk "
        "causes real harm to investors, so you present balanced, well-evidenced assessments. "
        "You respect regulatory capital requirements and believe sound risk management is "
        "the foundation of sustainable investing."
    ),
    tools=[RiskTool.create_risk_assessment_tool],
    llm=llm,
    max_iter=3,
    max_rpm=3,
    allow_delegation=False
)