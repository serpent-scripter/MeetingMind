# Backend Development Plan: MeetingMind

## 1️⃣ Executive Summary

- **Objective:** Build a scalable, asynchronous Python backend for the MeetingMind application.
- **Constraints:**
  - FastAPI (Python 3.13, async)
  - MongoDB Atlas using Motor and Pydantic v2 models
  - No Docker
  - Manual testing required after every task via frontend
  - Single-branch Git workflow (`main` only)
  - Background tasks handled synchronously or with FastAPI `BackgroundTasks`
  - Inline sensible defaults for missing details
- **Sprints:** 6 dynamic sprints covering all frontend-visible features from environment setup to core meeting management and processing.

## 2️⃣ In-Scope & Success Criteria

- **Features in Scope:**
  - User Authentication (Signup, Login, Logout)
  - Meeting Recording (create, view, edit title, delete, list)
  - Transcript generation, view, and export
  - AI-Generated Summary & Insights view and edit
  - Action Items extraction, manual creation, edit, status update, and list
  - User profile settings, storage usage view, account deletion
- **Success Criteria:**
  - All frontend features functional end-to-end.
  - All task-level tests pass via UI.
  - Each sprint's code pushed to `main` after verification.

## 3️⃣ API Design

- **Base path:** `/api/v1`
- **Error envelope:** `{ "error": "message" }`

### Auth Endpoints

- **POST /api/v1/auth/signup:** Register new user. Request: `{ "email", "password", "name" }`. Response: `{ "message": "Success" }`.
- **POST /api/v1/auth/login:** Authenticate user. Request: `{ "email", "password" }`. Response: `{ "access_token" }`.
- **POST /api/v1/auth/logout:** Clear session. Response: `{ "message": "Logged out" }`.
- **GET /api/v1/auth/me:** Get current user profile. Response: `{ "id", "email", "name", "storageUsed" }`.

### Meeting Endpoints

- **GET /api/v1/meetings:** List user's meetings (search/filter by title/content). Response: `[{ "id", "title", "duration", "recordedAt", "status" }]`.
- **POST /api/v1/meetings:** Create a new meeting recording entry. Request: `multipart/form-data` with `audioFile` and `title`. Response: `{ "id", "title", "status" }`.
- **GET /api/v1/meetings/{id}:** Get meeting details including metadata, transcript, summary, and action items.
- **PATCH /api/v1/meetings/{id}:** Edit meeting title or notes. Request: `{ "title" }`. Response: updated meeting.
- **DELETE /api/v1/meetings/{id}:** Archive meeting (soft delete).

### Action Items Endpoints

- **GET /api/v1/actions:** List all user action items. Response: `[{ "id", "meetingId", "description", "status", "dueDate" }]`.
- **POST /api/v1/actions:** Manually add action item. Request: `{ "meetingId", "description" }`.
- **PATCH /api/v1/actions/{id}:** Update action item (status/details). Request: `{ "status", "description", "dueDate" }`.
- **DELETE /api/v1/actions/{id}:** Archive/complete action item.

### User Settings

- **PATCH /api/v1/users/me:** Update profile. Request: `{ "name", "password" }`.
- **DELETE /api/v1/users/me:** Delete account.

## 4️⃣ Data Model (MongoDB Atlas)

- **users**
  - Fields: `_id` (ObjectId), `email` (string, required), `passwordHash` (string, required), `name` (string, required), `storageUsed` (int, default 0), `createdAt` (datetime)
  - Example: `{ "email": "user@example.com", "name": "Marcus", "storageUsed": 1048576 }`

- **meetings**
  - Fields: `_id` (ObjectId), `ownerId` (ObjectId, referenced), `title` (string, required), `audioFilePath` (string, required), `duration` (int, required), `status` (string, default "processing"), `recordedAt` (datetime), `createdAt` (datetime), `isArchived` (boolean, default false)
  - Example: `{ "title": "Standup", "duration": 1800, "status": "completed", "audioFilePath": "/uploads/audio.webm" }`

- **transcripts**
  - Fields: `_id` (ObjectId), `meetingId` (ObjectId, referenced), `content` (string), `timestampedSegments` (array), `generatedAt` (datetime)
  - Example: `{ "meetingId": "60d5ec...", "content": "Hello world...", "timestampedSegments": [] }`

- **summaries**
  - Fields: `_id` (ObjectId), `meetingId` (ObjectId, referenced), `summaryText` (string), `keyPoints` (array of strings), `originalVersion` (string), `generatedAt` (datetime)
  - Example: `{ "meetingId": "60d5ec...", "summaryText": "Discussed AI...", "keyPoints": ["AI limits"] }`

- **actionItems**
  - Fields: `_id` (ObjectId), `meetingId` (ObjectId, referenced), `ownerId` (ObjectId, referenced), `description` (string, required), `assignee` (string), `dueDate` (datetime), `status` (string, default "pending"), `source` (string, default "ai-generated")
  - Example: `{ "description": "Review PRD", "status": "pending", "source": "manual" }`

## 5️⃣ Frontend Audit & Feature Map

- **Dashboard (/):** Shows recent meetings and upcoming action items. Requires `GET /api/v1/meetings` and `GET /api/v1/actions`. Auth required.
- **Recording View (/record):** Audio capture interface. Requires `POST /api/v1/meetings` (multipart upload). Auth required.
- **Meeting Detail (/meetings/:id):** Displays audio, transcript, summary, and action items. Requires `GET /api/v1/meetings/{id}`, `PATCH /api/v1/meetings/{id}`. Auth required.
- **Meetings List (/meetings):** Full list with search. Requires `GET /api/v1/meetings` with search params. Auth required.
- **Action Items (/actions):** Full action items list. Requires `GET /api/v1/actions`, `PATCH /api/v1/actions/{id}`. Auth required.
- **Settings (/settings):** Profile updates. Requires `GET /api/v1/auth/me`, `PATCH /api/v1/users/me`, `DELETE /api/v1/users/me`. Auth required.

## 6️⃣ Configuration & ENV Vars (core only)

- `APP_ENV` — development
- `PORT` — 8000
- `MONGODB_URI` — MongoDB Atlas connection string
- `JWT_SECRET` — token signing key
- `JWT_EXPIRES_IN` — 86400
- `CORS_ORIGINS` — http://localhost:3000
- `OLLAMA_API_URL` — http://localhost:11434/api/generate

## 7️⃣ Background Work

- **Processing Audio:** Triggered after `POST /api/v1/meetings`. Uses `BackgroundTasks` to call AssemblyAI API for transcription, then local Ollama Llama 3 model for summary and action items, updating meeting `status` to "completed". UI polls `GET /api/v1/meetings/{id}` until status is "completed".

## 8️⃣ Integrations

- **AI Models (AssemblyAI / Local Llama 3 via Ollama):** API calls for speech-to-text (using [AssemblyAI](https://www.assemblyai.com/)) and local LLM processing.
  - Env vars: `ASSEMBLYAI_API_KEY`, `OLLAMA_API_URL`

## 9️⃣ Testing Strategy (Manual via Frontend)

- Validation only through frontend UI.
- Every task includes a **Manual Test Step** and a **User Test Prompt**.
- After all tasks in a sprint pass: **Commit and push to main**.

## 🔟 Dynamic Sprint Plan & Backlog (S0 → S5)

### S0 – Environment Setup & Frontend Connection (Always)

**Objectives:**

- Create FastAPI skeleton with `/api/v1` and `/healthz`
- Connect to MongoDB Atlas
- Enable CORS
- Initialize Git and .gitignore
  **Tasks:**
- Setup FastAPI and Motor client
  - **Manual Test Step:** Run backend, hit `/healthz` via browser/network tab → 200 OK with DB status
  - **User Test Prompt:** "Start the backend and refresh the app. Confirm that the status shows successful DB connection."
    **Definition of Done:** Backend runs, DB connects, frontend renders live data, repo live on GitHub `main`.
    **Post-sprint:** Commit and push to `main`

### S1 – Basic Auth (Signup / Login / Logout)

**Objectives:** Implement JWT auth
**Tasks:**

- Implement signup
  - **Manual Test Step:** Sign up via UI → success message visible
  - **User Test Prompt:** "Create a new account and verify confirmation."
- Implement login
  - **Manual Test Step:** Log in → token saved → redirected to dashboard
  - **User Test Prompt:** "Log in and confirm redirection to dashboard."
- Implement logout
  - **Manual Test Step:** Click logout → protected pages blocked
  - **User Test Prompt:** "After logout, refresh a protected page — it should redirect to login."
    **Definition of Done:** Auth flow works end-to-end.
    **Post-sprint:** Commit and push to `main`

### S2 – Meeting Recording

**Objectives:** Handle meeting creation and audio upload
**Tasks:**

- Implement meeting creation endpoint with local file save
  - **Manual Test Step:** Record in UI, click stop → meeting appears in list as processing
  - **User Test Prompt:** "Start a new recording, talk for 10 seconds, stop it, and verify it appears in your meetings list."
- Implement audio playback and meeting list endpoint
  - **Manual Test Step:** Click on the new meeting → audio plays back
  - **User Test Prompt:** "Go to the dashboard, click on the recent meeting, and verify you can play back the recorded audio."
    **Definition of Done:** Users can record, save, and play back meetings.
    **Post-sprint:** Commit and push to `main`

### S3 – Transcripts, Summaries, & Action Items Generation

**Objectives:** Integrate AI processing
**Tasks:**

- Add background task for AssemblyAI API and LLM summarization
  - **Manual Test Step:** Record a meeting → wait 2 minutes → status changes to completed
  - **User Test Prompt:** "Record a short meeting, wait for it to process, and verify the status updates to completed."
- Add endpoints to fetch transcript, summary, and action items
  - **Manual Test Step:** Open processed meeting → view transcript and summary tabs
  - **User Test Prompt:** "Open a completed meeting and verify that the transcript and AI-generated summary are visible."
    **Definition of Done:** AI processing accurately populates meeting details.
    **Post-sprint:** Commit and push to `main`

### S4 – Action Items Management & Search

**Objectives:** Full CRUD for action items and meeting search
**Tasks:**

- Implement action item manual creation, edit, and status toggle
  - **Manual Test Step:** Go to Action Items tab → mark item complete or edit description
  - **User Test Prompt:** "Navigate to the Action Items page, edit an item's description, and mark it as complete."
- Implement meeting search by title
  - **Manual Test Step:** Type in search bar → meetings list filters correctly
  - **User Test Prompt:** "Go to the Meetings list, type a keyword in the search bar, and verify the correct meetings are shown."
    **Definition of Done:** Users can manage action items and find meetings.
    **Post-sprint:** Commit and push to `main`

### S5 – User Settings & Deletion

**Objectives:** Manage profile and meeting archiving
**Tasks:**

- Implement profile update and storage stats
  - **Manual Test Step:** Go to Settings → update name → see updated name
  - **User Test Prompt:** "Navigate to Settings, change your name, save, and verify the new name appears."
- Implement meeting soft delete and account deletion
  - **Manual Test Step:** Archive a meeting → it disappears from main list
  - **User Test Prompt:** "Archive a meeting and verify it no longer shows up in your primary dashboard list."
    **Definition of Done:** Users can manage account details and delete content.
    **Post-sprint:** Commit and push to `main`
