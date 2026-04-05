# Vectorless RAG Chatbot

This project is a sophisticated Vectorless RAG (Retrieval-Augmented Generation) chatbot. Unlike traditional vector environments which rely on rigid text chunking and similarity embeddings, this application utilizes logical document reasoning through hierarchy tree structures.

The vectorless reasoning and indexing backend is powered by the [PageIndex](https://github.com/VectifyAI/PageIndex) framework. The frontend delivers a minimalist web UI configured with Jinja2 and Tailwind CSS. The interface enables swift, interactive document uploading and contextual reasoning chats that maintain an strict one-to-one memory scope between a document and its chat instance.

## Technical Architecture

- Application Framework: FastAPI
- Database Layer: SQLAlchemy (SQLite by default, compatible with standard SQL dialects)
- Core RAG Engine: PageIndex
- Large Language Model: Google Gemini API
- Package Manager: uv
- View Layer: Jinja2 Templates
- Styling: Tailwind CSS (CDN)

For installation and execution instructions, please refer to `QUICKSTART.md`.
