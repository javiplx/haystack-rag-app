from pathlib import Path
import sys

from contextlib import asynccontextmanager
import logging
from typing import List

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse

from common.api_utils import create_api
from common.models import FilesUploadResponse, FilesListResponse
from common.document_store import initialize_document_store
from common.config import settings
from indexing.service import IndexingService


logging.basicConfig(
    format="%(levelname)s - %(name)s - [%(process)d] - %(message)s",
    level=settings.log_level
)

# Create a logger for this module
logger = logging.getLogger(__name__)

# Set Haystack logger to INFO level
logging.getLogger("haystack").setLevel(settings.haystack_log_level)

# Create a single instance of IndexingService
document_store = initialize_document_store()
indexing_service = IndexingService(document_store)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")

    # Index all files on startup
    if settings.index_on_startup and indexing_service.index_files():
        logger.info("Indexing completed successfully")

    yield
    # Shutdown
    logger.info("Shutting down")
    # Add any cleanup code here if needed

app = create_api(title="RAG Indexing Service", lifespan=lifespan)

def get_indexing_service():
    if indexing_service.pipeline is None:
        raise HTTPException(status_code=500, detail="IndexingService not initialized")
    return indexing_service

@app.post("/files", response_model=List[FilesUploadResponse])
async def upload_files(
    files: List[UploadFile] = File(...),
    service: IndexingService = Depends(get_indexing_service)
) -> JSONResponse:
    """
    Upload and index multiple files.

    This endpoint allows uploading multiple files simultaneously. Each file is saved and indexed synchronously.

    Parameters:
    - files (List[UploadFile]): A list of files to be uploaded and indexed.

    Returns:
    - JSONResponse: A list of FilesUploadResponse objects, one for each uploaded file.
      Each response includes the file_id (filename) and status ("success" or "failed").
      If a file upload fails, an error message is included.

    Raises:
    - HTTPException(400): If no files are provided.
    - HTTPException(500): If the IndexingService is not initialized.

    The response status code is 200 if all files are uploaded successfully, or 500 if any file upload fails.
    """
    if not files:
        logger.info("No files uploaded")
        raise HTTPException(status_code=400, detail="No files uploaded")

    logger.info(f"Uploading {len(files)} files...")

    responses = []
    all_successful = True
    
    for file in files:
        try:
            contents = await file.read()
            logger.info(f"Uploading file: {file.filename}")
            full_path = service.save_uploaded_file(file.filename, contents)

            logger.info(f"File uploaded and indexed successfully: {full_path}")
            responses.append(FilesUploadResponse(file_id=file.filename, status="success"))
        except Exception as e:
            all_successful = False
            logger.error(f"Error uploading file {file.filename}: {str(e)}")
            responses.append(
                FilesUploadResponse(file_id=file.filename, status="failed", error=str(e))
            )

    status_code = 200 if all_successful else 500
    return JSONResponse(content=[response.dict() for response in responses], status_code=status_code)

@app.get("/files", response_model=FilesListResponse)
async def get_files(
    service: IndexingService = Depends(get_indexing_service)
) -> FilesListResponse:
    """
    Retrieve a list of all indexed files.

    This endpoint rescans the files directory and returns an updated list of all indexed files.

    Returns:
    - FilesListResponse: An object containing a list of file information.
      Each file entry typically includes details such as filename, path, and any other relevant metadata.

    Raises:
    - HTTPException(500): If the IndexingService is not initialized.

    The files list is updated each time this endpoint is called, ensuring the returned information is current.
    """
    files = service.rescan_files_and_paths()

    logger.info(f"Found files {files}")
    return FilesListResponse(files=files)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
