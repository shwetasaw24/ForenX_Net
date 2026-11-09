
import base64
import io
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from services.forenxnet_pipeline import ForenXNetPipeline


# ---------------------------------------------------------
# Paths and configuration
# ---------------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = ROOT_DIR / "data" / "uploads"
REPORT_DIR = ROOT_DIR / "reports" / "analyses"

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="ForenXNet API",
    description="Image forensics analysis backend",
    version="1.0.0",
)

# React + Vite development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Load the existing models once when the API starts.
# If model initialization fails, the error appears in the server log.
pipeline = ForenXNetPipeline()


# ---------------------------------------------------------
# Result serialization
# ---------------------------------------------------------

def image_to_data_url(value: Any) -> str | None:
    """Convert an image-like result to a browser-displayable PNG URL."""
    try:
        if hasattr(value, "detach"):
            value = value.detach().cpu().numpy()

        if isinstance(value, Image.Image):
            image = value.convert("RGB")
        else:
            array = np.asarray(value)

            if array.size == 0:
                return None

            if array.ndim == 3 and array.shape[0] in (1, 3, 4) \
                    and array.shape[-1] not in (1, 3, 4):
                array = np.moveaxis(array, 0, -1)

            if np.issubdtype(array.dtype, np.floating):
                array = np.nan_to_num(array)
                if array.min() >= 0 and array.max() <= 1:
                    array = array * 255
                else:
                    array_min = array.min()
                    array_max = array.max()
                    if array_max > array_min:
                        array = (
                            (array - array_min)
                            / (array_max - array_min)
                            * 255
                        )
                    else:
                        array = np.zeros_like(array)

            array = np.clip(array, 0, 255).astype(np.uint8)

            if array.ndim == 2:
                image = Image.fromarray(array, mode="L").convert("RGB")
            elif array.ndim == 3 and array.shape[-1] in (3, 4):
                image = Image.fromarray(array).convert("RGB")
            else:
                return None

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        return f"data:image/png;base64,{encoded}"

    except Exception:
        return None


IMAGE_KEYS = {"original", "heatmap", "binary_mask", "overlay"}


def make_json_safe(value: Any, key: str = "") -> Any:
    """Convert model output into JSON-safe values."""

    if key in {"mask", "probability_mask"}:
        # These raw arrays can be very large. The pipeline's visualization
        # outputs are returned separately for browser display.
        return None

    if key in IMAGE_KEYS and value is not None:
        return image_to_data_url(value)

    if hasattr(value, "detach"):
        value = value.detach().cpu().numpy()

    if isinstance(value, np.ndarray):
        if value.size == 1:
            return value.item()
        return value.tolist()

    if isinstance(value, np.generic):
        return value.item()

    if isinstance(value, Path):
        return str(value)

    if isinstance(value, dict):
        return {
            str(k): make_json_safe(v, str(k))
            for k, v in value.items()
            if not (str(k) in IMAGE_KEYS and v is None)
        }

    if isinstance(value, (list, tuple)):
        return [make_json_safe(item) for item in value]

    if isinstance(value, (str, int, float, bool)) or value is None:
        if isinstance(value, float) and not np.isfinite(value):
            return None
        return value

    if isinstance(value, datetime):
        return value.isoformat()

    return str(value)


# ---------------------------------------------------------
# API routes
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "name": "ForenXNet API",
        "docs": "/docs",
        "health": "/api/health",
    }


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "ForenXNet",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/api/analyze")
def analyze_image(file: UploadFile = File(...)):
    """Run the existing ForenXNet analysis pipeline on an uploaded image."""

    filename = Path(file.filename or "upload").name
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail="Unsupported image format. Upload JPG, PNG, WEBP, TIFF, or BMP.",
        )

    analysis_id = uuid.uuid4().hex
    image_path = UPLOAD_DIR / f"{analysis_id}{extension}"
    report_path = REPORT_DIR / f"{analysis_id}.json"

    try:
        total_bytes = 0

        with image_path.open("wb") as destination:
            while True:
                chunk = file.file.read(1024 * 1024)
                if not chunk:
                    break

                total_bytes += len(chunk)
                if total_bytes > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail="Image exceeds the 25 MB upload limit.",
                    )

                destination.write(chunk)

        if total_bytes == 0:
            raise HTTPException(status_code=400, detail="The uploaded file is empty.")

        # Verify that the upload is a readable image.
        try:
            with Image.open(image_path) as uploaded_image:
                uploaded_image.verify()
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is not a valid supported image.",
            ) from exc

        # Call your existing Python models; no model inference is reimplemented.
        raw_result = pipeline.analyze(str(image_path))

        if not isinstance(raw_result, dict):
            raise RuntimeError(
                "Pipeline analyze() must return a dictionary. "
                "Check services/forenxnet_pipeline.py."
            )

        result = make_json_safe(raw_result)

        record = {
            "analysis_id": analysis_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "filename": filename,
            "image_path": str(image_path.relative_to(ROOT_DIR)),
            "result": result,
        }

        report_path.write_text(
            json.dumps(record, indent=2, ensure_ascii=False, allow_nan=False),
            encoding="utf-8",
        )

        return record

    except HTTPException:
        if image_path.exists():
            image_path.unlink(missing_ok=True)
        raise

    except Exception as exc:
        # Keep the full traceback in the server terminal, not in the API response.
        import logging
        logging.exception("ForenXNet analysis failed")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {type(exc).__name__}. Check the backend terminal.",
        ) from exc

    finally:
        file.file.close()


@app.get("/api/history")
def get_history():
    """Return real analyses persisted on disk, newest first."""
    records = []

    for report_path in REPORT_DIR.glob("*.json"):
        try:
            record = json.loads(report_path.read_text(encoding="utf-8"))
            records.append(record)
        except (OSError, json.JSONDecodeError):
            continue

    records.sort(key=lambda item: item.get("created_at", ""), reverse=True)

    return {"count": len(records), "analyses": records}


@app.get("/api/analyses/{analysis_id}")
def get_analysis(analysis_id: str):
    """Return a saved analysis by its generated ID."""
    if not analysis_id.isalnum():
        raise HTTPException(status_code=400, detail="Invalid analysis ID.")

    report_path = REPORT_DIR / f"{analysis_id}.json"

    if not report_path.is_file():
        raise HTTPException(status_code=404, detail="Analysis not found.")

    try:
        return json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=500,
            detail="Could not read the saved analysis.",
        ) from exc
