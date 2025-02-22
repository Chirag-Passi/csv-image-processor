from PIL import Image
from aiobotocore.session import get_session
import requests
import boto3
import io
import uuid

import aiohttp
import aiobotocore

import os
from dotenv import load_dotenv


load_dotenv()

S3_BUCKET = os.getenv("ENV_S3_BUCKET")
AWS_ACCESS_KEY_ID = os.getenv("ENV_AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("ENV_AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("ENV_AWS_REGION")


# Download the image asynchronously
async def download_image(image_url):
    """Asynchronously download an image from a URL."""
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as response:
            if response.status != 200:
                raise Exception(f"Failed to download image from {image_url}")
            return io.BytesIO(await response.read())  # Return image content as bytes


import asyncio


# Compress the image asynchronously
async def compress_image(image, compression_ratio=0.5):
    """Compress the image by resizing it to a given ratio with a 5-second delay."""

    # Log and simulate a 5-second delay
    for i in range(1, 30):  # Loop from 1 to 5 for each second
        print(f"Compressing image... {i} second(s)")
        await asyncio.sleep(1)  # Sleep for 1 second asynchronously

    # Proceed with image compression after the delay
    img = Image.open(image)
    original_size = img.size  # Get original size (width, height)
    new_size = (
        int(original_size[0] * compression_ratio),
        int(original_size[1] * compression_ratio),
    )

    img = img.resize(new_size, Image.Resampling.LANCZOS)

    compressed_image = io.BytesIO()
    img.save(compressed_image, format="JPEG")
    compressed_image.seek(0)

    return compressed_image


# Upload the image to S3 asynchronously
async def upload_to_s3(image, filename):
    """Asynchronously upload the image to S3 and return the S3 URL."""
    session = get_session()
    unique_filename = f"{uuid.uuid4()}_{filename}"

    # Define the folder path inside the bucket
    folder_path = "demo/images/"

    # The full path for the file inside the S3 bucket
    full_key = f"{folder_path}{unique_filename}"

    async with session.create_client(
        "s3",
        region_name=AWS_REGION,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
    ) as s3_client:
        await s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=full_key,  # Use the full path
            Body=image,
            ContentType="image/jpeg",
        )

    return f"https://{S3_BUCKET}.s3.amazonaws.com/{full_key}"


# Asynchronous function to download, compress, and upload images
async def process_and_upload_image(request_id, idx, image_url):
    """Download, compress, and upload an image asynchronously."""
    try:
        # Step 1: Download the image asynchronously
        image = await download_image(image_url)

        # Step 2: Compress the image
        compressed_image = await compress_image(image)

        # Step 3: Upload the compressed image to S3
        filename = f"{request_id}_{idx}.jpg"
        s3_url = await upload_to_s3(compressed_image, filename)

        return s3_url
    except Exception as e:
        print(f"Error processing image {image_url}: {e}")
        return None
