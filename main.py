"""
AI Skin Health Analyzer — FastAPI Backend
Powered by Groq (llama-4-scout vision) — FREE, no quota issues, keys start with gsk_

Why Groq:
  - Completely free tier with generous limits
  - Vision model: meta-llama/llama-4-scout-17b-16e-instruct
  - API key from console.groq.com (starts with gsk_...)
  - No credit card needed
"""

import io
import os
import json
import uuid
import base64
import logging
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
from groq import Groq

# ─── Config ───────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO, format="%(levelname)s │ %(message)s")
log = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "YOUR_GROQ_API_KEY_HERE")
UPLOAD_DIR   = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_MB  = 10
MODEL        = "meta-llama/llama-4-scout-17b-16e-instruct"  # free vision model on Groq

# ─── Groq client ──────────────────────────────────────────────────────────────

client = Groq(api_key=GROQ_API_KEY)

# ─── Prompt ───────────────────────────────────────────────────────────────────

SKIN_PROMPT = """You are an expert AI dermatologist. Carefully analyze the skin visible in this selfie photograph.

Return ONLY a valid JSON object. No markdown, no backticks, no explanation — raw JSON only.

{
  "skinScore": <integer 0-100, overall skin health>,
  "skinType": "<Oily | Dry | Combination | Normal | Sensitive>",
  "skinAge": <integer, estimated biological skin age>,
  "hydrationPercent": <integer 0-100>,
  "oilinessLevel": "<Low | Med | High>",
  "grade": "<Excellent | Good Condition | Needs Attention | Poor>",
  "concerns": {
    "acne": <integer 0-100>,
    "darkSpots": <integer 0-100>,
    "redness": <integer 0-100>,
    "tanning": <integer 0-100>,
    "oiliness": <integer 0-100>
  },
  "recommendations": [
    { "priority": "High", "text": "Specific actionable advice." },
    { "priority": "High", "text": "Specific actionable advice." },
    { "priority": "Med",  "text": "Specific actionable advice." },
    { "priority": "Low",  "text": "Specific actionable advice." }
  ],
  "morningRoutine": [
    { "name": "Step name", "desc": "Why it suits this person's skin" },
    { "name": "Step name", "desc": "Why it suits this person's skin" },
    { "name": "Step name", "desc": "Why it suits this person's skin" },
    { "name": "Step name", "desc": "Why it suits this person's skin" }
  ],
  "nightRoutine": [
    { "name": "Step name", "desc": "Why it suits this person's skin" },
    { "name": "Step name", "desc": "Why it suits this person's skin" },
    { "name": "Step name", "desc": "Why it suits this person's skin" },
    { "name": "Step name", "desc": "Why it suits this person's skin" }
  ],
  "note": "One concise summary sentence about this person's skin."
}"""

# ─── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="DermAI Skin Analyzer",
    description="AI skin analysis via Groq Vision (free tier)",
    version="4.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ─── Helpers ──────────────────────────────────────────────────────────────────

def validate_image(file: UploadFile) -> None:
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported type '{file.content_type}'. Use JPEG, PNG or WEBP.",
        )


def resize_if_needed(img: Image.Image, max_px: int = 1024) -> Image.Image:
    """Groq works best with images under 1024px — keeps tokens low & response fast."""
    w, h = img.size
    if max(w, h) > max_px:
        ratio = max_px / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
        log.info(f"Resized to {img.size}")
    return img


def to_jpeg_b64(img: Image.Image) -> str:
    """Convert PIL image → base64 JPEG string for Groq API."""
    buf = io.BytesIO()
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def parse_json(raw: str) -> dict:
    """Strip markdown fences if present, then parse JSON."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = "\n".join(
            l for l in cleaned.splitlines()
            if not l.strip().startswith("```")
        )
    return json.loads(cleaned.strip())


def save_upload(img: Image.Image, name: str) -> None:
    ext  = Path(name).suffix or ".jpg"
    path = UPLOAD_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}{ext}"
    buf  = io.BytesIO()
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")
    img.save(buf, format="JPEG", quality=85)
    path.write_bytes(buf.getvalue())
    log.info(f"Saved → {path}")


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"service": "DermAI", "status": "running", "model": MODEL, "provider": "Groq"}


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    """
    POST a selfie → returns full skin analysis JSON.
    Uses Groq's free vision model (llama-4-scout).
    """
    validate_image(file)

    # Read & validate size
    raw_bytes = await file.read()
    size_mb   = len(raw_bytes) / (1024 * 1024)
    if size_mb > MAX_FILE_MB:
        raise HTTPException(status_code=413, detail=f"File too large ({size_mb:.1f} MB).")

    log.info(f"Received '{file.filename}' — {size_mb:.2f} MB")

    # Process image
    img    = Image.open(io.BytesIO(raw_bytes))
    img    = resize_if_needed(img)
    b64img = to_jpeg_b64(img)
    save_upload(img, file.filename or "upload.jpg")

    # ── Groq Vision call ──────────────────────────────────────────────────────
    raw_text = ""
    try:
        response = client.chat.completions.create(
            model    = MODEL,
            messages = [
                {
                    "role": "user",
                    "content": [
                        # Image block — base64 JPEG
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64img}",
                            },
                        },
                        # Text prompt
                        {
                            "type": "text",
                            "text": SKIN_PROMPT,
                        },
                    ],
                }
            ],
            temperature = 0.2,
            max_tokens  = 1500,
        )

        raw_text = response.choices[0].message.content
        log.info(f"Groq response (first 150 chars): {raw_text[:150]}")

        result = parse_json(raw_text)

    except json.JSONDecodeError as e:
        log.error(f"JSON parse error: {e}\nRaw:\n{raw_text}")
        raise HTTPException(status_code=502, detail=f"Model returned invalid JSON: {e}")
    except Exception as e:
        log.error(f"Groq API error: {e}")
        raise HTTPException(status_code=502, detail=f"AI analysis failed: {str(e)}")

    # Attach metadata
    result["_meta"] = {
        "model":         MODEL,
        "provider":      "Groq",
        "analyzed_at":   datetime.utcnow().isoformat(),
        "image_size_mb": round(size_mb, 2),
    }

    log.info(f"Done — score={result.get('skinScore')}")
    return JSONResponse(content=result)
