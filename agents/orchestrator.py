from fastapi import FastAPI, Body
from pydantic import BaseModel
import httpx, os, json
from typing import Optional

app = FastAPI(title="GrantMatch AI Unified Orchestrator")

class GrantRequest(BaseModel):
    abstract: Optional[str] = None
    input: Optional[str] = None

@app.get("/health")
def health():
    return {"status": "ok", "service": "GrantMatch AI Unified Orchestrator"}

@app.post("/match")
@app.post("/api/workflows/grantmatch_orchestrator/execute")
async def run_grant_match(payload: dict = Body(...)):
    # Parse input from abstract or input field
    abstract_text = payload.get("abstract") or payload.get("input") or ""
    if not abstract_text:
        return {"status": "error", "message": "No abstract provided in request body", "output": "Error: Abstract text is empty."}
    
    task_id = "gm_" + os.urandom(4).hex()
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. Grant Scout
        try:
            r1 = await client.post("http://localhost:8001/run", json={"task_id": task_id, "abstract": abstract_text})
            scout_res = r1.json().get("result", "")
        except Exception as e:
            scout_res = f"Grant Scout Notice: {str(e)}"
            
        # 2. Compliance Analyst
        try:
            r2 = await client.post("http://localhost:8002/run", json={"task_id": task_id, "abstract": abstract_text, "grant_target": str(scout_res)})
            comp_res = r2.json().get("result", "")
        except Exception as e:
            comp_res = f"Compliance Analyst Notice: {str(e)}"
            
        # 3. Synthesis Agent
        try:
            r3 = await client.post("http://localhost:8003/run", json={"task_id": task_id, "abstract": abstract_text, "grants": str(scout_res), "compliance": str(comp_res)})
            syn_res = r3.json().get("result", "")
        except Exception as e:
            syn_res = f"Synthesis Notice: {str(e)}"
            
    # Format clean output for DronaHQ Rich Text component
    try:
        raw_syn = syn_res if isinstance(syn_res, str) else str(syn_res)
        parsed = json.loads(raw_syn) if raw_syn.startswith("{") else {}
        if parsed:
            formatted_output = f"""## 🏆 GrantMatch AI — Strategic Alignment Report

### 🎯 Best Recommendation
{parsed.get('best_recommendation', 'N/A')}

### 📈 Readiness Score: {parsed.get('readiness_score', 'N/A')}

### 💡 Strategic Recommendations
""" + "\n".join([f"- {rec}" for rec in parsed.get('strategic_recommendations', [])]) + f"""

### 📄 Drafted Specific Aims Summary
{parsed.get('drafted_specific_aims', 'N/A')}
"""
        else:
            formatted_output = str(syn_res)
    except Exception as e:
        formatted_output = str(syn_res)

    return {
        "status": "success",
        "output": formatted_output,
        "scout_data": scout_res,
        "compliance_data": comp_res,
        "synthesis_data": syn_res
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
