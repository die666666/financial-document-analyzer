from fastapi import FastAPI, File, UploadFile, Form, HTTPException
import os
import uuid
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

from crewai import Crew, Process
from agents import financial_analyst, verifier, investment_advisor, risk_assessor
from task import (
    verification,
    analyze_financial_document,
    investment_analysis,
    risk_assessment,
)

app = FastAPI(title="Financial Document Analyzer")

_executor = ThreadPoolExecutor(max_workers=4)


def run_crew(query: str, file_path: str = "data/sample.pdf"):
    """Run the full analyst crew synchronously."""
    # Pause between each task to let the Groq TPM bucket partially refill.
    # llama-3.3-70b-versatile has 12,000 TPM — each task uses ~3,000-4,000 tokens.
    # A 15s pause between tasks allows ~3,000 tokens to recover (12,000/60 * 15).
    def task_callback(task_output):
        print(f"[Task done] Waiting 15s for TPM bucket to recover...")
        time.sleep(15)

    financial_crew = Crew(
        agents=[financial_analyst, verifier, investment_advisor, risk_assessor],
        tasks=[
            verification,
            analyze_financial_document,
            investment_analysis,
            risk_assessment,
        ],
        process=Process.sequential,
        verbose=True,
        task_callback=task_callback,  # sleep after each task completes
    )
    result = financial_crew.kickoff({"query": query, "file_path": file_path})
    return result


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Financial Document Analyzer API is running"}


@app.post("/analyze")
async def analyze_document(
    file: UploadFile = File(...),
    query: str = Form(default="Analyze this financial document for investment insights")
):
    """Analyze a financial document and provide comprehensive investment recommendations."""

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_id = str(uuid.uuid4())
    file_path = f"data/financial_document_{file_id}.pdf"

    try:
        os.makedirs("data", exist_ok=True)

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        if not query or not query.strip():
            query = "Analyze this financial document for investment insights"

        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                _executor,
                lambda: run_crew(query=query.strip(), file_path=file_path)
            ),
            timeout=300
        )

        return {
            "status": "success",
            "query": query.strip(),
            "analysis": str(response),
            "file_processed": file.filename
        }

    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Analysis timed out. Try a shorter query or a smaller document."
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing financial document: {str(e)}"
        )

    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)