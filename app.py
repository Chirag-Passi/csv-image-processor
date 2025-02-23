from utility.validate_utils import parse_csv
from flask import request, jsonify
from image_processing import process_images_task
from model import (
    create_request_record,
    delete_all_records,
    get_request_status,
    get_request_response,
)
import uuid
import csv
import asyncio
import io
from quart import Quart, request, jsonify
from quart_cors import cors
from quart import send_file, jsonify
from model import get_request_status


app = Quart(__name__)
app = cors(app, allow_origin="*")


# Upload API to accept the CSV file
@app.route("/upload", methods=["POST"])
async def upload():
    form = await request.files 

    if "file" not in form:
        return jsonify({"error": "No file provided"}), 400

    file = form["file"]
    if not file.filename.endswith(".csv"):
        return jsonify({"error": "Invalid file type"}), 400

    rows, error = parse_csv(file)
    if error:
        return jsonify({"error": error}), 400

    # Generate a unique request ID
    request_id = str(uuid.uuid4())

    # Create a new request record in MongoDB with 'Pending' status
    create_request_record(request_id, rows)
    asyncio.create_task(process_images_task(request_id, rows))  
    return jsonify({"request_id": request_id}), 200


# Status API
@app.route("/status/<request_id>", methods=["GET"])
def status(request_id):
    request_record = get_request_status(request_id)

    if not request_record:
        return jsonify({"error": "Request ID not found"}), 404

    return (
        jsonify({"status": request_record.get("status", "Unknown")}),
        200,
    )


# Download CSV File API
@app.route("/download/<request_id>", methods=["GET"])
async def download_processed_csv(request_id):
    """Download the processed CSV file for a given request ID."""
    try:
        # Check if the request has completed processing
        request_status = get_request_status(request_id)
        if not request_status:
            return jsonify({"error": "Request not found"}), 404

        # Check if the status is not "Completed"
        if request_status.get("status") != "Completed":
            return (
                jsonify(
                    {"message": "Processing is still in progress. Try again later."}
                ),
                202,
            )
        
        request_record, error = await get_request_response(request_id)

        if error or not request_record:
            print(f"Error: {error}")  # Log the error for debugging
            return jsonify({"error": error or "Request not found"}), 404

        print(f"Record found: {request_record}")

        input_data = request_record.get("input", [])
        output_data = request_record.get("output_images", {})

        csv_output = io.StringIO()
        csv_writer = csv.writer(csv_output)

        csv_writer.writerow(
            ["S. No.", "Product Name", "Input Image URLs", "Output Image URLs"]
        )

        for index, row in enumerate(input_data):
            serial_number = row.get("S. No.")
            product_name = row.get("Product Name")
            input_urls = ", ".join(
                row.get("Input Image Urls", [])
            )

            output_idx = str(index)
            output_urls = output_data.get(output_idx, {}).get("Output Images URLs", [])
            output_urls_str = ", ".join(output_urls)

            csv_writer.writerow(
                [serial_number, product_name, input_urls, output_urls_str]
            )

        csv_output.seek(0)
        bytes_io = io.BytesIO(csv_output.getvalue().encode())

        return await send_file(
            bytes_io,
            attachment_filename=f"{request_id}_processed.csv",
            mimetype="text/csv",
            as_attachment=True,
        )

    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({"error": "An unexpected error occurred."}), 500


# Delete API for the Testing
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
