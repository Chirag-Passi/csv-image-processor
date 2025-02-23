from pymongo import MongoClient
from datetime import datetime
from bson.json_util import dumps
from bson import InvalidDocument
from quart import jsonify, send_file
import os
from quart import send_file
from dotenv import load_dotenv

load_dotenv()

MONGGO_API_KEY = os.getenv("MONGGO_API_KEY")

# MongoDB configuration
client = MongoClient(MONGGO_API_KEY)
db = client["image_processing_db"]
requests_collection = db["requests"]


# Function to create a record in MongoDB
def create_request_record(request_id, rows):
    """Insert a new request record into the MongoDB database."""
    requests_collection.insert_one(
        {
            "_id": request_id,
            "status": "Pending",
            "input": rows,
            "created_at": datetime.utcnow(),
            "processed_at": None,
        }
    )


async def get_request_response(request_id):
    """Fetch the request record from MongoDB for the given request ID asynchronously."""
    try:
        request_record = requests_collection.find_one({"_id": request_id})
        if not request_record:
            return None, "Request not found"
        return request_record, None
    except Exception as e:
        return None, f"Error while fetching request: {str(e)}"


def get_request_status(request_id):
    try:
        request_record = requests_collection.find_one({"_id": request_id})
        if not request_record:
            return None
    except Exception as e:
        print(f"Error while fetching request: {str(e)}")
        return None

    return request_record


def delete_all_records():
    collections = db.list_collection_names()
    deleted_count = 0

    for collection in collections:
        result = db[collection].delete_many({})
        deleted_count += result.deleted_count

    return deleted_count


async def update_output_url_in_db(request_id, row_idx, s3_url):
    """Update the MongoDB document with the processed S3 URL for the specific row and image."""
    # Use the array filter to update the output URL in the correct row
    await requests_collection.update_one(
        {"_id": request_id},
        {"$push": {f"output_images.{row_idx}.Output Images URLs": s3_url}},
    )


def update_processing_status_in_db(request_id):
    """Update the status to 'Completed' and add the processed timestamp in MongoDB."""
    requests_collection.update_one(
        {"_id": request_id},
        {"$set": {"status": "Completed", "processed_at": datetime.utcnow()}},
    )
