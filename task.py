from crewai import Task

from agents import financial_analyst, verifier, investment_advisor, risk_assessor
from tools import FinancialDocumentTool, InvestmentTool, RiskTool


## Task 1 — Document Verification
verification = Task(
    description=(
        "Read the file at {file_path} and confirm it is a financial document. "
        "Check for financial sections like income statement, balance sheet, or cash flow. "
        "Return PASS if valid, FAIL if not."
    ),
    expected_output=(
        "One paragraph stating: document type, company name, reporting period, "
        "sections found, and a PASS or FAIL verdict."
    ),
    agent=verifier,
    tools=[FinancialDocumentTool.read_data_tool],
    async_execution=False,
)


## Task 2 — Financial Analysis
analyze_financial_document = Task(
    description=(
        "Read the file at {file_path} and answer: {query}. "
        "Extract key numbers: revenue, net income, EPS, margins, YoY growth. "
        "Only use data from the document. Flag any missing data."
    ),
    expected_output=(
        "Short report with: one summary paragraph, key metrics list, "
        "main trends observed, and data gaps if any."
    ),
    agent=financial_analyst,
    tools=[FinancialDocumentTool.read_data_tool],
    async_execution=False,
)


## Task 3 — Investment Analysis
investment_analysis = Task(
    description=(
        "Using the financial data already extracted, answer: {query}. "
        "Assess valuation using P/E, margins, and growth. "
        "Give a bullish, neutral, or bearish outlook with reasons. "
        "Include a disclaimer that this is not personalised financial advice."
    ),
    expected_output=(
        "Short report with: outlook rating, top 3 reasons, key risks, "
        "and a one-sentence disclaimer."
    ),
    agent=investment_advisor,
    tools=[InvestmentTool.analyze_investment_tool],
    async_execution=False,
)


## Task 4 — Risk Assessment
risk_assessment = Task(
    description=(
        "Using the financial data already extracted, assess risk for: {query}. "
        "Check: debt-to-equity, current ratio, cash flow, interest coverage. "
        "Rate overall risk as LOW, MODERATE, or HIGH with evidence."
    ),
    expected_output=(
        "Short report with: risk score per metric, overall rating, "
        "top 3 risk factors, and a one-sentence disclaimer."
    ),
    agent=risk_assessor,
    tools=[RiskTool.create_risk_assessment_tool],
    async_execution=False,
)