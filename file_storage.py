from PIL import Image
from aiobotocore.session import get_session
import io
import uuid
import aiohttp
from model import update_output_url_in_db
import os
from dotenv import load_dotenv


load_dotenv()

S3_BUCKET = os.getenv("ENV_S3_BUCKET")
AWS_ACCESS_KEY_ID = os.getenv("ENV_AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("ENV_AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("ENV_AWS_REGION")


# Download the image asynchronously (Helper)
async def download_image(image_url):
    """Asynchronously download an image from a URL."""
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as response:
            if response.status != 200:
                raise Exception(f"Failed to download image from {image_url}")
            return io.BytesIO(await response.read())  # Return image content as bytes


# Compress the image asynchronously (Helper)
async def compress_image(image, compression_ratio=0.5):
    """Compress the image by resizing it to a given ratio with a 5-second delay."""

    img = Image.open(image)
    original_size = img.size 
    new_size = (
        int(original_size[0] * compression_ratio),
        int(original_size[1] * compression_ratio),
    )

    img = img.resize(new_size, Image.Resampling.LANCZOS)

    compressed_image = io.BytesIO()
    img.save(compressed_image, format="JPEG")
    compressed_image.seek(0)

    return compressed_image


# Upload the image to S3 asynchronously (Helper)
async def upload_to_s3(image, filename):
    """Asynchronously upload the image to S3 and return the S3 URL."""
    session = get_session()
    unique_filename = f"{uuid.uuid4()}_{filename}"

    folder_path = "demo/images/"

    full_key = f"{folder_path}{unique_filename}"

    async with session.create_client(
        "s3",
        region_name=AWS_REGION,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
    ) as s3_client:
        await s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=full_key, 
            Body=image,
            ContentType="image/jpeg",
        )

    return f"https://{S3_BUCKET}.s3.amazonaws.com/{full_key}"


async def process_and_upload_image(request_id, row_idx, url_idx, image_url):
    """Download, compress, and upload an image asynchronously."""
    try:
        image = await download_image(image_url)
        compressed_image = await compress_image(image)
        filename = f"{request_id}_{row_idx}_{url_idx}.jpg"
        s3_url = await upload_to_s3(compressed_image, filename)
        await update_output_url_in_db(request_id, row_idx, s3_url)

        return s3_url
    except Exception as e:
        print(f"Error processing image {image_url}: {e}")
        return None
