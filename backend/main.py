from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import os
import httpx
import json
from dotenv import load_dotenv

from services.storage import save_upload, save_youtube, get_video_info, VIDEO_DIR
from services.energy import get_energy_profile, save_energy_data
from services.moment_ranker import rank_moments, save_moments

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="ClipWise API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure video directory exists
os.makedirs(VIDEO_DIR, exist_ok=True)


class YouTubeRequest(BaseModel):
    url: str

class EnergyRequest(BaseModel):
    file_id: str
    segments: list[dict] = []  # optional pre-segmented data

class ProcessingConfig(BaseModel):
    min_clip_duration: int = Field(default=30, alias="minDuration")
    max_clip_duration: int = Field(default=60, alias="maxDuration")
    target_clips: int = Field(default=10, alias="targetClips")
    format: str = "vertical"
    mode: str = "auto"
    extract_energy: bool = Field(default=True, alias="extractEnergy")

class Moment(BaseModel):
    rank: int
    start_time: str
    end_time: str
    duration_seconds: int
    score: int
    reason: str
    transcript_snippet: str
    highlight_type: str
    selected: bool = False

class AnalysisResult(BaseModel):
    live_id: str
    filename: str
    duration_minutes: int
    status: str
    moments: list[Moment]

@app.get("/")
def read_root():
    return {"message": "ClipWise API", "version": "0.1.0"}

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """Accept video file upload and save to /tmp/clipwise/<uuid>/."""
    import logging
    logger = logging.getLogger("uvicorn")
    try:
        result = save_upload(file)
        logger.warning(f"[UPLOAD] Returning: {result}")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/youtube")
async def download_youtube(req: YouTubeRequest):
    """Download YouTube video/audio via yt-dlp."""
    try:
        result = save_youtube(req.url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"YouTube download failed: {str(e)}")


@app.get("/video/{file_id}/info")
async def get_video_info_endpoint(file_id: str):
    """Get metadata for a processed video."""
    info = get_video_info(file_id)
    if not info:
        raise HTTPException(status_code=404, detail="Video not found")
    return info


@app.get("/video/{file_id}")
async def get_video(file_id: str):
    """Stream video file for playback."""
    info = get_video_info(file_id)
    if not info:
        raise HTTPException(status_code=404, detail="Video not found")
    video_path = info["path"]
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video file not found")
    from fastapi.responses import FileResponse
    return FileResponse(video_path, media_type="video/mp4")

@app.post("/analyze")
async def analyze_video(config: ProcessingConfig):
    return {"status": "not_implemented", "message": "Whisper + LLM integration pending"}

@app.post("/energy")
async def extract_energy(req: EnergyRequest):
    """Extract audio energy from a video file."""
    # Get file path from storage metadata
    info = get_video_info(req.file_id)
    if not info:
        raise HTTPException(status_code=404, detail="Video not found")

    video_path = info["path"]
    energy_profile = get_energy_profile(video_path, req.segments)

    # Save to /tmp/clipwise/<file_id>/energy.json
    energy_path = save_energy_data(
        req.file_id,
        energy_profile["energy_data"],
        energy_profile["segment_scores"],
        energy_profile["peak_times"],
    )

    return {
        "file_id": req.file_id,
        "energy_path": energy_path,
        "peak_times": energy_profile["peak_times"],
        "mean_rms": energy_profile["mean_rms"],
        "segment_scores": energy_profile["segment_scores"],
    }


class RankRequest(BaseModel):
    video_id: str
    min_clip_duration: int = 30
    max_clip_duration: int = 60
    target_clips: int = 10
    format: str = "vertical"
    use_llm: bool = True


class RankResponse(BaseModel):
    video_id: str
    moments_path: str
    moment_count: int
    moments: list[dict]


@app.post("/rank")
async def rank_video_moments(req: RankRequest):
    """
    Rank video moments using Grok AI (or energy-only fallback).

    Combines transcript + energy data to select the best timestamps
    for short-form clips. Returns ranked moments with scoring.
    """
    config = {
        "min_clip_duration": req.min_clip_duration,
        "max_clip_duration": req.max_clip_duration,
        "target_clips": req.target_clips,
        "format": req.format,
    }

    try:
        result = rank_moments(req.video_id, config, use_llm=req.use_llm)
        moments_path = save_moments(req.video_id, result)

        return RankResponse(
            video_id=req.video_id,
            moments_path=moments_path,
            moment_count=len(result.get("moments", [])),
            moments=result.get("moments", []),
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Moment ranking failed: {str(e)}")


@app.get("/result/{live_id}")
async def get_result(live_id: str):
    return {"live_id": live_id, "status": "not_found"}


class TranscribeRequest(BaseModel):
    video_id: str


@app.post("/transcribe")
async def transcribe_video(req: TranscribeRequest):
    """Trigger transcription on an existing video file."""
    from services.transcription import transcribe_file

    info = get_video_info(req.video_id)
    if not info:
        raise HTTPException(status_code=404, detail="Video not found")

    video_path = info["path"]
    result = transcribe_file(video_path)
    return result


class ProcessRequest(BaseModel):
    source: str  # "upload" or "youtube"
    file_id: str = ""  # for upload
    youtube_url: str = ""  # for youtube
    config: ProcessingConfig = ProcessingConfig()


@app.post("/extract")
async def extract_video(req: ProcessRequest):
    """
    Chains: upload/youtube -> transcribe -> energy
    Does NOT rank moments - that comes after config.
    """
    import logging
    import traceback
    logger = logging.getLogger("uvicorn")
    logger.warning(f"[EXTRACT] Received request: source={req.source}, file_id={req.file_id}")

    try:
        if req.source == "youtube":
            if req.file_id:
                video_id = req.file_id  # Already downloaded by /youtube
            else:
                result = save_youtube(req.youtube_url)
                video_id = result["file_id"]
        else:
            video_id = req.file_id

        info = get_video_info(video_id)
        if not info:
            raise HTTPException(status_code=404, detail="Video not found")
        video_path = info["path"]
        logger.warning(f"[EXTRACT] video_path={video_path}")

        # Step 1: Transcribe
        from services.transcription import transcribe_file
        transcript_path = f"/tmp/clipwise/{video_id}/transcript.json"
        if not os.path.exists(transcript_path):
            logger.warning(f"[EXTRACT] Starting transcription...")
            transcribe_file(video_path)
            logger.warning(f"[EXTRACT] Transcription complete")

        # Step 2: Extract energy (optional)
        energy_path = f"/tmp/clipwise/{video_id}/energy.json"
        if req.config.extract_energy and not os.path.exists(energy_path):
            logger.warning(f"[EXTRACT] Starting energy extraction...")
            energy_profile = get_energy_profile(video_path)
            save_energy_data(video_id, energy_profile["energy_data"], energy_profile["segment_scores"], energy_profile["peak_times"])
            logger.warning(f"[EXTRACT] Energy extraction complete")

        return {
            "video_id": video_id,
            "status": "extracted",
            "transcript_ready": os.path.exists(transcript_path),
            "energy_ready": os.path.exists(energy_path),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[EXTRACT] Error: {e}")
        logger.error(f"[EXTRACT] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@app.post("/process")
async def process_video(req: ProcessRequest):
    """
    Chains: upload/youtube -> transcribe -> energy -> rank
    Returns ranked moments ready for dashboard display.
    """
    import json
    import logging
    import traceback
    logger = logging.getLogger("uvicorn")
    logger.warning(f"[PROCESS] Received request: source={req.source}, file_id={req.file_id}, youtube_url={req.youtube_url}")

    try:
        # Step 1: Get video path (upload already done, or download youtube if needed)
        if req.source == "youtube":
            if req.file_id:
                video_id = req.file_id  # Already downloaded by /extract
            else:
                result = save_youtube(req.youtube_url)
                video_id = result["file_id"]
        else:
            video_id = req.file_id

        logger.warning(f"[PROCESS] Looking up video_id={video_id}")
        info = get_video_info(video_id)
        logger.warning(f"[PROCESS] get_video_info result: {info}")
        if not info:
            raise HTTPException(status_code=404, detail="Video not found")
        video_path = info["path"]
        logger.warning(f"[PROCESS] video_path={video_path}")

        # Step 2: Transcribe (if not already done)
        from services.transcription import transcribe_file
        transcript_path = f"/tmp/clipwise/{video_id}/transcript.json"
        logger.warning(f"[PROCESS] Checking transcript at {transcript_path}, exists={os.path.exists(transcript_path)}")
        if not os.path.exists(transcript_path):
            logger.warning(f"[PROCESS] Starting transcription...")
            transcribe_file(video_path)
            logger.warning(f"[PROCESS] Transcription complete")

        # Step 3: Extract energy (optional, only used for fallback if Gemini fails)
        energy_path = f"/tmp/clipwise/{video_id}/energy.json"
        logger.warning(f"[PROCESS] Checking energy at {energy_path}, exists={os.path.exists(energy_path)}")
        if req.config.extract_energy and not os.path.exists(energy_path):
            logger.warning(f"[PROCESS] Starting energy extraction...")
            energy_profile = get_energy_profile(video_path)
            save_energy_data(video_id, energy_profile["energy_data"], energy_profile["segment_scores"], energy_profile["peak_times"])
            logger.warning(f"[PROCESS] Energy extraction complete")

        # Step 4: Rank moments
        config = {
            "min_clip_duration": req.config.min_clip_duration,
            "max_clip_duration": req.config.max_clip_duration,
            "target_clips": req.config.target_clips,
            "format": req.config.format,
        }
        logger.warning(f"[PROCESS] Starting moment ranking with config={config}")
        result = rank_moments(video_id, config, use_llm=True)
        moments_path = save_moments(video_id, result)
        logger.warning(f"[PROCESS] Ranking complete, {len(result.get('moments', []))} moments")

        return {
            "video_id": video_id,
            "status": "complete",
            "moments_path": moments_path,
            "moment_count": len(result.get("moments", [])),
            "moments": result.get("moments", [])
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[PROCESS] Error: {e}")
        logger.error(f"[PROCESS] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.get("/moments/{video_id}")
async def get_moments(video_id: str):
    """Get ranked moments for a video."""
    info = get_video_info(video_id)
    if not info:
        raise HTTPException(status_code=404, detail="Video not found")

    moments_path = f"/tmp/clipwise/{video_id}/moments.json"
    if not os.path.exists(moments_path):
        raise HTTPException(status_code=404, detail="Moments not found")

    with open(moments_path) as f:
        moments_data = json.load(f)

    return moments_data


class OpusSendRequest(BaseModel):
    video_id: str
    moments: list[dict]  # [{start: float, end: float}, ...]


@app.post("/opus/send")
async def send_to_opus(req: OpusSendRequest):
    """
    Send selected moments to Opus Clip API.
    Returns job ID for polling status.
    """
    opus_api_key = os.getenv("OPUS_API_KEY")
    if not opus_api_key:
        raise HTTPException(status_code=500, detail="OPUS_API_KEY not configured in .env")

    # Get video info to get the file path
    info = get_video_info(req.video_id)
    if not info:
        raise HTTPException(status_code=404, detail="Video not found")

    video_path = info["path"]

    # Format timestamps for Opus API
    timestamps = [{"start": m["start"], "end": m["end"]} for m in req.moments]

    # Call Opus Clip API
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.opus.clip/v1/clips",
            headers={
                "Authorization": f"Bearer {opus_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "video_url": f"file://{video_path}",
                "timestamps": timestamps
            },
            timeout=30.0
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Opus API error: {response.text}"
        )

    result = response.json()
    return {
        "status": "submitted",
        "job_id": result.get("job_id"),
        "moments_count": len(req.moments)
    }


@app.get("/energy/{video_id}")
async def get_energy_endpoint(video_id: str):
    """
    Get energy data for a video (used for waveform visualization).
    """
    info = get_video_info(video_id)
    if not info:
        raise HTTPException(status_code=404, detail="Video not found")

    energy_path = f"/tmp/clipwise/{video_id}/energy.json"
    if not os.path.exists(energy_path):
        raise HTTPException(status_code=404, detail="Energy data not found")

    with open(energy_path) as f:
        energy_data = json.load(f)

    return {
        "video_id": video_id,
        "energy_data": energy_data.get("energy_data", []),
        "peak_times": energy_data.get("peak_times", []),
        "mean_rms": energy_data.get("mean_rms", 0)
    }