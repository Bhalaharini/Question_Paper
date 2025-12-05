import os
from datetime import datetime, timedelta
from typing import List, Optional
import uuid

from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import bcrypt
import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/sih")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

app = FastAPI(
    title="Mining Comminution Optimizer API",
    description="AI-Powered Mining Energy Optimization System",
    version="1.0.0",
)

# CORS configuration for production
origins = [
    os.getenv("CORS_ORIGIN", "http://localhost:5173"),
    "http://localhost:5174",
    "https://*.vercel.app",  # Allow Vercel deployments
    "https://*.railway.app",  # Allow Railway deployments
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if os.getenv("ENVIRONMENT") == "production" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Database client and references
client: AsyncIOMotorClient = AsyncIOMotorClient(
    MONGODB_URL, 
    serverSelectionTimeoutMS=30000, 
    socketTimeoutMS=45000,
    tlsCAFile=certifi.where()
)
# Get database name from env or extract from URL
db_name = os.getenv("MONGODB_DB", "sih")
db = client[db_name]


# Schemas
class UserOut(BaseModel):
    username: str
    role: str
    name: str
    email: str


class TokenResponse(BaseModel):
    token: str
    user: UserOut


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str
    name: str
    email: str


class MachineData(BaseModel):
    machine_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    rock_size_mm: Optional[float] = None
    weight_kg: Optional[float] = None
    moisture_pct: Optional[float] = None
    flow_rate: Optional[float] = None
    motor_current_A: Optional[float] = None
    motor_voltage_V: Optional[float] = None
    belt_speed_pwm: Optional[float] = None
    vibration_level: Optional[float] = None
    predicted_power_W: Optional[float] = None
    machine_status: Optional[str] = Field(default="running")


class MachineStatus(BaseModel):
    machine_id: str
    status: str
    last_update: datetime
    throughput: float
    power_draw: float
    efficiency: float
    temperature: float
    vibration: float


class ControlRequest(BaseModel):
    action: str


class GeminiVoiceRequest(BaseModel):
    command: str
    language: Optional[str] = None
    currentMode: Optional[str] = None
    availableModes: Optional[List[str]] = None


class GeminiChatMessage(BaseModel):
    role: str
    content: str


class GeminiChatRequest(BaseModel):
    messages: List[GeminiChatMessage]
    system: Optional[str] = None


# Simple session storage (in production, use Redis or similar)
active_sessions = {}


async def get_user_by_username(username: str):
    return await db["users"].find_one({"username": username})


def create_session_token(user: dict) -> str:
    """Create a simple session token"""
    token = str(uuid.uuid4())
    active_sessions[token] = {
        "user_id": str(user.get("_id")),
        "username": user.get("username"),
        "role": user.get("role"),
        "created_at": datetime.utcnow(),
    }
    return token


async def authenticate_request(authorization: Optional[str] = Header(None)):
    """Simple token validation"""
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    # Extract token from "Bearer <token>"
    try:
        token = authorization.replace("Bearer ", "")
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format")
    
    session = active_sessions.get(token)
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")
    
    # Check if session is still valid (24 hours)
    if datetime.utcnow() - session["created_at"] > timedelta(hours=24):
        del active_sessions[token]
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
    
    user = await db["users"].find_one({"_id": ObjectId(session["user_id"])})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    return user


@app.get("/health")
async def health():
    # PyMongo/Motor doesn't easily expose readyState like Mongoose; do a ping.
    try:
        await db.command("ping")
        connected = True
        host = client.options.server_selector.__class__.__name__
    except Exception:
        connected = False
        host = "unknown"
    return {
        "status": "ok",
        "database": {
            "connected": connected,
            "host": host,
            "name": db.name,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/db/status")
async def db_status():
    try:
        await db.command("ping")
        connected = True
    except Exception:
        connected = False
    return {
        "connected": connected,
        "host": "atlas",
        "port": "n/a",
        "database": db.name,
        "readyState": 1 if connected else 0,
    }


# Auth routes
@app.post("/api/auth/login", response_model=TokenResponse)
async def login(form: LoginRequest):
    print(f"Login attempt for username: {form.username}")
    user = await db["users"].find_one({"username": form.username})
    
    if not user:
        print(f"User not found: {form.username}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is inactive")
    
    print(f"User found: {user['username']}, checking password...")
    
    # Check password
    try:
        password_hash = user["password_hash"]
        if isinstance(password_hash, str):
            password_match = bcrypt.checkpw(form.password.encode(), password_hash.encode())
        else:
            password_match = bcrypt.checkpw(form.password.encode(), password_hash)
        
        print(f"Password match: {password_match}")
        
        if not password_match:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    except Exception as e:
        print(f"Password verification error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    # Update last_login
    await db["users"].update_one({"_id": user["_id"]}, {"$set": {"last_login": datetime.utcnow()}})
    
    # Create session token
    token = create_session_token(user)
    
    return TokenResponse(
        token=token,
        user=UserOut(username=user["username"], role=user["role"], name=user["name"], email=user["email"]),
    )


@app.post("/api/auth/logout")
async def logout(user: dict = Depends(authenticate_request)):
    """Logout and invalidate session token"""
    # Find and remove the session token
    authorization = user.get("_session_token")  # We'll need to pass this through
    if authorization:
        token = authorization.replace("Bearer ", "")
        active_sessions.pop(token, None)
    return {"message": "Logged out successfully"}


@app.post("/api/auth/register", response_model=UserOut)
async def register(req: RegisterRequest):
    existing = await db["users"].find_one({"username": req.username})
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    password_hash = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()
    doc = {
        "username": req.username,
        "password_hash": password_hash,
        "role": req.role,
        "name": req.name,
        "email": req.email,
        "created_at": datetime.utcnow(),
        "is_active": True,
    }
    res = await db["users"].insert_one(doc)
    return UserOut(username=req.username, role=req.role, name=req.name, email=req.email)


def machine_collection(machine_id: str):
    mapping = {
        "machine-01": "machine1datas",
        "machine-02": "machine2datas",
        "machine-03": "machine3datas",
    }
    col = mapping.get(machine_id)
    if not col:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid machine ID")
    return db[col]


@app.get("/api/machines/{machine_id}/data", response_model=List[MachineData])
async def get_machine_data(machine_id: str, limit: int = 10):
    col = machine_collection(machine_id)
    cursor = col.find({}).sort("timestamp", -1).limit(limit)
    items = [MachineData(**{**doc, "_id": None}) async for doc in cursor]
    return items


@app.get("/api/machines/{machine_id}/status", response_model=MachineStatus)
async def get_machine_status(machine_id: str):
    col = machine_collection(machine_id)
    latest = await col.find_one(sort=[("timestamp", -1)])
    if not latest:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No data found for machine")
    efficiency = min(100.0, float(latest.get("flow_rate", 0)) / 2.0)
    return MachineStatus(
        machine_id=machine_id,
        status=latest.get("machine_status", "running"),
        last_update=latest.get("timestamp", datetime.utcnow()),
        throughput=float(latest.get("flow_rate", 0) or 0),
        power_draw=float(latest.get("predicted_power_W", 0) or 0) / 1000.0,
        efficiency=efficiency,
        temperature=25.0 + float(latest.get("motor_current_A", 0) or 0),
        vibration=float(latest.get("vibration_level", 0) or 0),
    )


@app.post("/api/machines/{machine_id}/control")
async def control_machine(machine_id: str, req: ControlRequest, user: dict = Depends(authenticate_request)):
    if req.action not in ["start", "stop", "maintenance"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid action")
    status_map = {"start": "running", "stop": "stopped", "maintenance": "maintenance"}
    new_status = status_map[req.action]
    col = machine_collection(machine_id)
    await col.update_many({"machine_id": machine_id}, {"$set": {"machine_status": new_status, "timestamp": datetime.utcnow()}})
    return {"message": f"Machine {machine_id} {req.action} successful", "status": new_status}


# Gemini routes (minimal placeholders; keep behavior compatible)
@app.post("/api/gemini/voice")
async def gemini_voice(req: GeminiVoiceRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set")
    # Placeholder deterministic response to keep frontend working without external calls
    text = {
        "mode": None,
        "confidence": 0.0,
        "explanation": "Gemini integration placeholder",
    }
    return text


@app.post("/api/gemini/chat")
async def gemini_chat(req: GeminiChatRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set")
    conversation = "\n".join([f"{m.role.upper()}: {m.content}" for m in req.messages[-10:]])
    return {"text": f"[Gemini placeholder]\n{conversation}"}


# Analytics routes
@app.get("/api/analytics/overview")
async def analytics_overview(user: dict = Depends(authenticate_request)):
    machines = ["machine-01", "machine-02", "machine-03"]
    overview = []
    total_power = 0.0
    total_flow = 0.0
    avg_efficiency = 0.0
    running_machines = 0

    for machine_id in machines:
        col = machine_collection(machine_id)
        latest = await col.find_one(sort=[("timestamp", -1)])
        if latest:
            efficiency = min(100.0, float(latest.get("flow_rate", 0) or 0) / 2.0)
            total_power += float(latest.get("predicted_power_W", 0) or 0)
            total_flow += float(latest.get("flow_rate", 0) or 0)
            avg_efficiency += efficiency
            if latest.get("machine_status") == "running":
                running_machines += 1
            overview.append({
                "machine_id": machine_id,
                "name": f"Machine {machine_id.split('-')[1]}",
                "status": latest.get("machine_status"),
                "power_W": float(latest.get("predicted_power_W", 0) or 0),
                "flow_rate": float(latest.get("flow_rate", 0) or 0),
                "efficiency": efficiency,
                "temperature": 25.0 + float(latest.get("motor_current_A", 0) or 0),
                "vibration": float(latest.get("vibration_level", 0) or 0),
                "last_update": latest.get("timestamp"),
            })

    avg_efficiency = (avg_efficiency / len(overview)) if overview else 0.0
    return {
        "machines": overview,
        "total_machines": len(overview),
        "summary": {
            "total_power_kw": total_power / 1000.0,
            "total_throughput": total_flow,
            "avg_efficiency": round(avg_efficiency),
            "running_machines": running_machines,
            "operational_status": round((running_machines / len(machines)) * 100) if machines else 0,
        },
    }


@app.get("/api/analytics/trends")
async def analytics_trends(user: dict = Depends(authenticate_request)):
    machines = ["machine-01", "machine-02", "machine-03"]
    trends = []
    for machine_id in machines:
        col = machine_collection(machine_id)
        cursor = col.find({}).sort("timestamp", -1).limit(24)
        data = [doc async for doc in cursor]
        data.reverse()
        hourly = [{
            "hour": idx,
            "power": float((item.get("predicted_power_W", 0) or 0)) / 1000.0,
            "throughput": float(item.get("flow_rate", 0) or 0),
            "efficiency": min(100.0, float(item.get("flow_rate", 0) or 0) / 2.0),
        } for idx, item in enumerate(data)]
        trends.append({
            "machine_id": machine_id,
            "name": f"Machine {machine_id.split('-')[1]}",
            "hourly_data": hourly,
        })
    return {"trends": trends}


@app.get("/api/analytics/breakdown")
async def analytics_breakdown(user: dict = Depends(authenticate_request)):
    machines = ["machine-01", "machine-02", "machine-03"]
    breakdown = []
    total_utilization = 0.0
    for machine_id in machines:
        col = machine_collection(machine_id)
        latest = await col.find_one(sort=[("timestamp", -1)])
        if latest:
            utilization = min(100.0, float(latest.get("flow_rate", 0) or 0) / 2.0) if latest.get("machine_status") == "running" else 0.0
            total_utilization += utilization
            breakdown.append({
                "name": f"Machine {machine_id.split('-')[1]}",
                "value": utilization,
                "color": "#f59e0b" if machine_id == "machine-01" else ("#3b82f6" if machine_id == "machine-02" else "#10b981"),
            })
    return {"breakdown": breakdown, "total_utilization": total_utilization}


@app.get("/api/analytics/alerts")
async def analytics_alerts(user: dict = Depends(authenticate_request)):
    cursor = db["alerts"].find({"is_resolved": False}).sort("created_at", -1).limit(10)
    alerts = [{k: v for k, v in doc.items() if k != "_id"} async for doc in cursor]
    return {"alerts": alerts}


@app.get("/api/users/logs")
async def user_logs(user: dict = Depends(authenticate_request)):
    projection = {
        "username": 1,
        "name": 1,
        "role": 1,
        "email": 1,
        "last_login": 1,
        "created_at": 1,
        "is_active": 1,
    }
    cursor = db["users"].find({}, projection).sort("last_login", -1)
    users = [u async for u in cursor]
    for u in users:
        u.pop("_id", None)
    return {"users": users}


# Campus and Energy routes
@app.get("/api/campuses")
async def get_campuses(user: dict = Depends(authenticate_request)):
    """Get all campuses with their energy data"""
    cursor = db["campuses"].find({})
    campuses = []
    async for campus in cursor:
        campus.pop("_id", None)
        # Get latest energy data for this campus
        energy_data = await db["energy_data"].find_one(
            {"campus_id": campus["id"]},
            sort=[("timestamp", -1)]
        )
        if energy_data:
            campus["energyData"] = {
                "solar": energy_data.get("solar", 0),
                "wind": energy_data.get("wind", 0),
                "battery": {
                    "charge": energy_data.get("battery_charge", 0),
                    "health": energy_data.get("battery_health", 0),
                    "cycles": energy_data.get("battery_cycles", 0)
                },
                "load": energy_data.get("load", 0),
                "grid": energy_data.get("grid", 0),
                "timestamp": energy_data.get("timestamp")
            }
        campuses.append(campus)
    return {"campuses": campuses}


@app.get("/api/regions")
async def get_regions(user: dict = Depends(authenticate_request)):
    """Get all regions"""
    cursor = db["regions"].find({})
    regions = []
    async for region in cursor:
        region.pop("_id", None)
        regions.append(region)
    return {"regions": regions}


@app.get("/api/user/points")
async def get_user_points(user: dict = Depends(authenticate_request)):
    """Get user points and rankings"""
    cursor = db["user_points"].find({}).sort("rank", 1)
    points = []
    async for point in cursor:
        point.pop("_id", None)
        points.append(point)
    return {"points": points}


@app.get("/api/priority-requests")
async def get_priority_requests(user: dict = Depends(authenticate_request)):
    """Get all priority requests"""
    cursor = db["priority_requests"].find({}).sort("created_at", -1)
    requests = []
    async for req in cursor:
        req.pop("_id", None)
        requests.append(req)
    return {"requests": requests}


@app.post("/api/priority-requests")
async def create_priority_request(request: dict, user: dict = Depends(authenticate_request)):
    """Create a new priority request"""
    import uuid
    new_request = {
        "id": str(uuid.uuid4()),
        "type": request.get("type"),
        "priority": request.get("priority"),
        "occupancy": request.get("occupancy"),
        "jvvnlId": request.get("jvvnlId"),
        "active": request.get("active", True),
        "created_at": datetime.utcnow(),
        "machine_id": request.get("machine_id"),
        "status": "Pending"
    }
    await db["priority_requests"].insert_one(new_request)
    new_request.pop("_id", None)
    return {"request": new_request}


@app.put("/api/priority-requests/{request_id}")
async def update_priority_request(request_id: str, request: dict, user: dict = Depends(authenticate_request)):
    """Update a priority request"""
    result = await db["priority_requests"].update_one(
        {"id": request_id},
        {"$set": request}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    return {"message": "Request updated successfully"}


@app.get("/api/voice-commands")
async def get_voice_commands(user: dict = Depends(authenticate_request)):
    """Get voice command history"""
    cursor = db["voice_commands"].find({}).sort("timestamp", -1).limit(20)
    commands = []
    async for cmd in cursor:
        cmd.pop("_id", None)
        commands.append(cmd)
    return {"commands": commands}


@app.post("/api/voice-commands")
async def create_voice_command(command: dict, user: dict = Depends(authenticate_request)):
    """Log a voice command"""
    new_command = {
        "command": command.get("command"),
        "mode": command.get("mode"),
        "language": command.get("language", "en"),
        "confidence": command.get("confidence", 0.0),
        "timestamp": datetime.utcnow(),
        "success": command.get("success", False)
    }
    await db["voice_commands"].insert_one(new_command)
    new_command.pop("_id", None)
    return {"command": new_command}


@app.get("/api/energy/kpi")
async def get_energy_kpi(user: dict = Depends(authenticate_request)):
    """Get energy KPIs across all campuses"""
    # Calculate aggregated KPIs
    campuses = await db["campuses"].find({}).to_list(length=None)
    
    if not campuses:
        return {
            "kpi": {
                "renewableUtilization": 0,
                "gridDependency": 0,
                "carbonSavings": 0,
                "costReduction": 0
            }
        }
    
    total_renewable = sum(c.get("renewableUtilization", 0) for c in campuses)
    total_grid = sum(c.get("gridDependency", 0) for c in campuses)
    total_carbon = sum(c.get("carbonSavings", 0) for c in campuses)
    
    count = len(campuses)
    
    return {
        "kpi": {
            "renewableUtilization": round(total_renewable / count, 1),
            "gridDependency": round(total_grid / count, 1),
            "carbonSavings": round(total_carbon, 1),
            "costReduction": round((total_renewable / count) * 0.5, 1)  # Estimated cost reduction
        }
    }


@app.get("/api/energy/history")
async def get_energy_history(campus_id: str = None, hours: int = 24):
    """Get energy data history"""
    query = {}
    if campus_id:
        query["campus_id"] = campus_id
    
    cursor = db["energy_data"].find(query).sort("timestamp", -1).limit(hours)
    history = []
    async for data in cursor:
        data.pop("_id", None)
        history.append(data)
    
    return {"history": history}


@app.on_event("shutdown")
async def shutdown_event():
    client.close()

