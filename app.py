from utility.validate_utils import parse_csv
from flask import Flask, request, jsonify
from image_processing import process_images_task
from model import create_request_record, delete_all_records, get_request_status
import uuid
import csv
import asyncio
from quart import Quart, request, jsonify
from quart_cors import cors
from quart import send_file, jsonify
from model import get_request_status, download_csv

app = Quart(__name__)

# Enable CORS for the entire app, allowing requests from any origin
app = cors(app, allow_origin="*")


# Upload API to accept the CSV file
@app.route("/upload", methods=["POST"])
async def upload():
    # Get the form data and files asynchronously
    form = await request.files  # Wait for the form data to be fully available

    if "file" not in form:
        return jsonify({"error": "No file provided"}), 400

    file = form["file"]  # Access the file object after awaiting form data
    if not file.filename.endswith(".csv"):
        return jsonify({"error": "Invalid file type"}), 400

    # Parse CSV and validate format (assuming parse_csv is your custom function)
    rows, error = parse_csv(file)
    if error:
        return jsonify({"error": error}), 400

    # Generate a unique request ID
    request_id = str(uuid.uuid4())

    # Create a new request record in MongoDB with 'Pending' status
    create_request_record(request_id, rows)

    # Trigger async image processing in the background using asyncio.create_task
    asyncio.create_task(process_images_task(request_id, rows))  # Run asynchronously

    # Immediately return the request ID without waiting for processing
    return jsonify({"request_id": request_id}), 200


@app.route("/status/<request_id>", methods=["GET"])
def status(request_id):
    request_record = get_request_status(request_id)

    if not request_record:
        return jsonify({"error": "Request ID not found"}), 404

    return (
        jsonify({"status": request_record.get("status", "Unknown")}),
        200,
    )


# @app.route("/webhook", methods=["POST"])
# def webhook():
#     data = request.get_json()
#     request_id = data.get("request_id")
#     output_images = data.get("output_images")

#     # Update the request status to complete
#     update_request_status(request_id, "Completed", output_images)

#     return jsonify({"message": "Webhook received successfully"}), 200


@app.route("/delete-all", methods=["DELETE"])
def delete_all():
    try:
        deleted_count = delete_all_records()
        return (
            jsonify({"message": f"Deleted {deleted_count} records successfully"}),
            200,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/download/<request_id>", methods=["GET"])
async def download_processed_csv(request_id):
    """Download the processed CSV file for a given request ID."""
    try:
        # Call the download_csv function
        file_or_redirect, error_message = await download_csv(request_id)

        if file_or_redirect:
            if isinstance(file_or_redirect, dict):  # S3 URL
                # Return a JSON response with CORS headers for S3 redirection
                response = jsonify(file_or_redirect)
                response.headers["Access-Control-Allow-Origin"] = (
                    "*"  # Manually add CORS headers
                )
                return response, 200

            # For local file response, directly return without awaiting the response
            response = file_or_redirect  # Do not await send_file return
            response.headers["Access-Control-Allow-Origin"] = (
                "*"  # Add CORS headers for file download
            )
            return response

        # Handle case when file or redirect isn't available
        return jsonify({"error": error_message}), 404

    except Exception as e:
        # Log the error if needed, and return 500 for unhandled exceptions
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
