# 🎬 Online Platform Shorts Generator

A FastAPI-based backend service for generating short-form content from videos. This project is structured with a clear modular architecture and uses `click` and `uvicorn` for command-line execution and ASGI server deployment.

## 🗂 Project Structure

```bash
shorts-generator/
├── src/
│   ├── shorts_generator/
│   │   ├── __init__.py
│   │   ├── __pycache__/
│   │   ├── audio_trancriber.py
│   │   ├── prompt.py
│   │   ├── shorts_agent.py
│   │   ├── utils.py
│   │   ├── video_processor.py
│   │   └── __init__.py
│   │
│   ├── api.py
│   ├── config.py
│   ├── credentials.json   # <— Gmail credentials
│   ├── mail_sender.py
│   ├── model.py
│   ├── task.py
│   └── token.json         # <— Gmail token
│
├── .env
├── .gitignore
├── .python-version
├── pyproject.toml
├── README.md
├── test.py
└── uv.lock

```

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Saad-Ali-Khan/shorts-generator.git
cd shorts-generator
```

Prerequisites:
Install uv, uvicorn, celery, redis

### 2. Install Dependencies

```bash
uv sync
```

### 3. 🛠 Running the API

The main FastAPI app is located in src/shorts_generator/api.py

#### Using uvicorn:

```bash
cd src
uvicorn api:app --reload

For Server:
uv run uvicorn api:app --host 0.0.0.0 --port 8000 --reload --timeout-keep-alive 600
```

#### For Celery

```bash
cd src
uv run celery -A task worker --loglevel=info
```

### 4. API Documentation

API docs available at

http://127.0.0.1:8000/docs/

### 5. Url for testing

https://res.cloudinary.com/dbgre09ks/video/upload/v1753789189/How_I_became_a_Software_Engineer_at_TikTok_qftder.webm
