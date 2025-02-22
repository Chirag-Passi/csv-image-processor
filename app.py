from utility.validate_utils import parse_csv
from flask import Flask, request, jsonify
from quart import Quart, request, jsonify
from image_processing import process_images_task
from model import create_request_record, delete_all_records, get_request_status
import uuid
import csv


# app = Flask(__name__)
app = Quart(__name__)


@app.route("/upload", methods=["POST"])
async def upload():
    # Get the form data and files asynchronously
    form = await request.files  # Wait for the form data to be fully available

    if "file" not in form:
        return jsonify({"error": "No file provided"}), 400

    file = form["file"]  # Access the file object after awaiting form data
    if not file.filename.endswith(".csv"):
        return jsonify({"error": "Invalid file type"}), 400

    rows, error = parse_csv(file)
    if error:
        return jsonify({"error": error}), 400

    request_id = str(uuid.uuid4())

    # Store request record in MongoDB
    create_request_record(request_id, rows)

    # Trigger async image processing
    await process_images_task(request_id, rows)

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


if __name__ == "__main__":
    app.run(debug=True)
