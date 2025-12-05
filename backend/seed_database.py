"""
Seed script to populate MongoDB with initial data
Run this script to initialize the database with mock data
"""
from database import get_sync_db
from datetime import datetime, timedelta
import random

def seed_database():
    db = get_sync_db()
    
    print("🌱 Seeding database...")
    
    # Clear existing data
    print("Clearing existing data...")
    db.energy_data.delete_many({})
    db.users.delete_many({})
    db.leaderboard.delete_many({})
    db.admin_settings.delete_many({})
    db.priority_requests.delete_many({})
    db.regional_data.delete_many({})
    db.system_status.delete_many({})
    
    # Seed Energy Data (last 100 data points)
    print("Seeding energy data...")
    energy_data = []
    base_time = datetime.now()
    
    for i in range(100):
        timestamp = base_time - timedelta(seconds=i * 3)
        is_operating = random.random() > 0.1
        
        solar = (70 + random.random() * 25) if is_operating else 0
        wind = (15 + random.random() * 10) if is_operating else 0
        consumption = (3.5 + random.random() * 1.5) if is_operating else 0
        grid = (800 + random.random() * 100) if is_operating else 0
        battery_level = 75 + random.random() * 20
        
        energy_data.append({
            "solar": solar,
            "wind": wind,
            "grid": grid,
            "battery": {
                "level": battery_level,
                "health": 92 + random.random() * 6
            },
            "consumption": consumption,
            "timestamp": timestamp
        })
    
    db.energy_data.insert_many(energy_data)
    print(f"✅ Inserted {len(energy_data)} energy data points")
    
    # Seed Users
    print("Seeding users...")
    users = [
        {
            "id": "1",
            "name": "Praveen Kumar",
            "region": "Mining Operations",
            "points": 1850,
            "renewableUsage": 78.5,
            "rank": 12,
            "badges": ["Efficiency Expert", "Process Optimizer", "Safety Champion", "AI Pioneer"]
        }
    ]
    db.users.insert_many(users)
    print(f"✅ Inserted {len(users)} users")
    
    # Seed Leaderboard
    print("Seeding leaderboard...")
    leaderboard = [
        {"id": "1", "name": "Rajesh Sharma", "region": "Circuit A", "points": 2450, "renewableUsage": 89.2, "rank": 1},
        {"id": "2", "name": "Priya Gupta", "region": "Circuit B", "points": 2380, "renewableUsage": 87.5, "rank": 2},
        {"id": "3", "name": "Amit Singh", "region": "Circuit C", "points": 2290, "renewableUsage": 85.1, "rank": 3},
        {"id": "4", "name": "Sunita Devi", "region": "Circuit D", "points": 2150, "renewableUsage": 82.3, "rank": 4},
        {"id": "5", "name": "Vikram Rathore", "region": "Circuit E", "points": 2050, "renewableUsage": 80.7, "rank": 5},
        {"id": "6", "name": "Meera Patel", "region": "Circuit F", "points": 1980, "renewableUsage": 79.8, "rank": 6},
        {"id": "7", "name": "Arjun Verma", "region": "Circuit G", "points": 1920, "renewableUsage": 79.1, "rank": 7},
        {"id": "8", "name": "Kavita Nair", "region": "Circuit H", "points": 1890, "renewableUsage": 78.9, "rank": 8},
        {"id": "9", "name": "Rohit Desai", "region": "Circuit I", "points": 1870, "renewableUsage": 78.7, "rank": 9},
        {"id": "10", "name": "Lakshmi Reddy", "region": "Circuit J", "points": 1860, "renewableUsage": 78.6, "rank": 10},
        {"id": "11", "name": "Sanjay Kumar", "region": "Circuit K", "points": 1855, "renewableUsage": 78.55, "rank": 11},
        {"id": "12", "name": "Praveen Kumar", "region": "Mining Operations", "points": 1850, "renewableUsage": 78.5, "rank": 12}
    ]
    db.leaderboard.insert_many(leaderboard)
    print(f"✅ Inserted {len(leaderboard)} leaderboard entries")
    
    # Seed Admin Settings
    print("Seeding admin settings...")
    admin_settings = {
        "type": "settings",
        "energyMode": "Auto Mode",
        "mlAutoMode": False
    }
    db.admin_settings.insert_one(admin_settings)
    print("✅ Inserted admin settings")
    
    # Seed Priority Requests
    print("Seeding priority requests...")
    priority_requests = [
        {
            "id": "1",
            "facility": "Crusher Unit 1",
            "priority": "High",
            "reason": "Liner wear detected - maintenance required",
            "status": "Pending",
            "timestamp": datetime.now() - timedelta(hours=2)
        },
        {
            "id": "2",
            "facility": "Ball Mill 2",
            "priority": "Medium",
            "reason": "Efficiency optimization needed",
            "status": "Approved",
            "timestamp": datetime.now() - timedelta(hours=4)
        },
        {
            "id": "3",
            "facility": "Conveyor System 3",
            "priority": "Low",
            "reason": "Routine inspection scheduled",
            "status": "Pending",
            "timestamp": datetime.now() - timedelta(hours=6)
        }
    ]
    db.priority_requests.insert_many(priority_requests)
    print(f"✅ Inserted {len(priority_requests)} priority requests")
    
    # Seed Regional Data
    print("Seeding regional data...")
    regional_data = [
        {"region": "Circuit A", "usage": 85.2, "trend": "+12%"},
        {"region": "Circuit B", "usage": 78.9, "trend": "+8%"},
        {"region": "Circuit C", "usage": 82.1, "trend": "+15%"},
        {"region": "Circuit D", "usage": 76.5, "trend": "+5%"},
        {"region": "Circuit E", "usage": 79.3, "trend": "+10%"},
        {"region": "Circuit F", "usage": 81.7, "trend": "+7%"}
    ]
    db.regional_data.insert_many(regional_data)
    print(f"✅ Inserted {len(regional_data)} regional data entries")
    
    # Seed System Status
    print("Seeding system status...")
    system_status = [
        {"name": "Crusher Unit", "status": True},
        {"name": "Ball Mill", "status": True},
        {"name": "Conveyor System", "status": True},
        {"name": "AI Control", "status": True}
    ]
    db.system_status.insert_many(system_status)
    print(f"✅ Inserted {len(system_status)} system status entries")
    
    print("\n✅ Database seeding completed successfully!")
    print("\nCollections created:")
    print("  - energy_data (100 entries)")
    print("  - users (1 entry)")
    print("  - leaderboard (12 entries)")
    print("  - admin_settings (1 entry)")
    print("  - priority_requests (3 entries)")
    print("  - regional_data (6 entries)")
    print("  - system_status (4 entries)")

if __name__ == "__main__":
    seed_database()
