import asyncio
from file_storage import process_and_upload_image
from model import update_image_urls_in_db, update_processing_status_in_db


# Asynchronous image processing task
#


# Asynchronous image processing task
# async def process_images_task(request_id, rows):
#     """Asynchronous task to process images from the CSV rows."""
#     tasks = []  # This will store the individual image processing tasks

#     for row in rows:
#         urls = row["input_image_url"]  # This is now a list of URLs

#         # Iterate through each URL in the list and create processing tasks
#         for idx, url in enumerate(urls):
#             # Create a task for each image processing
#             tasks.append(process_and_upload_image(request_id, idx, url))

#     # Execute all tasks asynchronously and get the output S3 URLs
#     s3_urls = await asyncio.gather(*tasks)

#     # Update MongoDB with the processed image URLs
#     await update_image_urls_in_db(request_id, s3_urls)


# Asynchronous image processing task
async def process_images_task(request_id, rows):
    """Asynchronous task to process images from the CSV rows."""
    tasks = []  # Store tasks for image processing

    for row_idx, row in enumerate(rows):
        urls = row["Input Image Urls"]  # This is now a list of URLs
        # Process each URL individually and create processing tasks
        for idx, url in enumerate(urls):
            # Create a task for each image processing, pass row index and URL index
            tasks.append(process_and_upload_image(request_id, row_idx, idx, url))

    # Execute all tasks asynchronously
    await asyncio.gather(*tasks)

    # Once processing is complete, update the status in MongoDB
    await update_processing_status_in_db(request_id)
