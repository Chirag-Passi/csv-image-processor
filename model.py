from pymongo import MongoClient
from datetime import datetime
from bson.json_util import dumps
from bson import InvalidDocument
from quart import jsonify, send_file
import os
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB configuration
client = MongoClient(
    "mongodb+srv://admin:root@pythonapp.vlzqg.mongodb.net/?retryWrites=true&w=majority&appName=pythonApp"
)
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


async def download_csv(request_id):
    """Download the processed CSV for a given request ID."""
    # Await the URL fetching function
    output_csv_url = await get_output_csv_url(request_id)

    if not output_csv_url:
        return None, "CSV not available or processing not complete"

    # If the CSV is stored in S3 or another HTTP URL, return the URL as a dictionary
    if output_csv_url.startswith("http"):
        return {"redirect_url": output_csv_url}, None  # Return the S3 URL

    # If stored locally, serve the file using Quart's send_file
    if os.path.exists(output_csv_url):
        # Use send_file without awaiting it
        return (
            await send_file(
                output_csv_url,
                as_attachment=True,
                download_name=f"{request_id}_processed.csv",  # Correct usage for Quart
            ),
            None,
        )

    return None, "CSV file not found"


async def get_output_csv_url(request_id):
    """Fetch the output CSV file URL from the database."""
    # Await the database query
    request_record = await requests_collection.find_one({"_id": request_id})

    if not request_record or "output_csv_url" not in request_record:
        return None

    # Return the actual URL or local file path
    return request_record["output_csv_url"]


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


# Function to update image URLs in the MongoDB
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
