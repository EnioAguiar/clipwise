# ClipWise

**Automatic viral clip detector for long-form video content.**

ClipWise automatically finds the best moments in streams, podcasts, and long videos using AI. It transcribes the video, extracts audio energy peaks, and uses AI (Gemini 2.5 Flash) to rank moments by engagement potential.

Built inspired by [podcli](https://github.com/podstack/podcli) but with a different approach — focused on web dashboard, API-first, and optimized for content creators who want to quickly generate TikTok/Shorts clips from their recordings.

## Features

- **Multi-source input**: Upload video files (MP4, MKV, WAV) or paste YouTube URL
- **Automatic transcription**: Local Whisper model (GPU-accelerated) — no cloud API costs
- **Audio energy extraction**: FFmpeg-based RMS analysis with Z-score normalization
- **AI moment ranking**: Google Gemini 2.5 Flash analyzes transcript + energy to find viral candidates
- **Interactive dashboard**: Preview moments, select clips, configure duration
- **Opus Clip integration**: Send selected moments directly to Opus Clip API for AI clip generation

## Tech Stack

### Frontend
- **Next.js 14** (App Router)
- **Tailwind CSS** + shadcn/ui
- **React** with TypeScript

### Backend
- **FastAPI** (Python async)
- **Whisper** (OpenAI) with CUDA GPU support
- **FFmpeg** for audio analysis
- **Google Gemini 2.5 Flash** for moment ranking
- **yt-dlp** for YouTube download

### Infrastructure
- **SQLite** (optional, for future persistence)
- **Docker-ready** architecture

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                    │
│   Dashboard → Config Panel → Video Player → Moment Cards   │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/JSON
┌────────────────────────▼────────────────────────────────────┐
│                      Backend (FastAPI)                       │
│                                                              │
│  /upload ─────────→ save_file()                            │
│  /youtube ────────→ save_youtube() → yt-dlp                │
│  /extract ────────→ transcribe_file() + extract_energy()    │
│  /process ────────→ rank_moments() → Gemini API             │
│  /moments/{id} ──→ serve moments.json                      │
│  /opus/send ─────→ proxy to Opus Clip API                  │
└─────────────────────────────────────────────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          ▼                              ▼
   /tmp/clipwise/               Opus Clip API
   - transcript.json            (external)
   - energy.json
   - moments.json
```

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- CUDA-compatible GPU (optional, for faster transcription)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Run server (from backend directory)
uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

npm install
npm run dev
```

Open http://localhost:3000 in your browser.

## Configuration

### Environment Variables

```env
# Gemini API (for moment ranking)
GEMINI_API_KEY=your-gemini-api-key

# Opus Clip API (optional, for auto clip generation)
OPUS_API_KEY=your-opus-api-key

# Whisper (optional overrides)
# WHISPER_MODEL=base  # tiny, base, small, medium, large
# CUDA_DEVICE=0        # GPU device index
```

### Moment Ranking Config

| Parameter | Default | Description |
|-----------|---------|-------------|
| `min_clip_duration` | 30 | Minimum clip length (seconds) |
| `max_clip_duration` | 90 | Maximum clip length (seconds) |
| `target_clips` | 5 | Number of clips to generate |
| `format` | vertical | Output format (vertical/horizontal) |

## API Reference

### POST /upload
Upload video file for processing.

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@video.mp4"
```

### POST /youtube
Download video from YouTube URL.

```bash
curl -X POST http://localhost:8000/youtube \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=..."}'
```

### POST /extract
Transcribe and extract energy from video.

```bash
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"source": "upload", "file_id": "uuid"}'
```

### POST /process
Rank moments using Gemini AI.

```bash
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{
    "source": "upload",
    "file_id": "uuid",
    "config": {
      "min_clip_duration": 30,
      "max_clip_duration": 90,
      "target_clips": 5
    }
  }'
```

### GET /moments/{video_id}
Get ranked moments for a video.

```bash
curl http://localhost:8000/moments/uuid
```

### POST /opus/send
Send moments to Opus Clip API.

```bash
curl -X POST http://localhost:8000/opus/send \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": "uuid",
    "moments": [{"start": 123.4, "end": 168.4}]
  }'
```

## Project Structure

```
clipwise/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── requirements.txt    # Python dependencies
│   ├── .env                 # Environment variables (gitignored)
│   └── services/
│       ├── transcription.py  # Whisper integration
│       ├── energy.py         # FFmpeg audio analysis
│       ├── gemini_client.py  # Gemini API client
│       ├── moment_ranker.py   # Moment filtering & ranking
│       ├── storage.py         # File management
│       └── opus_client.py     # Opus Clip API proxy
├── frontend/
│   ├── src/app/
│   │   ├── page.tsx         # Main dashboard
│   │   └── ...
│   ├── package.json
│   └── ...
├── .planning/               # GSD planning artifacts
├── .gitignore
├── README.md
└── LICENSE
```

## How It Works

### 1. Upload & Download
User uploads video file or provides YouTube URL. File is saved to `/tmp/clipwise/{uuid}/`.

### 2. Transcription
Whisper transcribes the audio with word-level timestamps. Output: `transcript.json`

### 3. Energy Extraction
FFmpeg extracts RMS energy per second. Peaks indicate moments of high audio intensity. Output: `energy.json`

### 4. Moment Ranking
Gemini receives:
- Full transcript with timestamps
- Top 20 energy peaks
- Config (min/max duration, target clips)

Gemini returns ranked moments with scores (hook, standalone, relevance, quotability).

### 5. Filtering
Backend validates spans:
- `span = end - start`
- Must be within `min_clip_duration` to `max_clip_duration`
- Moments outside range are rejected
- Multiple candidates generated → filter keeps best ones

### 6. Dashboard & Export
User sees ranked moments with timestamps, scores, and preview text. Can select moments and send to Opus Clip API for auto clip generation.

## Development

### Running Tests
```bash
# Backend
cd backend && python -m pytest

# Frontend
cd frontend && npm test
```

### Code Quality
```bash
# Format Python
cd backend && black .

# Format TypeScript
cd frontend && npm run format
```

## License

MIT

## Acknowledgments

- Inspired by [podcli](https://github.com/podstack/podcli) — the gold standard for podcast clip tools
- Transcription powered by [Whisper](https://github.com/openai/whisper) from OpenAI
- AI ranking powered by [Google Gemini](https://ai.google.dev/)