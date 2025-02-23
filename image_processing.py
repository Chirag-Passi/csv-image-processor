import asyncio
from file_storage import process_and_upload_image
from model import update_processing_status_in_db


# Asynchronous image processing task
async def process_images_task(request_id, rows):
    """Asynchronous task to process images from the CSV rows."""
    tasks = []

    for row_idx, row in enumerate(rows):
        urls = row["Input Image Urls"]

        for idx, url in enumerate(urls):
            tasks.append(process_and_upload_image(request_id, row_idx, idx, url))

    await asyncio.gather(*tasks)

    await update_processing_status_in_db(request_id)
