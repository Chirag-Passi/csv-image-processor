from pymongo import MongoClient
from datetime import datetime
from bson.json_util import dumps
from bson import InvalidDocument

# MongoDB configuration
client = MongoClient(
    "mongodb+srv://admin:root@pythonapp.vlzqg.mongodb.net/?retryWrites=true&w=majority&appName=pythonApp"
)
db = client["image_processing_db"]
requests_collection = db["requests"]


def create_request_record(request_id, rows):
    try:
        record = {
            "_id": request_id,
            "status": "Processing",
            "rows": rows,  # Assuming 'rows' is a list of URLs or other data
        }
        db.requests.insert_one(record)
        print(f"Record inserted successfully with request ID: {request_id}")
    except InvalidDocument as e:
        print(f"Failed to insert record: {e}")


async def update_request_status(request_id, status, output_images=[]):
    requests_collection.update_one(
        {"request_id": request_id},
        {
            "$set": {
                "status": status,
                "output_images": output_images,
                "processed_at": datetime.utcnow(),
            }
        },
    )


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


async def update_image_urls_in_db(request_id, s3_urls):
    """Update the document in MongoDB with the new S3 URLs."""
    requests_collection.update_one(
        {"_id": request_id},
        {
            "$set": {
                "output_images": s3_urls,
                "status": "Completed",
                "processed_at": datetime.utcnow(),
            }
        },
    )
