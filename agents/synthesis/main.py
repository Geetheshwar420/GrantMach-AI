from fastapi import FastAPI
from pydantic import BaseModel
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

app = FastAPI()
llm = Groq(api_key=os.getenv("GROQ_API_KEY"))

class SynthesisTask(BaseModel):
    task_id: str
    abstract: str
    grants: str
    compliance: str

@app.post("/run")
async def run(task: SynthesisTask):
    chat = llm.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": """You are a senior grant strategy director.
Synthesize the final funding brief and write an optimized proposal outline. Return JSON with:
{
  "best_recommendation": "Top grant option with rationale",
  "readiness_score": "e.g. 90%",
  "strategic_recommendations": ["3 actionable edits to win the grant"],
  "drafted_specific_aims": "Compelling 1-paragraph summary tailored to the funder rubric"
}"""},
            {"role": "user", "content": f"Project: {task.abstract}\nGrants Found: {task.grants}\nCompliance Analysis: {task.compliance}"}
        ],
        response_format={"type": "json_object"}
    )
    return {"task_id": task.task_id, "agent": "synthesis", "result": chat.choices[0].message.content}

@app.get("/health")
def health(): return {"status": "ok", "agent": "synthesis"}
