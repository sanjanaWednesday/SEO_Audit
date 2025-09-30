from pymongo import MongoClient
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client.get_database("seo_audit")

def create_test_document():
    collection = db.workflow_executions
    test_doc = {
        "site_url": "https://example.com",
        "status": "started",
        "start_time": datetime.utcnow()
    }
    result = collection.insert_one(test_doc)
    print("Inserted document ID:", result.inserted_id)

if __name__ == "__main__":
    create_test_document()
    print("Collections now:", db.list_collection_names())
