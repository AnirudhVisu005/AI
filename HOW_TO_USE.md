# How to Use the Offline Support Chatbot

This file explains exactly how to use your app in simple steps.

## 1) Start the app

Open two terminals from repo root.

### Terminal A (Backend)

```powershell
.\.venv\Scripts\python -m uvicorn server.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Terminal B (Frontend)

```powershell
cd client
npm run dev -- --port 5173
```

If `5173` is busy, Vite may start on `5174`.

## 2) Open the app

Open the URL shown by Vite (usually `http://localhost:5173` or `http://localhost:5174`).

## 3) Use Chat tab

- Choose your current page context (for better answers).
- Type your question and send.
- Turn on Guided Mode to get step-by-step instructions.
- Use quick buttons for common prompts.

## 4) Use Admin tab (edit knowledge instantly)

- Add/Edit/Delete FAQs
- Add/Edit/Delete Error fixes
- Add/Edit/Delete Manual entries

Changes are saved to SQLite and are used immediately in the next chat request.
No retraining step is needed.

## 5) Use Analytics tab

See:
- Total questions asked
- Top questions
- Questions by page

## Is this fine-tuned or just pre-existing robotic replies?

Short answer: **It is NOT fine-tuned on your data.**

How it works:
- It retrieves the best match from your local FAQ/manual/error data (SQLite + retrieval logic).
- If Gemini API key is set, it may rewrite/synthesize that retrieved content into a more natural answer.
- If no API key, it returns pure local extracted answers.

So your app is not a fixed pre-programmed robotic bot with static responses only.
It is retrieval-based with optional AI phrasing, and your admin updates affect results immediately.

## Quick checks

Backend health:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

Expected: `status: ok`

## Common issue fixes

- If frontend is down: run `npm run dev` again inside `client`.
- If backend is down: restart uvicorn command above.
- If AI answer not showing: check `.env` has `GEMINI_API_KEY` and restart backend.
