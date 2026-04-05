# Quickstart Guide

This guide details the necessary steps to configure and successfully run the Vectorless RAG Chatbot application on your machine.

## Prerequisites

1. Python 3.12 or newer.
2. The `uv` Python package manager installed globally. 
3. Valid API keys for Google GenAI and PageIndex.

## Installation

1. Navigate to the root directory of the application.
2. Sync the dependencies and setup the virtual environment natively through `uv`:

```bash
uv sync
```

3. Create the required configuration file in the repository root. Create a file named `.env` based on the following pattern:

```ini
# .env
PAGEINDEX_API_KEY=your_pageindex_api_key_here
GOOGLE_API_KEY=your_google_ai_api_key_here
```

## Running Locally

To start the application, use `uv` to execute uvicorn directly:

```bash
uv run uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

Navigate to `http://127.0.0.1:8000` from your browser to begin indexing and interrogating uploaded documents. SQLite databases (`data/`) and user uploads (`data/uploads/`) will automatically be curated locally.

## Running via Docker

Alternatively, the application can be seamlessly built and served using the provided lightweight Alpine Dockerfile:

1. Build the container image:

```bash
docker build -t vectorless-rag .
```

2. Run the application (passing your environment configurations safely):

```bash
docker run -p 8000:8000 --env-file .env vectorless-rag
```
