import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from datetime import datetime
from typing import List

load_dotenv()

try:
    from google import genai
except Exception as e:
    genai = None

from database import (
    energy_collection,
    users_collection,
    leaderboard_collection,
    admin_collection,
    priority_requests_collection,
    regional_data_collection,
    system_status_collection
)
from models import (
    EnergyData,
    EnergyDataResponse,
    UserData,
    LeaderboardUser,
    UpdatePointsRequest,
    AddBadgeRequest,
    PriorityRequest,
    CreatePriorityRequest,
    UpdateRequestStatusRequest,
    RegionalData,
    AdminSettings,
    AdminDataResponse
)


class VoiceCommandRequest(BaseModel):
    command: str
    language: str
    currentMode: str
    availableModes: list[str]


class GeminiResponse(BaseModel):
    mode: str | None
    confidence: float
    explanation: str


app = FastAPI(title="SIH25210 Backend", version="1.0.0")

# CORS: allow frontend dev server
origins = [
    os.getenv("CORS_ORIGIN", "http://localhost:5173"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


# ============================================
# Energy Data Endpoints
# ============================================

@app.get("/api/energy/current", response_model=EnergyDataResponse)
async def get_current_energy():
    """Get current energy data with historical records"""
    try:
        # Get the most recent energy data
        current = await energy_collection.find_one(sort=[("timestamp", -1)])
        
        # Get last 100 historical records
        historical_cursor = energy_collection.find().sort("timestamp", -1).limit(100)
        historical = await historical_cursor.to_list(length=100)
        
        if not current:
            # Return default data if no data exists
            return {
                "energyData": {
                    "solar": 0,
                    "wind": 0,
                    "grid": 0,
                    "battery": {"level": 75, "health": 92},
                    "consumption": 0,
                    "timestamp": datetime.now()
                },
                "renewablePercentage": 75,
                "isOnline": True,
                "alerts": [],
                "historicalData": []
            }
        
        # Calculate renewable percentage (using battery level as equipment efficiency)
        renewable_percentage = current.get("battery", {}).get("level", 75)
        
        # Generate alerts based on current data
        alerts = []
        if current.get("battery", {}).get("level", 0) < 70:
            alerts.append("Equipment Efficiency Low")
        if current.get("solar", 0) > 90:
            alerts.append("Crusher Overload Warning")
        if current.get("wind", 0) < 10:
            alerts.append("Mill Speed Below Optimal")
        if current.get("grid", 0) > 900:
            alerts.append("High Throughput Achieved")
        
        return {
            "energyData": current,
            "renewablePercentage": renewable_percentage,
            "isOnline": True,
            "alerts": alerts,
            "historicalData": historical
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching energy data: {str(e)}")


@app.post("/api/energy/update")
async def update_energy_data(data: EnergyData):
    """Add new energy data point"""
    try:
        data_dict = data.model_dump()
        result = await energy_collection.insert_one(data_dict)
        return {"success": True, "id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating energy data: {str(e)}")


# ============================================
# User Data Endpoints
# ============================================

@app.get("/api/user/{user_id}", response_model=UserData)
async def get_user_data(user_id: str):
    """Get user data by ID"""
    try:
        user = await users_collection.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user data: {str(e)}")


@app.get("/api/leaderboard", response_model=List[LeaderboardUser])
async def get_leaderboard():
    """Get leaderboard data"""
    try:
        cursor = leaderboard_collection.find().sort("rank", 1)
        leaderboard = await cursor.to_list(length=100)
        return leaderboard
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching leaderboard: {str(e)}")


@app.post("/api/user/points")
async def update_user_points(request: UpdatePointsRequest):
    """Update user points"""
    try:
        # Update in users collection
        user_result = await users_collection.update_one(
            {"id": request.userId},
            {"$inc": {"points": request.points}}
        )
        
        # Update in leaderboard collection
        leaderboard_result = await leaderboard_collection.update_one(
            {"id": request.userId},
            {"$inc": {"points": request.points}}
        )
        
        if user_result.modified_count == 0 and leaderboard_result.modified_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Recalculate ranks
        await recalculate_leaderboard_ranks()
        
        return {"success": True, "message": "Points updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating points: {str(e)}")


@app.post("/api/user/badge")
async def add_user_badge(request: AddBadgeRequest):
    """Add a badge to user"""
    try:
        result = await users_collection.update_one(
            {"id": request.userId},
            {"$addToSet": {"badges": request.badge}}
        )
        
        if result.modified_count == 0:
            # Check if user exists
            user = await users_collection.find_one({"id": request.userId})
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            # Badge might already exist
            return {"success": True, "message": "Badge already exists or added"}
        
        return {"success": True, "message": "Badge added successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding badge: {str(e)}")


async def recalculate_leaderboard_ranks():
    """Recalculate and update leaderboard ranks based on points"""
    try:
        # Get all leaderboard entries sorted by points
        cursor = leaderboard_collection.find().sort("points", -1)
        entries = await cursor.to_list(length=1000)
        
        # Update ranks
        for idx, entry in enumerate(entries, start=1):
            await leaderboard_collection.update_one(
                {"id": entry["id"]},
                {"$set": {"rank": idx}}
            )
            # Also update in users collection
            await users_collection.update_one(
                {"id": entry["id"]},
                {"$set": {"rank": idx}}
            )
    except Exception as e:
        print(f"Error recalculating ranks: {e}")


# ============================================
# Admin Data Endpoints
# ============================================

@app.get("/api/admin/data", response_model=AdminDataResponse)
async def get_admin_data():
    """Get all admin data including settings, priority requests, regional data, and system status"""
    try:
        # Get admin settings
        settings = await admin_collection.find_one({"type": "settings"})
        if not settings:
            settings = {"energyMode": "Auto Mode", "mlAutoMode": False}
        
        # Get priority requests
        cursor = priority_requests_collection.find().sort("timestamp", -1)
        priority_requests = await cursor.to_list(length=100)
        
        # Get regional data
        cursor = regional_data_collection.find()
        regional_data = await cursor.to_list(length=100)
        
        # Get system status
        cursor = system_status_collection.find()
        system_status_list = await cursor.to_list(length=100)
        system_status = {item["name"]: item["status"] for item in system_status_list}
        
        return {
            "energyMode": settings.get("energyMode", "Auto Mode"),
            "mlAutoMode": settings.get("mlAutoMode", False),
            "systemStatus": system_status,
            "priorityRequests": priority_requests,
            "regionalData": regional_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching admin data: {str(e)}")


@app.post("/api/admin/energy-mode")
async def update_energy_mode(mode: str):
    """Update energy mode"""
    try:
        result = await admin_collection.update_one(
            {"type": "settings"},
            {"$set": {"energyMode": mode}},
            upsert=True
        )
        return {"success": True, "message": "Energy mode updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating energy mode: {str(e)}")


@app.post("/api/admin/ml-auto-mode")
async def update_ml_auto_mode(enabled: bool):
    """Toggle ML auto mode"""
    try:
        result = await admin_collection.update_one(
            {"type": "settings"},
            {"$set": {"mlAutoMode": enabled}},
            upsert=True
        )
        return {"success": True, "message": "ML auto mode updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating ML auto mode: {str(e)}")


@app.post("/api/admin/priority-request")
async def create_priority_request(request: CreatePriorityRequest):
    """Create a new priority request"""
    try:
        new_request = {
            "id": str(datetime.now().timestamp()),
            "facility": request.facility,
            "priority": request.priority,
            "reason": request.reason,
            "status": "Pending",
            "timestamp": datetime.now()
        }
        
        result = await priority_requests_collection.insert_one(new_request)
        return {"success": True, "id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating priority request: {str(e)}")


@app.post("/api/admin/priority-request/status")
async def update_priority_request_status(request: UpdateRequestStatusRequest):
    """Update priority request status"""
    try:
        result = await priority_requests_collection.update_one(
            {"id": request.requestId},
            {"$set": {"status": request.status}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Priority request not found")
        
        return {"success": True, "message": "Status updated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating request status: {str(e)}")


# ============================================
# Gemini AI Endpoints
# ============================================


@app.post("/api/gemini/voice", response_model=GeminiResponse)
def gemini_voice(req: VoiceCommandRequest):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set")
    if genai is None:
        raise HTTPException(status_code=500, detail="google-genai not available")

    client = genai.Client(api_key=api_key)

    prompt = f'''
You are an energy management system voice assistant. Analyze this voice command and determine the intended energy mode.

Voice Command: "{req.command}"
Language: {req.language}
Current Mode: {req.currentMode}
Available Modes: {', '.join(req.availableModes)}

Energy Mode Mappings:
- "solar" or "solar only" → solar
- "wind" or "wind only" → wind
- "solar and wind" or "renewable" or "hybrid" → solar+wind
- "all sources" or "everything" or "full power" → solar+wind+grid
- "grid" or "grid only" → grid

Respond with JSON only:
{{
  "mode": "detected_mode_or_null",
  "confidence": 0.0-1.0,
  "explanation": "brief_explanation"
}}
'''

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        text = getattr(response, "text", None)
        if not text:
            return GeminiResponse(mode=None, confidence=0.0, explanation="No valid response from Gemini")

        # Try to parse strict JSON
        import json, re
        parsed = None
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            # extract JSON object if wrapped or extra text present
            match = re.search(r"\{[\s\S]*\}", text)
            if match:
                try:
                    parsed = json.loads(match.group(0))
                except Exception:
                    parsed = None

        if parsed and isinstance(parsed, dict):
            return GeminiResponse(
                mode=parsed.get("mode"),
                confidence=float(parsed.get("confidence", 0.0)),
                explanation=parsed.get("explanation", "") or "Parsed from Gemini response",
            )

        return GeminiResponse(mode=None, confidence=0.0, explanation="Unable to parse Gemini response")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gemini API error: {e}")


class ChatMessage(BaseModel):
    role: str  # 'user' | 'assistant' | 'system'
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    system: str | None = None
    temperature: float | None = None


class ChatResponse(BaseModel):
    text: str


@app.post("/api/gemini/chat", response_model=ChatResponse)
def gemini_chat(req: ChatRequest):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set")
    if genai is None:
        raise HTTPException(status_code=500, detail="google-genai not available")

    client = genai.Client(api_key=api_key)

    # Build a simple conversation prompt
    system_context = req.system or (
        "You are an expert AI Mining Assistant helping with crushing optimization, grinding efficiency, predictive maintenance, Digital Twin simulation, equipment monitoring, and AI-driven process control."
    )
    conv = [f"{m.role.upper()}: {m.content}" for m in req.messages[-20:]]
    prompt = f"""
{system_context}

Provide concise, clear, and actionable answers.

Conversation so far:
{chr(10).join(conv)}

ASSISTANT:
"""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        text = getattr(response, "text", "").strip()
        if not text:
            raise HTTPException(status_code=502, detail="Empty response from Gemini")
        return ChatResponse(text=text)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gemini API error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
