# Internship Guidance API

Python 3.10+ / FastAPI / PyMongo backend. All commands below run from the
`internship-guidance-agent` project root.

## Start an offline demo

```powershell
python -m pip install -r backend/requirements.txt
Copy-Item backend/.env.example backend/.env
python -m uvicorn backend.main:app --reload --port 8000
```

Interactive API documentation: `http://localhost:8000/docs`.
The provided environment example explicitly enables `DEMO_MODE=true`.
Without this flag the application requires MongoDB and a JWT secret with at
least 32 characters. It never falls back to demo storage after a database error.
Demo storage is thread-safe, process-local, and reset on restart. It automatically
seeds ten **synthetic sample opportunities**, labelled `is_demo: true`, with no
application URLs and no claims that the companies or openings are real.

## Persistent storage

Set `DEMO_MODE=false`, `MONGODB_URI`, `MONGODB_DATABASE`, and a random
`JWT_SECRET` in `backend/.env`. MongoDB is checked on startup and indexes enforce
unique user emails, IDs, and user/internship favorites. Revocable sessions use a
TTL index. Persistent mode starts empty; it never silently populates demo data.

To intentionally seed the same synthetic sample records into the configured
database, run `python -m backend.scripts.seed_demo_data`. This is idempotent;
`--overwrite` refreshes only known sample IDs and their relative dates. It does
not create demo accounts or delete user records.

## API contract

All application endpoints are under `/api`. Bearer authentication is required
except registration, login, and health. Registration returns a token immediately;
login uses JSON, not a form body. Set `Authorization: Bearer <access_token>`.

| Method | Endpoint | Body / purpose |
| --- | --- | --- |
| GET | `/api/health` | Storage and LLM mode; also available at `/health` |
| POST | `/api/auth/register` | `{ "name": "Student Name", "email": "student@example.com", "password": "a-long-passphrase" }` |
| POST | `/api/auth/login` | `{ "email": "student@example.com", "password": "a-long-passphrase" }` |
| POST | `/api/auth/logout` | Revokes the current JWT session |
| GET | `/api/auth/me` | Public user fields only |
| GET / PUT | `/api/profile` | Read / replace current profile; `/api/profiles/me` is an alias |
| GET | `/api/internships` | `q`, `location`, `domain`, `work_mode`, `min_stipend`, `include_expired`, `limit`, `offset` |
| GET | `/api/internships/{id}` | Canonical record plus the current profile match |
| GET | `/api/recommendations` | `limit`, `offset`, `include_ineligible`; returns ranked matches and weights |
| POST | `/api/agent/chat` | `{ "message": "Explain my skill gaps", "internship_ids": ["demo-python"] }` |
| POST | `/api/agent/skill-gap` | `{ "internship_id": "demo-python" }` |
| POST | `/api/agent/compare` | `{ "internship_ids": ["demo-python", "demo-data"] }` |
| GET | `/api/favorites` | Only current user's favorites, each with its stored internship |
| POST | `/api/favorites` | `{ "internship_id": "demo-python" }`; idempotent save |
| POST | `/api/favorites/{id}` | Equivalent save by path |
| DELETE | `/api/favorites/{id}` | Remove current user's saved record |

Example profile (`PUT` replaces the whole profile; omitted fields use defaults):

```json
{
  "full_name": "Student Name",
  "degree": "B.Tech",
  "year": 3,
  "cgpa": 8.2,
  "skills": ["Python", "FastAPI", "MongoDB"],
  "interests": ["Backend Development"],
  "preferred_locations": ["Bengaluru"],
  "preferred_work_mode": "remote",
  "min_stipend": 18000,
  "max_duration_months": 3
}
```

`available_from` accepts an ISO date. CGPA uses a 0–10 scale. Internship data
uses the normalized fields in `backend.models`; unavailable values are returned
as null/"Not specified" by the frontend rather than generated.

List responses use named arrays (`internships`, `recommendations`, `favorites`)
and `total`; paginated endpoints additionally return `limit` and `offset`.
Recommendation rows contain `internship`, `score` / `match_score`, `score_breakdown`,
`eligible`, `ineligibility_reasons`, `matched_skills`, `missing_skills`, and
`explanation`. See OpenAPI for all validated schemas.

## Matching

Deterministic weights are **skills 35, education 25, sector 20, location 15,
and internship mode 5**. Skill overlap and category comparisons are
case-insensitive. Sector preferences match the role title or domain. If a
student omits a soft preference, that criterion is excluded and the active
weights are normalized instead of silently penalizing or rewarding the profile.
Ties sort by internship ID.

Eligibility is a separate hard gate: expired deadlines, already-started roles,
availability, degree, year, and minimum CGPA. Missing required eligibility data
is not assumed qualified. A deadline today is valid. Recommendations exclude
ineligible records by default; `include_ineligible=true` includes diagnostic
reasons. Scores are fit measurements, not selection probabilities.

## AI and security

Passwords use Argon2id via `pwdlib`, a secure hashing alternative to bcrypt.
JWTs are HS256, expire, and require a live server-side session; logout invalidates
the token immediately. API responses never return password hashes or credential
validation inputs. Favorites and profiles are keyed to the authenticated user.
CORS uses explicit configured origins. All three AI routes share a per-user
sliding-window limit (`AI_RATE_LIMIT`, `AI_RATE_WINDOW_SECONDS`) and return HTTP
429 with `Retry-After` when exceeded. The limiter is process-local; use a shared
gateway limiter for multi-worker deployments.

`LLM_MODE=auto` uses the configured `OPENAI_API_KEY` if present; otherwise it uses
clearly labelled `mock` mode. `LLM_MODE=mock` forces offline AI. The integration
uses the official-compatible `/v1/chat/completions` HTTP contract, with a bounded
read-only tool loop, validated tool arguments, timeout, JSON guidance output,
and `store: false`. Provider failures degrade to explicitly labelled mock advice
and preserve actual database results. Names, bio, emails, password hashes, and
session data are not sent in the profile context.

All returned internship objects and ranking facts come from the repository, not
generated text. Tool execution is allowlisted: search, details, skill analysis,
comparison, and explain recommendations. The model cannot write to the database
or submit applications. An empty database returns empty results. Generated
guidance is kept separate from the server-rendered canonical match summaries.

## Checks

```powershell
python -m pytest backend/tests -q
python -m backend.scripts.validate_database
python -m backend.scripts.seed_demo_data
```

Tests use an isolated in-memory repository and mocked HTTP transport, so neither
MongoDB nor an OpenAI key is required. A real MongoDB contract test runs only
when `MONGODB_TEST_URI` is explicitly set; it uses and deletes a unique disposable
test database. The validator reports schema errors and orphaned records without
printing personal profile content or credentials.
