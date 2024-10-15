# app/database.py
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import MONGO_DETAILS

client = AsyncIOMotorClient(MONGO_DETAILS)
db = client['annotated_images']
projects_collection = db['projects']
images_collection = db['images']
db1 = client['text_annotation_db']
text_projects_collection = db1['text_projects']
ner_annotations_collection = db1['ner_annotations']