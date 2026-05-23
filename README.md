# ClipWise

Detector de momentos para lives — encontra os melhores trechos automaticamente.

## Stack

- **Frontend:** Next.js 14 (App Router) + Tailwind + shadcn/ui
- **Backend:** FastAPI (Python) + Faster Whisper + GPT-4o mini

## Setup

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows
pip install -r requirements.txt
cp .env.example .env  # editar com suas chaves
npm run dev
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/` | Health check |
| POST | `/upload` | Upload vídeo |
| POST | `/analyze` | Processar com Whisper + LLM |
| GET | `/result/{live_id}` | Buscar resultado |

## Fluxo

1. Upload vídeo (MP4, MKV, WAV, ou YouTube link)
2. Configure min/max duration e target clips
3. Iniciar análise (Whisper → transcrição)
4. LLM rankeia momentos por score
5. Dashboard com timestamps
6. Export manual ou gerar via Opus API