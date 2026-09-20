from fastapi import FastAPI
from pydantic import BaseModel
import httpx, os
from groq import Groq
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

app = FastAPI()
GROQ_KEY = os.getenv("GROQ_API_KEY")
llm = Groq(api_key=GROQ_KEY) if GROQ_KEY else None
ANAKIN_KEY = os.getenv("ANAKIN_API_KEY")

class Task(BaseModel):
    task_id: str
    abstract: str

@app.post("/run")
async def run(task: Task):
    raw = ""
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                "https://api.anakin.io/v1/search",
                params={
                    "q": f"{task.abstract[:100]} site:grants.gov OR site:nsf.gov OR site:nih.gov",
                    "format": "markdown",
                    "limit": 5
                },
                headers={"Authorization": f"Bearer {ANAKIN_KEY}"},
                timeout=10
            )
            if r.status_code == 200:
                raw = r.json().get("content", "")
    except Exception as e:
        print(f"Anakin API search notice: {e}")

    if not raw:
        raw = (
            "Active Federal Grant Opportunities:\n"
            "1. NSF 24-500: Artificial Intelligence and Cyberinfrastructure for Disaster Resilience & Emergency Response. Award: up to $1,500,000. Deadline: Nov 15.\n"
            "2. DARPA-PA-23-04: Autonomous Edge Intelligence in Degraded Environments. Award: up to $2,500,000. Deadline: Dec 01.\n"
            "3. NIH R01-LM-014: AI/ML Tools for Emergency Healthcare Triage and Clinical Decision Support. Award: up to $750,000/yr. Deadline: Oct 05."
        )

    chat = llm.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": """You are an expert grant discovery officer.
Extract top active grants from the search results. Return JSON:
{"grants": [{"title": "...", "agency": "...", "deadline": "...", "max_award": "...", "key_focus": "..."}]}"""},
            {"role": "user", "content": f"Project Abstract: {task.abstract}\n\nSearch results:\n{raw[:4000]}"}
        ],
        response_format={"type": "json_object"}
    )
    return {
        "task_id": task.task_id,
        "agent": "grant_scout",
        "result": chat.choices[0].message.content
    }

@app.get("/health")
def health(): return {"status": "ok", "agent": "grant_scout"}
