#  🎬 Online Platform Shorts Generator

A FastAPI-based backend service for generating short-form content from videos. This project is structured with a clear modular architecture and uses `click` and `uvicorn` for command-line execution and ASGI server deployment.

## 🗂 Project Structure

```bash
shorts-generator/
├── src/
│ └── shorts_generator/
│ ├── audio_transcriber.py
│ ├── config.py
│ ├── model.py
│ ├── prompt.py
│ ├── shorts_agent.py
│ ├── utils.py
│ ├── video_processor.py
│ └── api.py
├── .env
├── pyproject.toml
├── README.md
└── uv.lock
```


## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Saad-Ali-Khan/shorts-generator.git
cd shorts-generator
```

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
```
### 4. API Documentation

API docs available at 

http://127.0.0.1:8000/docs/
