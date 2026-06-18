"""
AILifeBot RecruitAI — Dual-Portal Agentic Orchestrator
"""

import os
import json
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import asyncio

load_dotenv()

app = FastAPI(title="AILifeBot Dual-Portal Orchestrator")

USE_GEMINI = False
if os.getenv("GEMINI_API_KEY"):
    from google import genai
    from google.genai import types
    gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    USE_GEMINI = True
else:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    MODEL_NAME = "gpt-4o-mini"

# ──────────────────────────────────────────────
# Pydantic Models
# ──────────────────────────────────────────────

class ManagerPrompt(BaseModel):
    prompt: str

class ResumeUpload(BaseModel):
    resume_text: str

class ChatMessage(BaseModel):
    message: str
    history: list[dict] = []

# ──────────────────────────────────────────────
# CORE GENERATOR
# ──────────────────────────────────────────────

def generate_completion(system_prompt, user_content, history=None, temperature=0.7, max_tokens=1500, json_mode=False):
    if USE_GEMINI:
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
            max_output_tokens=max_tokens,
            response_mime_type="application/json" if json_mode else "text/plain"
        )
        contents = []
        if history:
            for m in history:
                role = "model" if m["role"] == "assistant" else "user"
                contents.append(types.Content(role=role, parts=[types.Part.from_text(text=m["content"])]))
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_content)]))
        
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
            config=config
        )
        return response.text
    else:
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_content})
        
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"} if json_mode else None
        )
        return response.choices[0].message.content

# ──────────────────────────────────────────────
# DATABASE
# ──────────────────────────────────────────────
with open("mock_db.json", "r") as f:
    MOCK_DB = json.load(f)

# ──────────────────────────────────────────────
# MANAGER ENDPOINTS
# ──────────────────────────────────────────────

@app.post("/api/manager/pipeline")
async def manager_pipeline(req: ManagerPrompt):
    """
    1. Generates JD
    2. Builds Archetype from Top Performers
    3. Finds matches in Passive + Silver Medalists
    """
    try:
        # Step 1: Generate JD
        jd_sys = "You are an HR AI. Given a manager's raw input, create a professional, inclusive job description in Markdown."
        jd = generate_completion(jd_sys, req.prompt, temperature=0.7)
        
        # Step 2: Build Archetype
        arch_sys = "You are a recruitment AI. Analyze these top performers and extract a 'High-Performer Archetype' (Success Vectors, Skills). Return JSON with key 'archetype_summary' and 'success_vectors' (list of strings)."
        arch_raw = generate_completion(arch_sys, json.dumps(MOCK_DB["top_performers"]), json_mode=True)
        archetype = json.loads(arch_raw)
        
        # Step 3: Semantic Match & Outreach
        source_sys = (
            "You are an AI sourcing agent. Compare the Archetype to these Passive Candidates and Silver Medalists. "
            "Return JSON with an array 'sourced_candidates'. Each must have: id, name, match_score (0-100), "
            "churn_signal, and a hyper-personalized 'outreach_message'."
        )
        candidates_data = json.dumps({
            "archetype": archetype,
            "passive": MOCK_DB["passive_candidates"],
            "silver": MOCK_DB["silver_medalists"]
        })
        sourced_raw = generate_completion(source_sys, candidates_data, temperature=0.5, json_mode=True)
        sourced = json.loads(sourced_raw)
        
        return {
            "status": "Pipeline Complete",
            "job_description": jd,
            "archetype": archetype,
            "sourced_candidates": sourced.get("sourced_candidates", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ──────────────────────────────────────────────
# CANDIDATE ENDPOINTS
# ──────────────────────────────────────────────

@app.post("/api/candidate/screen")
async def candidate_screen(req: ResumeUpload):
    """
    Parses resume, checks against JD/Archetype, provides Fit Score.
    Bias Mitigation: Name/Gender are ignored.
    """
    try:
        screen_sys = (
            "You are a cognitive screening AI. Analyze this resume text and return JSON. "
            "The model is operating in BLIND MODE. Ignore names/gender/age. "
            "Return JSON with exact keys: 'fit_score' (object with 'hard_skills' 0-100, 'experience_quality' 0-100, 'behavioral_intent' 0-100, 'overall' 0-100), "
            "'anomalies' (list of gaps), 'career_narrative' (string)."
        )
        raw = generate_completion(screen_sys, req.resume_text, json_mode=True)
        return json.loads(raw)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/candidate/interview")
async def candidate_interview(req: ChatMessage):
    try:
        sys = (
            "You are an AI Interviewer for AILifeBot. Be empathetic, dynamic. Ask ONE question at a time based on their previous answer. "
            "If they say they are done, thank them and end."
        )
        user_content = req.message if req.message else "Hi, I am ready for the interview."
        reply = generate_completion(sys, user_content, history=req.history, temperature=0.7, max_tokens=300)
        return {"response": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/candidate/snapshot")
async def candidate_snapshot(req: ChatMessage):
    try:
        transcript = "\n".join([f"{m['role']}: {m['content']}" for m in req.history])
        sys = (
            "Analyze interview transcript. Return JSON with 'vibe_check', 'red_flags' (list), "
            "'top_3_reasons_to_hire' (list), and 'recommended_action'."
        )
        raw = generate_completion(sys, transcript, json_mode=True)
        return json.loads(raw)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ──────────────────────────────────────────────
# FRONTEND ROUTING
# ──────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")

@app.get("/manager")
async def serve_manager():
    return FileResponse("static/manager.html")

@app.get("/candidate")
async def serve_candidate():
    return FileResponse("static/candidate.html")
