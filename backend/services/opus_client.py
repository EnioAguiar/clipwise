"""
Opus Clip API client with resumable upload support.
Based on: https://help.opus.pro/api-reference/endpoints/upload-video-create-project
"""

import httpx
import os
import uuid
from typing import Optional

BASE_URL = "https://api.opus.pro/api"


class OpusClient:
    """Opus Clip API client with resumable upload support."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        }
    
    async def get_upload_link(self) -> dict:
        """
        Step 1: Get resumable upload URL and uploadId.
        POST /api/upload-links
        """
        response = httpx.post(
            f"{BASE_URL}/upload-links",
            headers=self.headers,
            json={"video": {"usecase": "LocalUpload"}},
            timeout=30.0
        )
        response.raise_for_status()
        data = response.json()
        return {
            "upload_id": data["uploadId"],
            "url": data["url"]
        }
    
    async def initiate_resumable_upload(self, url: str) -> str:
        """
        Step 2: Start resumable upload session.
        POST <url_from_step1> with x-goog-resumable: start
        Returns the location header for uploading.
        """
        response = httpx.post(
            url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "X-Goog-Resumable": "start",
                "Content-Length": "0"
            },
            timeout=30.0
        )
        response.raise_for_status()
        # Location header contains the resumable upload URL
        return response.headers["Location"]
    
    async def upload_video_chunked(
        self, 
        location: str, 
        filepath: str, 
        progress_callback: Optional[callable] = None
    ) -> bool:
        """
        Step 3: PUT video in chunks to upload location.
        Uses Content-Range header for resumable upload.
        """
        file_size = os.path.getsize(filepath)
        chunk_size = 5 * 1024 * 1024  # 5MB chunks
        
        with open(filepath, "rb") as f:
            offset = 0
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                
                end = offset + len(chunk) - 1
                content_range = f"bytes {offset}-{end}/{file_size}"
                
                headers = {
                    "Content-Range": content_range,
                    "Content-Length": str(len(chunk))
                }
                
                response = httpx.put(
                    location, 
                    headers=headers, 
                    content=chunk,
                    timeout=120.0
                )
                
                if response.status_code not in (200, 201):
                    raise Exception(f"Upload failed: {response.status_code} - {response.text}")
                
                offset += len(chunk)
                if progress_callback:
                    progress_callback(offset / file_size * 100)
        
        return True
    
    async def create_clip_project(
        self,
        upload_id: str,
        timestamps: list[dict],
        title: str = "ClipWise Export",
        skip_curate: bool = False
    ) -> dict:
        """
        Step 4: Create clip project with uploadId + timestamps.
        POST /api/clip-projects
        
        timestamps format: [{"start": 123.4, "end": 168.4}, ...]
        Converts to clipDurations: [[123.4, 168.4], ...]
        """
        # Convert timestamps to clip durations [[start, end], ...]
        clip_durations = [[ts["start"], ts["end"]] for ts in timestamps]
        
        payload = {
            "videoUrl": upload_id,  # Use uploadId for uploaded videos
            "uploadedVideoAttr": {
                "title": title
            },
            "curationPref": {
                "clipDurations": clip_durations,
                "skipCurate": skip_curate
            }
        }
        
        response = httpx.post(
            f"{BASE_URL}/clip-projects",
            headers=self.headers,
            json=payload,
            timeout=60.0
        )
        response.raise_for_status()
        return response.json()
    
    async def create_clip_project_from_url(
        self,
        video_url: str,
        timestamps: list[dict],
        title: str = "ClipWise Export",
        skip_curate: bool = False
    ) -> dict:
        """
        Create clip project using a public URL (YouTube, etc).
        For YouTube videos - send directly without upload.
        
        timestamps format: [{"start": 123.4, "end": 168.4}, ...]
        """
        clip_durations = [[ts["start"], ts["end"]] for ts in timestamps]
        
        payload = {
            "videoUrl": video_url,
            "uploadedVideoAttr": {
                "title": title
            },
            "curationPref": {
                "clipDurations": clip_durations,
                "skipCurate": skip_curate
            }
        }
        
        response = httpx.post(
            f"{BASE_URL}/clip-projects",
            headers=self.headers,
            json=payload,
            timeout=60.0
        )
        response.raise_for_status()
        return response.json()
    
    async def get_project_status(self, project_id: str) -> dict:
        """
        Poll for clip generation status.
        GET /api/clip-projects/{project_id}
        """
        response = httpx.get(
            f"{BASE_URL}/clip-projects/{project_id}",
            headers=self.headers,
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()
    
    async def download_clip(self, clip_url: str, output_path: str) -> str:
        """Download a completed clip to local storage."""
        response = httpx.get(clip_url, follow_redirects=True, timeout=300.0)
        response.raise_for_status()
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(response.content)
        
        return output_path


async def upload_video_to_opus(
    video_filepath: str,
    progress_callback: Optional[callable] = None
) -> str:
    """
    Convenience function: upload a video file to Opus and return upload_id.
    
    Flow:
    1. Get upload link
    2. Initiate resumable upload
    3. Upload in chunks
    4. Return upload_id for use in create_clip_project
    """
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("OPUS_API_KEY")
    if not api_key:
        raise Exception("OPUS_API_KEY not configured in .env")
    
    client = OpusClient(api_key)
    
    # Step 1: Get upload link
    result = await client.get_upload_link()
    upload_id = result["upload_id"]
    upload_url = result["url"]
    
    # Step 2: Initiate resumable upload
    location = await client.initiate_resumable_upload(upload_url)
    
    # Step 3: Upload video in chunks
    await client.upload_video_chunked(location, video_filepath, progress_callback)
    
    return upload_id