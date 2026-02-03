import logging

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from app.parser.pipeline import parse_linkedin_pdf
from app.parser.models import ParsedProfile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Suchi LinkedIn Parser",
    description="Stateless LinkedIn PDF parsing service",
    version="1.0.0",
)

MAX_PDF_SIZE = 10 * 1024 * 1024  # 10MB


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "linkedin-parser"}


@app.post("/parse/linkedin-pdf", response_model=ParsedProfile)
async def parse_pdf(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    contents = await file.read()
    if len(contents) > MAX_PDF_SIZE:
        raise HTTPException(status_code=400, detail="PDF exceeds 10MB size limit")

    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Empty PDF file")

    try:
        profile = parse_linkedin_pdf(contents)
        return profile
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("Failed to parse LinkedIn PDF")
        raise HTTPException(status_code=500, detail="Failed to parse PDF")
