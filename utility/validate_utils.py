import io
import csv
import uuid


# Function to validate the CSV headers
def validate_headers(headers):
    required_headers = ["s. no.", "product name", "input image urls"]
    headers = [header.strip().lower() for header in headers]

    if headers != required_headers:
        return False
    return True


# Function to parse the CSV file and return rows as a list of dictionaries
def parse_csv(file):
    file_content = io.StringIO(
        file.stream.read().decode("utf-8")
    )  # Decode to string from bytes
    csv_data = csv.reader(file_content)

    headers = next(csv_data)

    if not validate_headers(headers):
        return (
            None,
            "Invalid CSV format. Expected headers: S. No., Product Name, Input Image Urls",
        )

    rows = []
    for row in csv_data:
        if len(row) != 3:
            continue  # Skip malformed rows

        serial_number, product_name, input_urls = row
        input_images = input_urls.split(",")  # Split input URLs by comma

        # create_request_record(request_id, product_name, input_images)
        rows.append(
            {
                "serial_number": serial_number,
                "product_name": product_name,
                "input_images": input_images,
            }
        )

    if not rows:
        return None, "No valid rows found in CSV"

    return rows, None


# Function to generate a response when the CSV is processed
# def create_response(rows):
#     return {"request_id": rows[0]["request_id"]}
