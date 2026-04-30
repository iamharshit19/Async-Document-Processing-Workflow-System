# Async Document Processing Workflow

This is a full-stack application that allows users to upload documents, process them asynchronously in the background via Celery, track progress live via Server-Sent Events (SSE) and Redis Pub/Sub, and then review, finalize, and export the extracted structured data.

## Architecture Overview

- **Frontend**: React (Vite) + TypeScript. It uses pure CSS for a premium glassmorphic dark theme.
- **Backend API**: Python FastAPI for fast, async-ready REST endpoints.
- **Background Worker**: Celery for reliable background task processing outside the request-response cycle.
- **Database**: PostgreSQL with SQLAlchemy ORM (Synchronous via psycopg2, compatible with Celery threads).
- **Message Broker & Pub/Sub**: Redis. It handles Celery task queues and broadcasts live progress updates to the FastAPI SSE endpoint.

## Features implemented

1. Upload one or more documents.
2. Background processing job using Celery.
3. Live progress tracking using Redis Pub/Sub -> FastAPI SSE -> React.
4. Dashboard with search, filter by status, and sorting.
5. Review and finalize extracted output.
6. Retry for failed jobs.
7. Export finalized records to CSV and JSON.

## Setup Instructions

### Prerequisites
- Docker and Docker Compose
- Node.js (v18+)

### Running the application

1. **Start the backend infrastructure (Postgres, Redis, FastAPI, Celery)**
```bash
docker-compose up --build -d
```
The API will be available at `http://localhost:8000`.

2. **Start the frontend application**
```bash
cd frontend
npm install
npm run dev
```
The frontend will be available at `http://localhost:5173`.

## Assumptions & Tradeoffs

- **Local Storage**: Files are stored locally within the `uploads/` directory inside the Docker container rather than using S3. This simplifies local setup.
- **Synchronous SQLAlchemy**: We are using standard `psycopg2` synchronous sessions because Celery workers run synchronously. To maintain code reuse across FastAPI endpoints and Celery tasks, a synchronous DB session layer is used.
- **SSE vs WebSockets**: SSE (Server-Sent Events) is used for progress tracking because it's natively unidirectional (Server -> Client), automatically reconnects, and is simpler to proxy/scale than full duplex WebSockets.
- **Mock Processing**: The "processing" step is simulated with `time.sleep()`. The architecture however supports full AI/OCR integration by replacing the sleep blocks with actual models.
- **CORS**: Currently permissive (`*`) for development purposes.

## Note on AI tools
This project was developed with the assistance of the Antigravity AI coding assistant to quickly scaffold boilerplate code, React components, and Docker configurations.
