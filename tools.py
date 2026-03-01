## Importing libraries and files
import os
import re
from pypdf import PdfReader
from dotenv import load_dotenv
load_dotenv()

from crewai_tools import SerperDevTool
from crewai.tools import tool

## Creating search tool
search_tool = SerperDevTool()

# ── Token limit for PDF extraction ──────────────────────────────────────────
# Groq free tier limit is 6,000 TPM. With 4 agents each receiving the document,
# we cap extraction at 1,500 words (~2,000 tokens) to stay safely within limits.
# Increase this if you upgrade to Groq Dev tier (higher TPM limits).
MAX_WORDS = 1500

# ── Shared PDF path constant ─────────────────────────────────────────────────
DEFAULT_PDF_PATH = r"D:\BACKUP\Backup\Python Projects\Task\financial-document-analyzer-debug\data\TSLA-Q2-2025-Update.pdf"


## Creating custom pdf reader tool
class FinancialDocumentTool():
    @staticmethod
    @tool("Read Financial Document")
    def read_data_tool(path: str = DEFAULT_PDF_PATH) -> str:
        """Tool to read data from a PDF file at the given path.

        Args:
            path (str): Path of the PDF file.

        Returns:
            str: Extracted text content of the financial document, capped at MAX_WORDS
                 to stay within Groq free tier token limits.
        """
        reader = PdfReader(path)

        full_report = ""
        total_words = 0

        for page in reader.pages:
            content = page.extract_text() or ""

            # Remove consecutive blank lines
            while "\n\n" in content:
                content = content.replace("\n\n", "\n")

            # Fix: cap total extracted words to avoid Groq rate limit errors.
            # Count words in this page and stop early if limit is reached.
            page_words = content.split()
            remaining = MAX_WORDS - total_words

            if remaining <= 0:
                break  # already hit the limit on a previous page

            if len(page_words) > remaining:
                # Take only as many words as we have budget for
                content = " ".join(page_words[:remaining])
                full_report += content + "\n"
                total_words += remaining
                break
            else:
                full_report += content + "\n"
                total_words += len(page_words)

        # Append a note if the document was truncated
        if total_words >= MAX_WORDS:
            full_report += (
                f"\n[Note: Document truncated to {MAX_WORDS} words to comply with "
                f"API token limits. Upgrade to Groq Dev tier for full document analysis.]\n"
            )

        return full_report


## Creating Investment Analysis Tool
class InvestmentTool:
    @staticmethod
    @tool("Analyze Investment Data")
    def analyze_investment_tool(financial_document_data: str) -> str:
        """Analyzes financial document data and returns investment insights.

        Args:
            financial_document_data (str): Raw financial document text content.

        Returns:
            str: Structured investment analysis report.
        """
        processed_data = " ".join(financial_document_data.split())

        # ── Investment Analysis Logic ────────────────────────────────────────
        analysis = {}

        # 1. Revenue
        revenue_match = re.search(
            r'(?:total\s+)?revenue[:\s]+\$?([\d,]+(?:\.\d+)?)\s*(million|billion|M|B)?',
            processed_data, re.IGNORECASE
        )
        if revenue_match:
            value = float(revenue_match.group(1).replace(",", ""))
            multiplier = {"million": 1e6, "billion": 1e9, "m": 1e6, "b": 1e9}.get(
                (revenue_match.group(2) or "").lower(), 1
            )
            analysis["Revenue"] = f"${value * multiplier:,.2f}"

        # 2. Net Income
        net_income_match = re.search(
            r'net\s+(?:income|profit)[:\s]+\$?([\d,]+(?:\.\d+)?)\s*(million|billion|M|B)?',
            processed_data, re.IGNORECASE
        )
        if net_income_match:
            value = float(net_income_match.group(1).replace(",", ""))
            multiplier = {"million": 1e6, "billion": 1e9, "m": 1e6, "b": 1e9}.get(
                (net_income_match.group(2) or "").lower(), 1
            )
            analysis["Net Income"] = f"${value * multiplier:,.2f}"

        # 3. EPS
        eps_match = re.search(
            r'(?:eps|earnings\s+per\s+share)[:\s]+\$?([\d.]+)',
            processed_data, re.IGNORECASE
        )
        if eps_match:
            analysis["EPS"] = f"${float(eps_match.group(1)):.2f}"

        # 4. P/E Ratio
        pe_match = re.search(
            r'(?:p/?e\s*ratio|price[\s\-]+to[\s\-]+earnings)[:\s]+([\d.]+)',
            processed_data, re.IGNORECASE
        )
        if pe_match:
            pe = float(pe_match.group(1))
            analysis["P/E Ratio"] = f"{pe:.2f}"
            if pe < 15:
                analysis["Valuation Signal"] = "Potentially Undervalued (P/E < 15)"
            elif pe <= 25:
                analysis["Valuation Signal"] = "Fairly Valued (P/E 15-25)"
            else:
                analysis["Valuation Signal"] = "Potentially Overvalued (P/E > 25)"

        # 5. Profit Margin — derived from Revenue + Net Income
        if "Revenue" in analysis and "Net Income" in analysis:
            rev = float(analysis["Revenue"].replace("$", "").replace(",", ""))
            net = float(analysis["Net Income"].replace("$", "").replace(",", ""))
            if rev > 0:
                margin = (net / rev) * 100
                analysis["Profit Margin"] = f"{margin:.2f}%"
                analysis["Margin Signal"] = (
                    "Strong (>20%)"     if margin > 20 else
                    "Moderate (10-20%)" if margin >= 10 else
                    "Weak (<10%)"
                )

        # 6. Revenue Growth
        growth_match = re.search(
            r'(?:revenue\s+growth|yoy\s+growth)[:\s]+([\d.]+)%',
            processed_data, re.IGNORECASE
        )
        if growth_match:
            growth = float(growth_match.group(1))
            analysis["Revenue Growth"] = f"{growth:.2f}%"
            analysis["Growth Signal"] = (
                "High Growth (>15%)"      if growth > 15 else
                "Moderate Growth (5-15%)" if growth >= 5 else
                "Low Growth (<5%)"
            )

        # ── Format output ────────────────────────────────────────────────────
        if not analysis:
            return (
                "Investment Analysis: No structured financial metrics could be extracted. "
                "Ensure the document contains labelled fields such as Revenue, Net Income, EPS, or P/E Ratio."
            )

        report_lines = ["=== Investment Analysis Report ==="]
        for key, value in analysis.items():
            report_lines.append(f"  {key}: {value}")
        report_lines.append("==================================")
        return "\n".join(report_lines)


## Creating Risk Assessment Tool
class RiskTool:
    @staticmethod
    @tool("Create Risk Assessment")
    def create_risk_assessment_tool(financial_document_data: str) -> str:
        """Creates a risk assessment from financial document data.

        Args:
            financial_document_data (str): Raw financial document text content.

        Returns:
            str: Structured risk assessment report with an overall risk score.
        """
        risks = {}
        risk_score = 0

        # 1. Debt-to-Equity
        de_match = re.search(
            r'(?:debt[\s\-]+to[\s\-]+equity|d/?e\s*ratio)[:\s]+([\d.]+)',
            financial_document_data, re.IGNORECASE
        )
        if de_match:
            de = float(de_match.group(1))
            risks["Debt-to-Equity Ratio"] = f"{de:.2f}"
            if de > 2.0:
                risks["Leverage Risk"] = "High — significant debt relative to equity"
                risk_score += 30
            elif de > 1.0:
                risks["Leverage Risk"] = "Moderate — debt exceeds equity"
                risk_score += 15
            else:
                risks["Leverage Risk"] = "Low — conservative leverage"
                risk_score += 5

        # 2. Current Ratio
        cr_match = re.search(
            r'current\s+ratio[:\s]+([\d.]+)',
            financial_document_data, re.IGNORECASE
        )
        if cr_match:
            cr = float(cr_match.group(1))
            risks["Current Ratio"] = f"{cr:.2f}"
            if cr < 1.0:
                risks["Liquidity Risk"] = "High — current liabilities exceed current assets"
                risk_score += 30
            elif cr < 1.5:
                risks["Liquidity Risk"] = "Moderate — thin liquidity buffer"
                risk_score += 15
            else:
                risks["Liquidity Risk"] = "Low — healthy short-term liquidity"
                risk_score += 5

        # 3. Operating Cash Flow
        ocf_match = re.search(
            r'(?:operating\s+cash\s+flow|cash\s+from\s+operations)[:\s]+\$?([-\d,]+(?:\.\d+)?)\s*(million|billion|M|B)?',
            financial_document_data, re.IGNORECASE
        )
        if ocf_match:
            value = float(ocf_match.group(1).replace(",", ""))
            multiplier = {"million": 1e6, "billion": 1e9, "m": 1e6, "b": 1e9}.get(
                (ocf_match.group(2) or "").lower(), 1
            )
            ocf = value * multiplier
            risks["Operating Cash Flow"] = f"${ocf:,.2f}"
            if ocf < 0:
                risks["Cash Flow Risk"] = "High — negative operating cash flow"
                risk_score += 25
            else:
                risks["Cash Flow Risk"] = "Low — positive operating cash flow"

        # 4. Interest Coverage Ratio
        icr_match = re.search(
            r'interest\s+coverage(?:\s+ratio)?[:\s]+([\d.]+)',
            financial_document_data, re.IGNORECASE
        )
        if icr_match:
            icr = float(icr_match.group(1))
            risks["Interest Coverage Ratio"] = f"{icr:.2f}x"
            if icr < 1.5:
                risks["Debt Servicing Risk"] = "High — earnings barely cover interest"
                risk_score += 20
            elif icr < 3.0:
                risks["Debt Servicing Risk"] = "Moderate — limited interest coverage buffer"
                risk_score += 10
            else:
                risks["Debt Servicing Risk"] = "Low — earnings comfortably cover interest"

        # 5. Revenue Concentration
        if re.search(
            r'(top\s+\d+\s+customer|single\s+customer|customer\s+concentration)',
            financial_document_data, re.IGNORECASE
        ):
            risks["Revenue Concentration Risk"] = "Elevated — dependency on a small customer base"
            risk_score += 10

        # 6. Macro/Market risk keywords
        macro_keywords = ["recession", "inflation risk", "interest rate risk", "regulatory risk", "geopolitical"]
        found_macro = [kw for kw in macro_keywords if kw.lower() in financial_document_data.lower()]
        if found_macro:
            risks["Macro/Market Risk Flags"] = ", ".join(found_macro)
            risk_score += 5 * len(found_macro)

        # ── Overall Risk Rating ──────────────────────────────────────────────
        risk_score = min(risk_score, 100)
        overall = (
            "HIGH RISK"     if risk_score >= 60 else
            "MODERATE RISK" if risk_score >= 30 else
            "LOW RISK"
        )
        risks["Overall Risk Score"] = f"{risk_score}/100"
        risks["Overall Rating"]     = overall

        if len(risks) == 2:
            return (
                "Risk Assessment: No structured risk metrics could be extracted. "
                "Ensure the document contains fields such as Debt-to-Equity, Current Ratio, or Operating Cash Flow."
            )

        report_lines = ["=== Risk Assessment Report ==="]
        for key, value in risks.items():
            report_lines.append(f"  {key}: {value}")
        report_lines.append("==============================")
        return "\n".join(report_lines)