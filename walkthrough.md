# Walkthrough - Sprint 3: AI Reflection Engine

This walkthrough captures the implementation details, database changes, API routes, verification logs, and architectural interview notes for Sprint 3.

---

## ⚡ Production API Resilience & Retries

To address Google Gemini API limit demand spikes (such as HTTP 503 warnings) in production, we implemented a robust resilience strategy:

### 1. Automatic Retries with Exponential Backoff
* **Model version:** Downgraded the default reflection model from `gemini-3.5-flash` to **`gemini-2.5-flash`**.
* **Retry schedule:**
  * Attempt 1: Immediate call.
  * Attempt 2: Sleep delay of 2.0 seconds.
  * Attempt 3: Sleep delay of 4.0 seconds.
* **Duration tracking:** Measures total API request duration using `time.perf_counter()` and prints logs on both successes and failures.

### 2. Degraded Recovery Pathways
If all three retry attempts fail, the API degrades gracefully instead of throwing exceptions:
1. **Cache Recovery:** If a pre-existing cached reflection exists in MySQL (even if outdated/stale), it is returned with the attribute `"is_outdated": true`. The React editor card displays a warning banner: *"AI service is temporarily busy. A fallback cached reflection has been displayed."*
2. **Local Fallback:** If no cached reflection exists, a deterministic python fallback is generated using NLP keyword mapping:
   * Summarizes the draft (takes first two sentences).
   * Identifies emotional triggers (e.g. searching for words like *happy, sad, anxious, stress, tired, productive*).
   * Generates a reflective prompt.
   * Model metadata: `Model: Local Fallback`.
   * Stored in the database so that subsequent GET requests load it cleanly.

---

## ⚙️ Sprint 3 Gemini Configuration Bug Investigation & Fix

A production configuration issue was identified where the backend container always launched in mock mode (`mock-gemini-2.5`) despite having a valid `GEMINI_API_KEY` in the host file `backend/.env`.

### 1. Root Cause Analysis
1. **Missing OS Environment Injection:** In `docker-compose.yml`, the `backend` service block lacked an `env_file` mapping. While host volumes mounted `backend/.env` inside the container at `/backend/.env`, the operating system environment of the container did not receive these variables.
2. **Settings Fallbacks:** Pydantic was fallback-defaulting to mock key placeholders because `GEMINI_API_KEY` was missing from the container's environment shell.
3. **Hardcoded Model Names:** Model version parameters were hardcoded in multiple places in the service layer, making it difficult to upgrade model families cleanly.
4. **Template Key Leak:** The template file `.env.example` had a real API key saved inside it, violating standard template design rules.

### 2. Solutions Implemented
* **Docker Compose Env Injection:** Updated the `backend` service in `docker-compose.yml` to load `./backend/.env` via the `env_file` block. Consolidating settings allowed us to remove the duplicate `environment` parameters.
* **Single Source of Truth (`GEMINI_MODEL`):**
  * Added `GEMINI_MODEL=gemini-2.5-flash` and `MOCK_AI=false` inside the active environment file `backend/.env`.
  * Exposed `GEMINI_MODEL` (default: `"gemini-2.5-flash"`) and `MOCK_AI` (default: `False`) parameters in the `Settings` class in `backend/app/config.py`.
  * Refactored `backend/app/services/gemini.py` to invoke the API using `settings.GEMINI_MODEL` dynamically.
* **Startup Logging:** Added verification logging in `backend/main.py`s `lifespan` handler to print status confirmations at boot time.
* **Template Sanitization:** Removed active keys from `backend/.env.example` and replaced them with placeholders.

### 3. Files Modified
* [docker-compose.yml](file:///Users/pranav/Desktop/mindspace/docker-compose.yml): Consolidating `env_file` mappings.
* [backend/.env](file:///Users/pranav/Desktop/mindspace/backend/.env): Adding model configuration variables.
* [backend/.env.example](file:///Users/pranav/Desktop/mindspace/backend/.env.example): Sanitizing templates.
* [backend/app/config.py](file:///Users/pranav/Desktop/mindspace/backend/app/config.py): Exposing configuration variables.
* [backend/main.py](file:///Users/pranav/Desktop/mindspace/backend/main.py): Adding boot logging confirmations.
* [backend/app/services/gemini.py](file:///Users/pranav/Desktop/mindspace/backend/app/services/gemini.py): Refactoring API URLs to dynamic parameters.

---

## 🛠️ Sprint 3 Manual Testing Bug Investigations & Fixes

Following manual testing, four critical production bugs were identified and fixed in the AI Reflection Engine:

### Issue 1: Remove Unintended Mock Mode Fallback
* **Root Cause:** The application was checking `settings.GEMINI_API_KEY == "mock-key-for-local-testing"` and unconditionally bypassing real Gemini API calls. Since the default placeholder was copied into the host `.env` file, the backend always returned mock reflections (`mock-gemini-1.5`) even when a key was present or when running inside Docker.
* **Resolution:** Added a `MOCK_AI` settings parameter (default `False`). The service layer now only fallback-mocks if:
  1. `settings.MOCK_AI` is explicitly set to `True`
  2. Or `settings.GEMINI_API_KEY` is missing or is set to default local testing values.
  Otherwise, it calls the Google Gemini API.

### Issue 2: Cache Invalidation Bug
* **Root Cause:** Inside SQLite (used for local tests), the `onupdate=func.now()` column definition does not automatically emit DDL triggers on row edits unless a column value is explicitly modified in Python. When updating junction tables (such as tag edits) or when modifying text fields, SQLAlchemy did not emit changes to the `updated_at` column. Consequently, the journal's `updated_at` timestamp was stale, leading `reflection_generated_at >= journal_updated_at` to incorrectly flag cache hits.
* **Resolution:** Modified the backend CRUD service layer `update_journal_entry` inside `app/services/journal.py` to explicitly assign `db_entry.updated_at = datetime.now()` before commit. This forces SQLAlchemy to update the journal entry row timestamp on every PUT request, correctly invalidating cached reflections.

### Issue 3: Crisis Scan Precedence
* **Root Cause:** Crisis scans were bundled inside the generator service instead of running before cache lookups. If a user edited an entry to contain a self-harm phrase, requesting reflection would hit the cached normal reflection of the previous entry and bypass the crisis warning display.
* **Resolution:** Placed crisis scanning precedence *first* inside both GET and POST service hooks. The app now pre-scans content for crisis keywords. If matched, it bypasses cache lookups and LLM calls, overwriting/writing the crisis warning resource card directly in the database.

### Issue 4: Muted Service Logs
* **Root Cause:** Logs were uninformative (`Yielding mock AI reflection`).
* **Resolution:** Updated log parameters inside `app/services/gemini.py` to print exact execution states:
  * Calling Gemini: `Using Gemini model: gemini-2.5-flash`
  * Calling Mock: `Using mock reflection because GEMINI_API_KEY is missing` or `Using mock reflection because MOCK_AI=true`.

---

## 1. Features Completed

### Backend AI Engine (FastAPI + Google Gemini API)
* **AIReflection Model:** Database entity `AIReflection` inside `app/models/reflection.py` mapped to journals with cascade delete rules.
* **Gemini Service Integration:** Configured an asynchronous client inside `app/services/gemini.py` that submits prompt blocks to Google's Gemini-2.5-flash API and requests structured JSON outputs.
* **Ethical Prompt Boundaries:** Programmed instructions explicitly preventing the model from issuing clinical diagnoses, therapeutic prescriptions, or claiming therapeutic authority.
* **Crisis Safety Filter:** Pre-checks self-harm keywords. If matched, it bypasses external requests, immediately logs a safety trigger, and saves/returns a supportive helpline resource card.
* **Intelligent Caching:** Reflections are reused unless the journal's `updated_at` is greater than the reflection's `generated_at` timestamp.
* **Alembic Migrations:** Executed revision `8d31a8f417cd` creating the `ai_reflections` table in MySQL.

### Frontend Integration (React + Tailwind CSS)
* **Insights display card:** Integrated an elegant card inside `JournalEditor.tsx` appearing below the tags panel for saved entries.
* **Pulsing skeleton loader:** Shows animated loaders during generation states.
* **Crisis Hotline Banner:** Highlights crisis safety messages inside a red banner with helpline resources when crisis filters are triggered.
* **Dynamic Re-generation:** Allows users to re-submit entries for analysis after editing, automatically updating the cached database reflections.

---

## 2. API Endpoints Reference

| Protocol | Endpoint | Authorization | Status Codes | Description |
|---|---|---|---|---|
| **POST** | `/api/v1/journals/{id}/generate-reflection` | Bearer Token | 200, 401, 403, 404, 502 | Trigger Google Gemini reflection insights generation (or update stale cache). |
| **GET** | `/api/v1/journals/{id}/reflection` | Bearer Token | 200, 401, 403, 404 | Retrieve cached AI reflection, returning 404 on cache miss. |

---

## 3. Database Changes (MySQL DDL)

Migration revision `8d31a8f417cd` generates the following MySQL schema definitions:

```sql
CREATE TABLE ai_reflections (
    id INT AUTO_INCREMENT PRIMARY KEY,
    journal_id INT NOT NULL UNIQUE,
    summary TEXT NOT NULL,
    detected_patterns TEXT NOT NULL,
    reflection_question TEXT NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    model_used VARCHAR(50) NOT NULL,
    FOREIGN KEY (journal_id) REFERENCES journal_entries(id) ON DELETE CASCADE
);

CREATE INDEX ix_ai_reflections_id ON ai_reflections(id);
CREATE INDEX ix_ai_reflections_journal_id ON ai_reflections(journal_id);
```

---

## 4. Verification & Testing

### Backend Unit Tests
We executed the async tests inside an in-memory SQLite environment using `pytest`.

```
============================= test session starts ==============================
collected 20 items

app/tests/test_auth.py ........                                          [ 40%]
app/tests/test_journal.py .....                                          [ 65%]
app/tests/test_reflection.py .......                                     [100%]

============================== 20 passed in 9.98s ==============================
```

### Frontend Production Build & Type Checking
* **Type Validation:** `npm run lint` (runs `tsc --noEmit`) -> Passed.
* **Client compile:** `npm run build` -> Succeeded in 1.10 seconds.

---

## 5. Architectural Design Decisions & Interview Preparation

### 1. Naive Datetime Cache Comparisons
* **Decision:** We parsed datetime stamps to naive states (`replace(tzinfo=None)`) before comparison.
* **Why it matters:** Databases store timestamps in local timezone contexts which often lose offset details. Comparing offset-aware datetimes with database-fetched naive datetimes raises `TypeError`. Naive conversions ensure robust comparisons regardless of active timezone defaults.

### 2. Prompt JSON enforcement (`responseMimeType`)
* **Decision:** Configured the Gemini call generation config with `responseMimeType: "application/json"`.
* **Why it matters:** Standard LLM calls return markdown wrappers (e.g. ` ```json ` blocks), requiring regex cleaning before JSON loading. Restricting the mime type forces Gemini to deliver a pure JSON string, preventing parsing failures.

### 3. Crisis Safety keyword bypass
* **Decision:** Used localized keyword checks rather than relying on external LLM classification.
* **Why it matters:** Running AI classifications for self-harm increases latency and introduces model classification errors. Local parsing is instant, runs in O(N), works offline, and guarantees a safe response.
