# Offline Support Chatbot — README

Short: Local-first support chatbot (React + FastAPI) with hybrid retrieval (BM25 + embeddings) and optional LLM synthesis.

Repository layout (important):

- `client/` — React + Vite frontend.
- `server/` — FastAPI backend, retrieval code, and scripts.

Quick start (development)

1. Backend (recommended in PowerShell on Windows):

```powershell
cd server
.\.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python build_indexes.py   # optional: builds FAISS and embedding artifacts
$env:PYTHONPATH = "."
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

2. Frontend (from repo root):

```bash
cd client
npm install
npm run dev
# or build: npm run build
```

API Endpoints

- `POST /api/chat` — chat endpoint
- `GET/POST/PUT/DELETE /api/admin/*` — admin CRUD for faqs/manuals/errors
- `GET /api/admin/analytics` — analytics from chat logs

Docker (backend + frontend)

1. Build and run with `docker-compose` (requires Docker Engine):

```bash
docker compose up --build
```

2. Backend will be available at `http://localhost:8000` and frontend at `http://localhost:5173` (served by nginx via the frontend image).

Notes & recommendations

- The app can run fully locally but `faiss`, `torch`, and other native packages are heavy — ensure platform compatibility.
- `GEMINI_API_KEY` environment variable enables optional LLM synthesis; set it in your environment or Docker compose when using AI features.
- Production hardening recommended: add authentication, rate-limiting, background workers for embedding/index builds, and swap SQLite for Postgres if scaling.

Where to look next

- Core backend: [server/app/main.py](server/app/main.py)
- Retrieval: [server/retrieval/](server/retrieval/)
- Frontend app: [client/src/App.tsx](client/src/App.tsx)
# Offline Support Chatbot

A fully offline support assistant for application help and user-manual guidance. Features AI-powered responses, guided tutorials, error explanations, and context-aware help.

## Features

✅ **Instant Answers** - Direct answers to FAQs and manuals  
✅ **Guided Mode** - Step-by-step tutorials and instructions  
✅ **Error-Aware Help** - Explains specific error codes and suggests fixes  
✅ **Context-Aware** - Knows which page you're on for relevant suggestions  
✅ **Admin Panel** - Add/edit/delete FAQs, errors, and manuals without retraining  
✅ **Analytics** - Track questions, top topics, and page-specific trends  
✅ **100% Offline** - No external dependencies or hosted services  
✅ **Local Storage** - SQLite for persistence, JSON seed files for data  

## Tech Stack

- **Frontend**: React 18 + TypeScript + Vite + Framer Motion
- **Backend**: FastAPI + SQLite + Python 3.8+
- **Styling**: Custom CSS with dark theme
- **Optional**: Google Gemini API for enhanced responses (no API key = pure local mode)

## Project Layout

```
├── client/                   # React frontend
│   ├── src/
│   │   ├── App.tsx          # Main chat, admin, analytics UI
│   │   ├── main.tsx         # React entry point
│   │   └── styles.css       # Dark theme styling
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── server/                   # FastAPI backend
│   ├── app/
│   │   └── main.py          # API endpoints & search logic
│   ├── data/
│   │   ├── faq_seed.json    # FAQ seed data
│   │   ├── error_seed.json  # Error responses
│   │   ├── manual_seed.json # User manual content
│   │   └── support.db       # SQLite database (auto-created)
│   ├── requirements.txt
│   └── .venv/               # Virtual environment (create this)
└── README.md
```

## Quick Start

### Prerequisites

- **Python 3.8+** (for backend)
- **Node.js 16+** (for frontend)
- **pip** and **npm** (usually included)

### 1. Backend Setup

```bash
cd server

# Create virtual environment
python -m venv .venv

# Activate it
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload --port 8000
```

The server starts on **http://127.0.0.1:8000**. Seed data loads automatically on first run.

### 2. Frontend Setup (in another terminal)

```bash
cd client

# Install dependencies
npm install

# Start dev server
npm run dev
```

The frontend opens on **http://localhost:5173** and proxies API calls to the backend.

### 3. Open the App

Visit **http://localhost:5173** in your browser. The chatbot is ready to use!

## How to Use

### Chat Tab
- **Ask questions** like "How do I upload a file?" or "I'm getting an error"
- **Enable Guided Mode** for step-by-step tutorials
- **Select your current page** for context-aware suggestions
- **Quick buttons** for common tasks: Upload Help, Report Issue, Show Steps, Contact Admin

### Admin Tab
Manage your knowledge base (no API keys or retraining needed):
- **FAQs** - Add, edit, delete questions and answers
- **Errors** - Create error codes, messages, and fixes
- **Manuals** - Build step-by-step guides for complex features

All changes take effect immediately.

### Analytics Tab
- **Total Questions Asked** - Track engagement
- **Top Questions** - Identify common user needs
- **Questions by Page** - See which pages get most help requests

## API Endpoints

### Chat
- `POST /api/chat` - Send question, get answer
  ```json
  {
    "message": "How to upload?",
    "page": "Upload Page",
    "guided_mode": false,
    "current_error": null
  }
  ```

### Admin (FAQs)
- `GET /api/admin/faqs` - List all FAQs
- `POST /api/admin/faqs` - Add FAQ
- `PUT /api/admin/faqs/{id}` - Update FAQ
- `DELETE /api/admin/faqs/{id}` - Delete FAQ

### Admin (Errors)
- `GET /api/admin/errors` - List error responses
- `POST /api/admin/errors` - Add error response
- `PUT /api/admin/errors/{id}` - Update error
- `DELETE /api/admin/errors/{id}` - Delete error

### Admin (Manuals)
- `GET /api/admin/manuals` - List manuals
- `POST /api/admin/manuals` - Add manual
- `PUT /api/admin/manuals/{id}` - Update manual
- `DELETE /api/admin/manuals/{id}` - Delete manual

### Analytics
- `GET /api/admin/analytics` - Usage stats

## Customization

### Add More Seed Data

Edit JSON files in `server/data/`:
- `faq_seed.json` - FAQs with tags and page context
- `error_seed.json` - Error keys, messages, and fixes
- `manual_seed.json` - Tutorial content and guides

### Enable AI Synthesis (Optional)

Add Gemini API key:
```bash
# Set environment variable
set GEMINI_API_KEY=your_api_key_here  # Windows
export GEMINI_API_KEY=your_api_key_here  # macOS/Linux

# Run server
uvicorn app.main:app --reload --port 8000
```

Without an API key, the app uses pure local search (still great!).

### Customize Theme

Edit `client/src/styles.css`:
- Change `--accent` and `--user-bg` for button colors
- Modify `--bg` and `--panel` for dark/light theme
- Adjust `--text` and `--muted` for typography

## Production Build

### Frontend
```bash
cd client
npm run build
# Output in client/dist/
```

### Backend
```bash
cd server
pip install gunicorn
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Troubleshooting

### Backend won't start
- Check Python version: `python --version` (need 3.8+)
- Verify venv is activated
- Reinstall requirements: `pip install -r requirements.txt --force-reinstall`

### Frontend shows "Cannot find module"
- Delete `node_modules/` and `package-lock.json`
- Run `npm install` again

### API calls failing
- Ensure backend runs on port 8000
- Check `client/vite.config.ts` proxy setting
- Frontend must be on `localhost:5173`

### Data not persisting
- Check if `server/data/support.db` exists
- Verify SQLite is installed: `python -m sqlite3 --version`
- Clear database and restart: delete `.db` file, restart server

## Notes

- The backend stores editable FAQs, errors, and manuals in SQLite at `server/data/support.db`
- Local seed files are loaded automatically on first startup
- Chat history is tracked in `chat_logs` table for analytics
- No external AI service is required (Gemini is optional for enhancement)
- All data stays offline — perfect for sensitive environments

## Future Ideas

- 📱 Mobile app version
- 🎤 Voice input for questions
- 🌐 Multi-language support
- 📊 Advanced ML-based answer ranking
- 🔗 Deep linking to app sections
- 💬 Live chat escalation to admin

---

**Built with React, FastAPI, and ❤️ for great UX**

