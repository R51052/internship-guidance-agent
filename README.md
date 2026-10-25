# Internpath — Internship Guidance Agent

Internpath is a full-stack internship discovery application:

- **Backend:** FastAPI, MongoDB Atlas, JWT authentication, deterministic matching, bounded AI assistant.
- **Frontend:** React + Vite with a responsive dashboard, live opportunity catalog, profile editor, and AI assistant.
- **Live data:** a repeatable India-focused sync command stores source-linked employer and student-career records in MongoDB while preserving sync timestamps.

## Project layout

```text
internship-guidance-agent/
├── backend/                 # FastAPI application and MongoDB integration
├── frontend-react/          # React/Vite application
├── css/ js/ *.html          # Previous static frontend kept for compatibility
└── README.md
```

## 1. Configure the backend

Create or edit:

```text
backend/.env
```

Required persistent settings:

```env
DEMO_MODE=false
SEED_DEMO_DATA=false
MONGODB_URI=mongodb+srv://USERNAME:URL_ENCODED_PASSWORD@YOUR_CLUSTER.mongodb.net/
MONGODB_DATABASE=internship_guidance
JWT_SECRET=replace-with-a-random-secret-at-least-32-characters
```

For AI, use either provider or automatic selection:

```env
LLM_MODE=auto
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.8-flash
GROQ_API_KEY=
GROQ_MODEL=openai/gpt-oss-120b
GROQ_BASE_URL=https://api.groq.com/openai/v1
```

Keys stay in the backend `.env`; never put them in React or commit them.

To use Groq without OpenAI billing, set `LLM_MODE=groq` and add `GROQ_API_KEY`. Groq exposes an OpenAI-compatible chat-completions API, so the existing bounded tool-calling flow can be reused.

## 2. Start the FastAPI backend

From the project root:

```powershell
python -m uvicorn backend.main:app --reload --port 8000
```

Health check:

```text
http://127.0.0.1:8000/api/health
```

## 3. Synchronize India internship data

For an India-focused catalog sourced from official employer career pages, run:

```powershell
python -m backend.scripts.seed_india_internships
```

This stores source-linked records from Amazon, Salesforce, Cargill, Red Hat, Walmart Global Tech, GE Appliances, Hevo Data, Merkle Science, Sprinto, Microsoft, Oracle, and Adobe. The script removes the previous Western-heavy The Muse records so the React catalog stays focused on India. Some Microsoft, Oracle, and Adobe entries are official student-career search portals rather than a single job ID; always verify the live role page before applying.

## 4. Optional public-feed synchronization

The sync fetches recent internship listings from The Muse public jobs feed and upserts them into MongoDB:

```powershell
python -m backend.scripts.sync_live_internships --pages 5 --max-age-days 365
```

This currently stores up to 100 recent listings (20 per page), source-linked to The Muse. The source does not provide a guaranteed universal deadline, stipend, or active/closed flag, so missing facts stay empty instead of being invented. Always verify the employer page before applying.

The three curated Amazon Jobs records can be synchronized separately:

```powershell
python -m backend.scripts.seed_real_internships
```

## 5. Run the React frontend

In a second terminal:

```powershell
cd frontend-react
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

If the API runs elsewhere, create `frontend-react/.env.local`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## 6. Verify the application

```powershell
python -m pytest backend/tests -q
python -m compileall -q backend
cd frontend-react
npm run build
```

The React app supports registration, login, MongoDB-backed profile persistence, opportunity search/filtering, recommendations, and the AI assistant. The assistant returns a deterministic student toolkit based on the student's profile and top match: a four-week plan, project ideas, mock interview questions, resume upgrades, skill focus, and an application tracker checklist. It does not claim that an application was submitted; external application actions remain on the official employer page.

## Live-data limitation

“Live” here means the sync command fetches the source feed when run. The upstream feed does not guarantee that every result is still open, so Internpath labels the source and timestamp and keeps employer links for verification. Run the sync command whenever you want a fresh catalog; do not treat a listing as confirmed open until the source page confirms it.
