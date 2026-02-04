# Mining_app

A React + Vite + Tailwind frontend with a FastAPI backend connected to MongoDB Atlas and Google Gemini. This README explains how to set up both sides locally on macOS.

## ⚡ Quick Start

**For complete MongoDB integration details, see [MONGODB_INTEGRATION.md](./MONGODB_INTEGRATION.md)**

## Prerequisites
- Node.js 18+
- Python 3.10+ (3.11/3.12/3.13 are fine)
- MongoDB Atlas connection (already configured)
- A Google Gemini API key (keep it secret; never commit it)

## Project structure
```
backend/
  - main.py              # FastAPI application with API endpoints
  - database.py          # MongoDB connection configuration
  - models.py            # Pydantic data models
  - seed_database.py     # Database initialization script
  - requirements.txt     # Python dependencies
frontend/
  - src/
    - api/backend.ts     # API service layer
    - contexts/          # React context providers with API integration
    - components/        # UI components
```

---

## Backend (FastAPI + MongoDB)

### 1) Create and activate a virtual environment
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

### 3) Configure environment variables
Create a `.env` file in `backend/`:
```
MONGODB_URI=mongodb+srv://root:root@dbname.hyrc0.mongodb.net/?appName=dbname
GEMINI_API_KEY=your_real_key_here
CORS_ORIGIN=http://localhost:5173
PORT=8000
```

Never commit your real `.env`. There is a `.gitignore` in `backend/` and an example file `.env.example` for reference.

### 4) Seed the database (First time only)
```bash
python seed_database.py
```
This will populate MongoDB with initial data for energy, users, leaderboard, and admin settings.

### 5) Run the backend
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Backend health check:
```bash
curl -s http://localhost:8000/health
```

Endpoints:
- `POST /api/gemini/voice` – voice intent parsing for energy modes
- `POST /api/gemini/chat` – chat responses powered by Gemini

---

## Frontend (Vite React)

### 1) Install dependencies
```bash
cd frontend
npm install
```

### 2) Configure backend URL for local dev
Create `frontend/.env.local` (ignored by git):
```
VITE_BACKEND_URL=http://localhost:8000/api
```
This lets the app call `http://localhost:8001/api/...` directly. Alternatively, you can rely on Vite’s proxy configured in `vite.config.ts`—it uses `VITE_BACKEND_URL` to point `/api` to your backend.

### 3) Run the frontend
```bash
npm run dev
```
Open http://localhost:5173.

### 4) Verify integration
- Chat page: send a message and check DevTools → Network for `POST /api/gemini/chat` → 200
- Voice control: trigger an unmatched command; expect `POST /api/gemini/voice` → 200
If the call fails (e.g., missing key), the UI will gracefully fall back to local canned responses.

---

## Troubleshooting
- 404 on `/api/gemini/chat`:
  - Ensure the backend is running (8000) and `VITE_BACKEND_URL` is set, then restart `npm run dev`.
- `{"detail":"google-genai not available"}`:
  - Make sure you’re running uvicorn inside the virtual environment that has `google-genai` installed.
- `{"detail":"GEMINI_API_KEY is not set"}`:
  - Add it to `backend/.env` and restart uvicorn.

---

## Scripts quick reference
Frontend:
- `npm run dev` – start Vite
- `npm run build` – build for production
- `npm run preview` – preview production build

Backend:
- `uvicorn main:app --reload --port 8001` – run FastAPI in dev

---

## Security
- Keep your Gemini key server-side only in `backend/.env`.
- Never commit secrets. Use `.env.local` for frontend variables and `.env` in backend.

