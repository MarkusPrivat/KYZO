import io
import uuid
import base64

from pathlib import Path
from datetime import datetime
from typing import TypedDict

from fastapi import UploadFile
from PIL import Image, ImageOps


class ProcessedImageMetadata(TypedDict):
    """Definition of the metadata returned after image processing."""
    file_id: str
    path: str
    base64: str
    mime_type: str


class ImageProcessingService:
    """
    Service for handling image uploads, including optimization,
    local storage, and base64 encoding for LLM vision tasks.
    """
    def __init__(self, storage_path: str = "storage/scans"):
        """
        Initializes the service and ensures the storage directory exists.

        Args:
            storage_path (str): The local directory where images will be saved.
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.MAX_RESOLUTION = 2048

    async def process_upload(self, file: UploadFile) -> ProcessedImageMetadata:
        """
        Main processing pipeline: Optimizes, stores, and encodes an uploaded image.

        This method reads the raw file, corrects orientation based on EXIF data,
        resizes the image for cost-effective OCR, and saves it locally. It also
        returns a base64 string for direct LLM processing.

        Args:
            file (UploadFile): The raw image file from the multipart request.

        Returns:
            ProcessedImageMetadata: A dictionary containing the file ID,
                                     local path, base64 string, and mime type.

        Raises:
            PIL.UnidentifiedImageError: If the uploaded file is not a valid image.
        """
        # Ensure the file pointer is at the beginning
        await file.seek(0)
        content = await file.read()

        with Image.open(io.BytesIO(content)) as img:
            # Correct orientation based on EXIF data (critical for mobile uploads)
            img = ImageOps.exif_transpose(img)

            optimized_img_buffer = self._optimize_image(img)

            file_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.jpg"
            file_path = self.storage_path / file_id

            with open(file_path, "wb") as f:
                f.write(optimized_img_buffer.getbuffer())

            # Encode to base64 for LLM vision input
            base64_str = base64.b64encode(optimized_img_buffer.getvalue()).decode("utf-8")

            return {
                "file_id": file_id,
                "path": str(file_path),
                "base64": base64_str,
                "mime_type": "image/jpeg"
            }

    def _optimize_image(self, image: Image.Image) -> io.BytesIO:
        """
        Internal pillow logic: Handles color mode conversion, resizing, and JPEG compression.

        Args:
            image (Image.Image): The source Pillow Image object.

        Returns:
            io.BytesIO: A buffer containing the optimized JPEG data.
        """
        # Convert to RGB if necessary (handles PNG transparency or GIFs)
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")

        image.thumbnail((self.MAX_RESOLUTION, self.MAX_RESOLUTION), Image.Resampling.LANCZOS)

        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=80, optimize=True)
        buffer.seek(0)

        return buffer
