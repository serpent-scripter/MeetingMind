# MeetingMind Backend

## Project Overview

The MeetingMind backend is built with FastAPI and MongoDB. It provides the core API for meeting transcriptions, action item extractions, and user management. It integrates with external services such as AssemblyAI for audio transcription and Groq for fast LLM inference (e.g., generating summaries and action items).

## Project Structure

The backend has been refactored into a clean and modular architecture:

- `api/`: Contains the FastAPI application routers (`auth.py`, `meetings.py`, `users.py`, `actions.py`).
- `core/`: Core configurations, security utilities, constants, and logging.
- `db/`: Database connection and MongoDB setup.
- `schemas/`: Pydantic models for request and response validation.
- `services/`: Business logic, background tasks, and utility functions (e.g., interacting with AssemblyAI and Groq).
- `tests/`: Comprehensive test suite using Pytest.

## Setup & Installation

1. **Create a Virtual Environment**:
   It is recommended to use a virtual environment. For example, using `venv` (named `venv_arm` for ARM-based Mac users, or just `venv`):

   ```bash
   python3 -m venv venv_arm
   ```

2. **Activate the Virtual Environment**:
   - On macOS/Linux:
     ```bash
     source venv_arm/bin/activate
     ```
   - On Windows:
     ```bash
     venv_arm\Scripts\activate
     ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Environment Variables

Copy the provided `.env.example` file to a new file named `.env`:

```bash
cp .env.example .env
```

Open the `.env` file and fill in the required API keys (e.g., AssemblyAI, Groq, MongoDB URI, JWT Secret).

## Running the Server

Start the Uvicorn development server with live reloading:

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`. You can access the interactive API documentation at `http://127.0.0.1:8000/docs`.

## Running Tests

To run the complete test suite with coverage reporting, use the following command:

```bash
PYTHONPATH=. pytest --cov=. --cov-report=term-missing
```
