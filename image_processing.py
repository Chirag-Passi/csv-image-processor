import asyncio
from file_storage import process_and_upload_image
from model import update_image_urls_in_db


# Asynchronous image processing task
async def process_images_task(request_id, rows):
    """Asynchronous task to process images from the CSV rows."""

    image_urls = []
    for row in rows:
        urls = row["input_images"]
        # If urls are in a list, join them into a single string
        if isinstance(urls, list):
            urls = ",".join(urls)  # Join URLs with a comma if it's a list
        image_urls.append(urls)  # Append the string of URLs to the list

    # Create a list of asyncio tasks for image processing
    tasks = [
        process_and_upload_image(request_id, idx, url)
        for idx, url in enumerate(image_urls)
    ]

    # Execute all tasks asynchronously and get output S3 URLs
    s3_urls = await asyncio.gather(*tasks)

    # Update MongoDB with the processed image URLs
    await update_image_urls_in_db(request_id, s3_urls)
