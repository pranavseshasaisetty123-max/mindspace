# Walkthrough - Sprint 5: Settings, Exporters & Productivity

This walkthrough captures the implementation details, database changes, API routes, verification logs, and architectural notes for Sprint 5.

---

## ⚙️ Sprint 5: Settings, Exporters & Productivity Features

We have completed the implementation of User Settings, Markdown/PDF Streaming Exporters, and Extended Dashboard Analytics.

### 1. User Settings & Preferences
* **Database Schema:** Created the `user_settings` table (revisions id: `9a58b8f219ff`) mapping a one-to-one relationship with `users` with cascade deletes.
* **Auto-Seeding:** Integrated preferences queries that automatically seed default configurations (`reminder_enabled=False`, `reminder_time="21:00"`, `timezone="UTC"`, `theme="dark"`) on a user's first check.
* **Validation Bounds:** Formulated regex validation constraints inside Pydantic schemas to reject invalid times (e.g. `25:00`) with HTTP validation warnings.

### 2. Streaming Exporters (Markdown & PDF)
* **Markdown Exporter:** Converts journal titles, metrics, dates, and drafts into clean markdown blocks.
* **Platypus PDF Exporter:** Employs **ReportLab Platypus** layouts (mapping titles, metadata cards, horizontal dividers, and body paragraph wraps). PageBreak flowables separate chronological lists.
* **In-Memory Streaming:** Streams file buffers directly from `io.BytesIO` buffers using FastAPI's `StreamingResponse`. This optimizes memory and bypasses disk cleanup scripts.
* **Ownership Controls:** Endpoints check that a user can only download their own journal logs, returning status 403 on violations.

### 3. Extended Analytics Dashboard Metrics
We expanded backend calculations inside `app/services/analytics.py` to aggregate:
* **Longest Writing Streak:** Scans all unique writing dates historically, groups consecutive day segments, and returns the maximum streak size.
* **Total Words Written:** Word counters aggregated across all active journal content fields.
* **Average Words per Journal:** Word counts divided by entry counts.
* **Entries this Week:** Queries entry counts between Monday and Sunday of the current week.
* **Total AI Reflections:** Returns the total count of reflections in `ai_reflections`.

### 4. Settings Frontend & Themes Switcher (React)
* **Visual settings page:** Created `/settings` providing sliders, timezone selects, and download action buttons.
* **Themes class swapper:** Selectors trigger theme class lists on `document.body` in real time, supporting:
  * **Slate Dark (Default):** baseline colors.
  * **Alabaster Light:** clean white design overrides.
  * **Aurora Glass:** translucent layouts with blurs.
* **Toast Notification Alerts:** Renders slide-in alerts displaying successes, loaders, or validation warnings.

---

## 2. API Endpoints Reference

| Protocol | Endpoint | Authorization | Status Codes | Description |
|---|---|---|---|---|
| **GET** | `/api/v1/settings` | Bearer Token | 200, 401 | Retrieve user settings (seeds defaults on miss). |
| **PUT** | `/api/v1/settings` | Bearer Token | 200, 401, 422 | Modify user settings. |
| **GET** | `/api/v1/export/journals/{id}` | Bearer Token | 200, 401, 403, 404 | Download a single entry as Markdown or PDF. |
| **GET** | `/api/v1/export/journals/all` | Bearer Token | 200, 401, 404 | Download entire journal history as a single file. |

---

## 3. Database Changes (MySQL DDL)

Migration revision `9a58b8f219ff` generates the following MySQL schema definitions:

```sql
CREATE TABLE user_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    reminder_enabled BOOLEAN NOT NULL DEFAULT 0,
    reminder_time VARCHAR(5) NOT NULL DEFAULT '21:00',
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    theme VARCHAR(20) NOT NULL DEFAULT 'dark',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX ix_user_settings_id ON user_settings(id);
CREATE INDEX ix_user_settings_user_id ON user_settings(user_id);
```

---

## 4. Verification & Testing

### Backend Unit Tests
We executed the async tests inside an in-memory SQLite environment using `pytest`.

```
============================= test session starts ==============================
collected 29 items

app/tests/test_analytics.py .....                                        [ 17%]
app/tests/test_auth.py ........                                          [ 44%]
app/tests/test_export.py .                                               [ 48%]
app/tests/test_journal.py .....                                          [ 65%]
app/tests/test_reflection.py .......                                     [ 89%]
app/tests/test_settings.py ...                                           [100%]

============================= 29 passed in 13.36s ==============================
```

### Frontend Production Build & Type Checking
* **Type Validation:** `npm run lint` (runs `tsc --noEmit`) -> Passed.
* **Client compile:** `npm run build` -> Succeeded in 1.81 seconds.
