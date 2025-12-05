"""
Seed script to populate MongoDB Atlas with sample data.

Usage:
    python app/seed.py

Requires MONGODB_URL environment variable or .env file.
"""

import asyncio
import os
import ssl
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import bcrypt
import certifi
import random
import uuid

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/sih")


async def seed_database():
    """Seed the database with sample users, alerts, and machine data."""
    
    client = AsyncIOMotorClient(
        MONGODB_URL, 
        serverSelectionTimeoutMS=30000,
        tlsCAFile=certifi.where()
    )
    # Extract database name from URL or use default
    db_name = os.getenv("MONGODB_DB", "sih")
    db = client[db_name]
    
    print(f"Connected to MongoDB: {db.name}")
    
    # Clear existing data (optional - comment out if you want to keep existing data)
    print("Clearing existing data...")
    await db["users"].delete_many({})
    await db["alerts"].delete_many({})
    await db["machine1datas"].delete_many({})
    await db["machine2datas"].delete_many({})
    await db["machine3datas"].delete_many({})
    await db["campuses"].delete_many({})
    await db["regions"].delete_many({})
    await db["priority_requests"].delete_many({})
    await db["user_points"].delete_many({})
    await db["voice_commands"].delete_many({})
    await db["energy_data"].delete_many({})
    
    # Seed users
    print("Seeding users...")
    users = [
        {
            "username": "admin",
            "password_hash": bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode(),
            "role": "admin",
            "name": "Admin User",
            "email": "admin@mining.com",
            "campus": "Main Campus",
            "created_at": datetime.utcnow(),
            "is_active": True,
            "last_login": datetime.utcnow() - timedelta(hours=2),
        },
        {
            "username": "operator1",
            "password_hash": bcrypt.hashpw("operator123".encode(), bcrypt.gensalt()).decode(),
            "role": "user",
            "name": "John Operator",
            "email": "operator1@mining.com",
            "campus": "North Campus",
            "created_at": datetime.utcnow() - timedelta(days=30),
            "is_active": True,
            "last_login": datetime.utcnow() - timedelta(hours=5),
        },
        {
            "username": "engineer1",
            "password_hash": bcrypt.hashpw("engineer123".encode(), bcrypt.gensalt()).decode(),
            "role": "user",
            "name": "Jane Engineer",
            "email": "engineer1@mining.com",
            "campus": "South Campus",
            "created_at": datetime.utcnow() - timedelta(days=45),
            "is_active": True,
            "last_login": datetime.utcnow() - timedelta(hours=1),
        },
        {
            "username": "govt1",
            "password_hash": bcrypt.hashpw("govt123".encode(), bcrypt.gensalt()).decode(),
            "role": "government",
            "name": "Government Observer",
            "email": "govt@mining.com",
            "campus": "Central Office",
            "created_at": datetime.utcnow() - timedelta(days=60),
            "is_active": True,
            "last_login": datetime.utcnow() - timedelta(hours=24),
        },
    ]
    result = await db["users"].insert_many(users)
    user_ids = result.inserted_ids
    print(f"Created {len(users)} users")
    
    # Seed campuses
    print("Seeding campuses...")
    campuses = [
        {
            "id": "1",
            "name": "Main Campus",
            "renewableUtilization": 85.2,
            "gridDependency": 14.8,
            "carbonSavings": 1250.0,
            "created_at": datetime.utcnow()
        },
        {
            "id": "2",
            "name": "North Campus",
            "renewableUtilization": 72.8,
            "gridDependency": 27.2,
            "carbonSavings": 890.0,
            "created_at": datetime.utcnow()
        },
        {
            "id": "3",
            "name": "South Campus",
            "renewableUtilization": 67.3,
            "gridDependency": 32.7,
            "carbonSavings": 707.0,
            "created_at": datetime.utcnow()
        }
    ]
    await db["campuses"].insert_many(campuses)
    print(f"Created {len(campuses)} campuses")
    
    # Seed energy data
    print("Seeding energy data...")
    energy_data = []
    for campus in campuses:
        for i in range(24):
            timestamp = datetime.utcnow() - timedelta(hours=23-i)
            energy_data.append({
                "campus_id": campus["id"],
                "campus_name": campus["name"],
                "solar": random.uniform(150, 300) if 6 <= i <= 18 else random.uniform(0, 50),
                "wind": random.uniform(40, 100),
                "battery_charge": random.uniform(60, 95),
                "battery_health": random.uniform(85, 95),
                "battery_cycles": random.randint(800, 1500),
                "load": random.uniform(150, 250),
                "grid": random.uniform(0, 80),
                "timestamp": timestamp
            })
    await db["energy_data"].insert_many(energy_data)
    print(f"Created {len(energy_data)} energy data points")
    
    # Seed regions
    print("Seeding regions...")
    regions = [
        {
            "id": "region-1",
            "name": "North Zone",
            "type": "solar",
            "usage": 245.5,
            "coordinates": [28.6139, 77.2090],
            "campuses": ["Main Campus", "North Campus"],
            "solar": 320.0,
            "wind": 85.0,
            "load": 180.0,
            "points": 1250,
            "created_at": datetime.utcnow()
        },
        {
            "id": "region-2",
            "name": "South Zone",
            "type": "wind",
            "usage": 180.3,
            "coordinates": [12.9716, 77.5946],
            "campuses": ["South Campus"],
            "solar": 180.0,
            "wind": 165.0,
            "load": 220.0,
            "points": 890,
            "created_at": datetime.utcnow()
        },
        {
            "id": "region-3",
            "name": "East Zone",
            "type": "solar",
            "usage": 195.7,
            "coordinates": [22.5726, 88.3639],
            "campuses": [],
            "solar": 210.0,
            "wind": 95.0,
            "load": 165.0,
            "points": 1050,
            "created_at": datetime.utcnow()
        }
    ]
    await db["regions"].insert_many(regions)
    print(f"Created {len(regions)} regions")
    
    # Seed user points
    print("Seeding user points...")
    user_points = [
        {
            "userId": str(user_ids[1]),
            "userName": "John Operator",
            "campus": "North Campus",
            "points": 1250,
            "renewableUsage": 85.2,
            "rank": 1,
            "created_at": datetime.utcnow()
        },
        {
            "userId": str(user_ids[2]),
            "userName": "Jane Engineer",
            "campus": "South Campus",
            "points": 890,
            "renewableUsage": 72.8,
            "rank": 2,
            "created_at": datetime.utcnow()
        },
        {
            "userId": str(user_ids[0]),
            "userName": "Admin User",
            "campus": "Main Campus",
            "points": 1450,
            "renewableUsage": 90.5,
            "rank": 1,
            "created_at": datetime.utcnow()
        }
    ]
    await db["user_points"].insert_many(user_points)
    print(f"Created {len(user_points)} user points records")
    
    # Seed priority requests
    print("Seeding priority requests...")
    priority_types = ['exam_center', 'classroom', 'hostel', 'lab', 'office']
    priority_levels = ['grid', 'solar', 'wind', 'solar+wind', 'solar+wind+grid']
    priority_requests = []
    
    for i in range(10):
        priority_requests.append({
            "id": str(uuid.uuid4()),
            "type": random.choice(priority_types),
            "priority": random.choice(priority_levels),
            "occupancy": random.randint(20, 100) if random.choice([True, False]) else None,
            "jvvnlId": f"JVVNL-{random.randint(1000, 9999)}" if random.choice([True, False]) else None,
            "active": random.choice([True, False]),
            "created_at": datetime.utcnow() - timedelta(hours=random.randint(1, 72)),
            "machine_id": f"machine-{random.choice(['01', '02', '03'])}",
            "status": random.choice(["Pending", "Approved", "Rejected"])
        })
    
    await db["priority_requests"].insert_many(priority_requests)
    print(f"Created {len(priority_requests)} priority requests")
    
    # Seed voice commands
    print("Seeding voice commands...")
    voice_commands = [
        {
            "command": "Switch to solar mode",
            "mode": "solar",
            "language": "en",
            "confidence": 0.95,
            "timestamp": datetime.utcnow() - timedelta(hours=5),
            "success": True
        },
        {
            "command": "Enable wind power",
            "mode": "wind",
            "language": "en",
            "confidence": 0.88,
            "timestamp": datetime.utcnow() - timedelta(hours=12),
            "success": True
        },
        {
            "command": "Activate hybrid mode",
            "mode": "solar+wind",
            "language": "en",
            "confidence": 0.92,
            "timestamp": datetime.utcnow() - timedelta(hours=24),
            "success": True
        },
        {
            "command": "Switch to grid backup",
            "mode": "grid",
            "language": "en",
            "confidence": 0.85,
            "timestamp": datetime.utcnow() - timedelta(hours=36),
            "success": True
        }
    ]
    await db["voice_commands"].insert_many(voice_commands)
    print(f"Created {len(voice_commands)} voice commands")
    
    # Seed alerts
    print("Seeding alerts...")
    severities = ['low', 'medium', 'high', 'critical']
    alert_messages = [
        "High vibration detected",
        "Motor temperature elevated",
        "Scheduled maintenance due",
        "Power consumption spike",
        "Belt speed irregularity",
        "Low battery health warning",
        "Grid dependency increased",
        "Solar panel efficiency drop",
        "Wind turbine maintenance required",
        "Energy storage capacity low"
    ]
    
    alerts = []
    for i in range(15):
        alerts.append({
            "machine_id": f"machine-{random.choice(['01', '02', '03'])}",
            "message": random.choice(alert_messages),
            "severity": random.choice(severities),
            "created_by": "system",
            "created_at": datetime.utcnow() - timedelta(hours=random.randint(1, 120)),
            "is_resolved": random.choice([True, False, False, False]),  # 75% unresolved
        })
    
    await db["alerts"].insert_many(alerts)
    print(f"Created {len(alerts)} alerts")
    
    # Seed machine data
    print("Seeding machine data...")
    
    machines = [
        ("machine-01", "machine1datas"),
        ("machine-02", "machine2datas"),
        ("machine-03", "machine3datas"),
    ]
    
    for machine_id, collection_name in machines:
        data_points = []
        base_time = datetime.utcnow() - timedelta(hours=24)
        
        for i in range(48):  # 48 data points (every 30 minutes for 24 hours)
            timestamp = base_time + timedelta(minutes=30 * i)
            
            # Generate synthetic data with some variation
            data_points.append({
                "machine_id": machine_id,
                "timestamp": timestamp,
                "rock_size_mm": random.uniform(10, 50),
                "weight_kg": random.uniform(500, 2000),
                "moisture_pct": random.uniform(5, 15),
                "flow_rate": random.uniform(80, 150),
                "motor_current_A": random.uniform(10, 30),
                "motor_voltage_V": random.uniform(380, 420),
                "belt_speed_pwm": random.uniform(50, 100),
                "vibration_level": random.uniform(0.1, 2.5),
                "predicted_power_W": random.uniform(15000, 35000),
                "machine_status": "running" if i < 45 else "stopped",
            })
        
        await db[collection_name].insert_many(data_points)
        print(f"Created {len(data_points)} data points for {machine_id}")
    
    print("\n✅ Database seeded successfully!")
    print("\nTest credentials:")
    print("  Username: admin      | Password: admin123    | Role: admin")
    print("  Username: operator1  | Password: operator123 | Role: user")
    print("  Username: engineer1  | Password: engineer123 | Role: user")
    print("  Username: govt1      | Password: govt123     | Role: government")
    print(f"\nTotal records created:")
    print(f"  - Users: {len(users)}")
    print(f"  - Campuses: {len(campuses)}")
    print(f"  - Energy Data: {len(energy_data)}")
    print(f"  - Regions: {len(regions)}")
    print(f"  - User Points: {len(user_points)}")
    print(f"  - Priority Requests: {len(priority_requests)}")
    print(f"  - Voice Commands: {len(voice_commands)}")
    print(f"  - Alerts: {len(alerts)}")
    print(f"  - Machine Data Points: {48 * 3}")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(seed_database())
