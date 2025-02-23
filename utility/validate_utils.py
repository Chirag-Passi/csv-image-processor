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
    # Decode file content from bytes to string
    file_content = io.StringIO(file.stream.read().decode("utf-8"))
    csv_data = csv.reader(file_content)

    # Read headers from the first row
    headers = next(csv_data)

    # Validate headers, expecting the exact column names
    if not validate_headers(headers):
        return (
            None,
            "Invalid CSV format. Expected headers: 'S. No.', 'Product Name', 'Input Image Urls'",
        )

    rows = []
    for row in csv_data:
        # Ensure each row has exactly 3 values (S. No., Product Name, Input Image Urls)
        if len(row) != 3:
            continue  # Skip malformed rows

        # Unpack row values
        serial_number, product_name, input_urls = row

        # Split 'Input Image Urls' by comma to create a list of URLs
        input_images = [url.strip() for url in input_urls.split(",")]

        # Append the row data to the list, using the correct keys
        rows.append(
            {
                "S. No.": serial_number,
                "Product Name": product_name,
                "Input Image Urls": input_images,  # Store the URLs as a list
            }
        )

    # If no valid rows were found, return an error message
    if not rows:
        return None, "No valid rows found in CSV"

    # Return the parsed rows and None (no error)
    return rows, None


# Function to generate a response when the CSV is processed
# def create_response(rows):
#     return {"request_id": rows[0]["request_id"]}
