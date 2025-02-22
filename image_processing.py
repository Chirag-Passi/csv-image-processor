import asyncio
from file_storage import process_and_upload_image
from model import update_image_urls_in_db


async def process_images_task(request_id, rows):
    """Asynchronous task to process images from the CSV rows."""
    image_urls = [row["input_images"] for row in rows]

    # Create a list of asyncio tasks for image processing
    tasks = [
        process_and_upload_image(request_id, idx, url)
        for idx, url in enumerate(image_urls)
    ]

    # Execute all tasks asynchronously
    s3_urls = await asyncio.gather(*tasks)

    # Update MongoDB with the processed image URLs
    await update_image_urls_in_db(request_id, s3_urls)
