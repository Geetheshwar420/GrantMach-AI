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

@app.post("/run")
async def run(task: Task):
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.anakin.io/v1/search",
            params={
                "q": f"{task.abstract[:100]} site:grants.gov OR site:nsf.gov OR site:nih.gov",
                "format": "markdown",
                "limit": 5
            },
            headers={"Authorization": f"Bearer {ANAKIN_KEY}"},
            timeout=30
        )
    raw = r.json().get("content", "No matching grants found") if r.status_code == 200 else "No matching grants found"

    chat = llm.chat.completions.create(
        model="llama-3.1-8b-instant",
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
