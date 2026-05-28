from fastapi import UploadFile, HTTPException, status

from apps.kyzo_backend.config import fastapi_settings


def validate_uploaded_file(files: list[UploadFile]) -> None:
    """
    Validates the MIME type and file size of an uploaded file.
    """
    for file in files:
        if file.content_type not in fastapi_settings.ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type '{file.content_type}' is not supported. "
                       f"Allowed formats: {', '.join(fastapi_settings.ALLOWED_MIME_TYPES)}"
            )

        file_size = file.size

        if file_size is None:
            file.file.seek(0, 2)
            file_size = file.file.tell()
            file.file.seek(0)

        if file_size > fastapi_settings.MAX_UPLOAD_SIZE:
            max_mb = fastapi_settings.MAX_UPLOAD_SIZE / (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File is too large ({file.size} bytes). Max limit is {max_mb} MB."
            )
