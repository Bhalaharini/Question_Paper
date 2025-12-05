from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import certifi

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    raise ValueError("MONGODB_URI environment variable is not set")

# Async client for FastAPI
async_client = AsyncIOMotorClient(MONGODB_URI, tlsCAFile=certifi.where())
async_db = async_client.sih_database

# Collections
energy_collection = async_db.energy_data
users_collection = async_db.users
leaderboard_collection = async_db.leaderboard
admin_collection = async_db.admin_settings
priority_requests_collection = async_db.priority_requests
regional_data_collection = async_db.regional_data
system_status_collection = async_db.system_status

# Sync client for seeding data
sync_client = None
sync_db = None

def get_sync_db():
    global sync_client, sync_db
    if sync_client is None:
        sync_client = MongoClient(MONGODB_URI, tlsCAFile=certifi.where())
        sync_db = sync_client.sih_database
    return sync_db
