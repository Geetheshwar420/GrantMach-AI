from fastapi import FastAPI
from pydantic import BaseModel
import httpx, os
from groq import Groq
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

app = FastAPI()
llm = Groq(api_key=os.getenv("GROQ_API_KEY"))
ANAKIN_KEY = os.getenv("ANAKIN_API_KEY")

class Task(BaseModel):
    task_id: str
    abstract: str
    grant_target: str

@app.post("/run")
async def run(task: Task):
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.anakin.io/v1/search",
            params={
                "q": f"{task.grant_target} eligibility requirements review criteria",
                "format": "markdown"
            },
            headers={"Authorization": f"Bearer {ANAKIN_KEY}"},
            timeout=30
        )
    raw = r.json().get("content", "") if r.status_code == 200 else ""

    chat = llm.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": """You are a grant compliance reviewer.
Analyze alignment between the project and grant requirements. Return JSON:
{"match_score_percentage": 85, "alignment_strengths": [...], "compliance_gaps": [...]}"""},
            {"role": "user", "content": f"Abstract: {task.abstract}\nGrant Details: {task.grant_target}\nGuidelines: {raw[:4000]}"}
        ],
        response_format={"type": "json_object"}
    )
    return {"task_id": task.task_id, "agent": "compliance_analyst", "result": chat.choices[0].message.content}

@app.get("/health")
def health(): return {"status": "ok", "agent": "compliance_analyst"}
