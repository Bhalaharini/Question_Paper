from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Energy Data Models
class BatteryData(BaseModel):
    level: float
    health: float

class EnergyData(BaseModel):
    solar: float
    wind: float
    grid: float
    battery: BatteryData
    consumption: float
    timestamp: datetime = Field(default_factory=datetime.now)

class EnergyDataResponse(BaseModel):
    energyData: EnergyData
    renewablePercentage: float
    isOnline: bool
    alerts: List[str]
    historicalData: List[EnergyData]

# User Data Models
class UserData(BaseModel):
    id: str
    name: str
    region: str
    points: int
    renewableUsage: float
    rank: int
    badges: List[str]

class LeaderboardUser(BaseModel):
    id: str
    name: str
    region: str
    points: int
    renewableUsage: float
    rank: int

class UpdatePointsRequest(BaseModel):
    userId: str
    points: int

class AddBadgeRequest(BaseModel):
    userId: str
    badge: str

# Admin Data Models
class PriorityRequest(BaseModel):
    id: str
    facility: str
    priority: str  # 'Low' | 'Medium' | 'High' | 'Critical'
    reason: str
    status: str  # 'Pending' | 'Approved' | 'Rejected'
    timestamp: datetime

class CreatePriorityRequest(BaseModel):
    facility: str
    priority: str
    reason: str

class UpdateRequestStatusRequest(BaseModel):
    requestId: str
    status: str  # 'Approved' | 'Rejected'

class RegionalData(BaseModel):
    region: str
    usage: float
    trend: str

class AdminSettings(BaseModel):
    energyMode: str
    mlAutoMode: bool

class SystemStatus(BaseModel):
    name: str
    status: bool

class AdminDataResponse(BaseModel):
    energyMode: str
    mlAutoMode: bool
    systemStatus: dict
    priorityRequests: List[PriorityRequest]
    regionalData: List[RegionalData]
