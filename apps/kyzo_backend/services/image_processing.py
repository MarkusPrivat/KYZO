import io
import uuid
import base64

from pathlib import Path
from datetime import datetime
from typing import TypedDict

from fastapi import HTTPException, status, UploadFile
from pdf2image import convert_from_bytes
from pdf2image.exceptions import PDFPageCountError, PDFSyntaxError, PDFInfoNotInstalledError
from PIL import Image, ImageOps, UnidentifiedImageError

from apps.kyzo_backend.config import ImageProcessMessages


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

    async def process_upload(self, file: UploadFile) -> list[ProcessedImageMetadata]:
        """
        Orchestrates the processing of an uploaded file by converting it into
        optimized, AI-ready images.

        This method handles the conversion workflow for both PDF and standard images:
        1. Reads file content and identifies the format.
        2. PDFs: Renders every page into separate images via Poppler.
        3. Images: Normalizes orientation (EXIF) and optimizes for AI consumption.
        4. Storage: Persists all images as JPEGs and generates base64 strings.

        Args:
            file (UploadFile): The uploaded file from the FastAPI request.
                               Supports common image formats and PDFs.

        Returns:
            list[ProcessedImageMetadata]: A list of metadata for each processed page
                                          or image, ready for LLM/OCR processing.

        Raises:
            HTTPException (400): If the file is corrupt, encrypted (PDF), or
                                 an unsupported format.
            HTTPException (500): If Poppler (PDF service) is missing or an
                                 unexpected server-side error occurs.
        """
        await file.seek(0)
        content = await file.read()

        try:
            results = []

            if file.content_type == "application/pdf" or file.filename.lower().endswith(".pdf"):
                pages = convert_from_bytes(content, dpi=200)

                for i, page_img in enumerate(pages):
                    optimized_buffer = self._optimize_image(page_img)

                    file_id = (f"{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                               f"_p{i + 1}_{uuid.uuid4().hex[:4]}.jpg")
                    results.append(self._save_and_encode(optimized_buffer, file_id))

            else:
                with Image.open(io.BytesIO(content)) as img:
                    img = ImageOps.exif_transpose(img)
                    optimized_buffer = self._optimize_image(img)

                    file_id = (f"{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                               f"_{uuid.uuid4().hex[:8]}.jpg")

                    results.append(self._save_and_encode(optimized_buffer, file_id))

            return results

        except PDFInfoNotInstalledError as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ImageProcessMessages.POPPLER_NOT_FOUND
            ) from error

        except (PDFPageCountError, PDFSyntaxError, UnidentifiedImageError) as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ImageProcessMessages.CORRUPT_FILE
            ) from error

        except Exception as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"{ImageProcessMessages.UNEXPECTED_ERROR} {str(error)}"
            ) from error

    def _optimize_image(self, image: Image.Image) -> io.BytesIO:
        """
        Internal pillow logic: Handles color mode conversion, resizing, and JPEG compression.

        Args:
            image (Image.Image): The source Pillow Image object.

        Returns:
            io.BytesIO: A buffer containing the optimized JPEG data.
        """
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")

        image.thumbnail((self.MAX_RESOLUTION, self.MAX_RESOLUTION), Image.Resampling.LANCZOS)

        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=80, optimize=True)
        buffer.seek(0)

        return buffer

    def _save_and_encode(self, buffer: io.BytesIO, file_id: str) -> ProcessedImageMetadata:
        """
        Persists the optimized image to disk and generates a base64 representation.

        This helper handles the final stage of the image pipeline: writing the
        processed bytes to the local storage path and preparing the data structure
        required for both database storage and LLM transmission.

        Args:
            buffer (io.BytesIO): The in-memory buffer containing the JPEG data.
            file_id (str): The unique filename (UUID-based) for the file.

        Returns:
            ProcessedImageMetadata: A dictionary containing the file metadata,
                                     including the base64 string for Vision OCR.

        Note:
            Any I/O errors occurring during file writing will bubble up to the
            calling method and will be caught by the central error handling.
        """
        self.storage_path.mkdir(parents=True, exist_ok=True)

        file_path = self.storage_path / file_id
        with open(file_path, "wb") as f:
            f.write(buffer.getbuffer())

        base64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return {
            "file_id": file_id,
            "path": str(file_path),
            "base64": base64_str,
            "mime_type": "image/jpeg"
        }
