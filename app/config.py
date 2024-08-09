# app/config.py
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_DETAILS = "mongodb+srv://Mohit:Tz4O610okBOvSpIu@cluster0.a2yzwap.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = AsyncIOMotorClient(MONGO_DETAILS)
db = client['annotated_images']
projects_collection = db['projects']
images_collection = db['images']
