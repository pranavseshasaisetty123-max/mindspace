# MindSpace (Working Title)

An AI-powered private reflection and journaling platform designed to help students and young professionals express thoughts, build healthy reflection habits, and track emotional states over time without clinical diagnostics.

---

## 🏗️ System Architecture

```mermaid
graph TB
    subgraph Client Tier [Frontend React App]
        React[Vite + React SPA] -->|Axios Client / JWT| Router[React Router Guards]
        Router --> Context[Auth Context API]
    end

    subgraph API Tier [FastAPI Backend Service]
        Server[FastAPI App]
        AuthRouter[Auth Controller]
        JournalRouter[Journal CRUD Router]
        JournalService[JournalService Layer]
        DBConnection[SQLAlchemy Session manager]
        Crypt[Bcrypt Hashing / pyjwt Service]
    end

    subgraph Storage Tier [MySQL Database]
        MySQL[(MySQL 8.0 DB)]
    end

    React -->|HTTPS REST API requests| Server
    Server --> AuthRouter
    Server --> JournalRouter
    JournalRouter --> JournalService
    JournalService --> DBConnection
    AuthRouter --> Crypt
    AuthRouter --> DBConnection
    DBConnection -->|SQLAlchemy Async Query| MySQL
```

---

## 🚀 Tech Stack

* **Frontend:** React 18, Vite, Tailwind CSS, React Router, Lucide Icons, Axios.
* **Backend:** FastAPI, SQLAlchemy ORM, Alembic Migrations, PyJWT (token auth), Bcrypt (password security).
* **Database:** MySQL 8.0 (Relational persistent storage).
* **Virtualization:** Docker, Docker Compose.
* **Testing:** Pytest (including `pytest-asyncio` and `aiosqlite` for isolated async test runs).

---

## 📂 Repository Structure

```
mindspace/
├── docker-compose.yml
├── README.md
├── software_design_document.md
├── walkthrough.md
├── frontend/                  # React Single-Page Application
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── src/
│       ├── components/        # Protected routes & UI helpers
│       ├── contexts/          # Auth JWT Context API
│       ├── pages/             # Login, Register, Dashboard, Editor, and Timeline Pages
│       └── main.tsx
└── backend/                   # FastAPI Web Application
    ├── Dockerfile
    ├── requirements.txt
    ├── main.py                # Server mount
    ├── app/
    │   ├── config.py          # Settings validation
    │   ├── database.py        # SQLAlchemy connections
    │   ├── models/            # SQLAlchemy DB entities (User, JournalEntry, Tag)
    │   ├── schemas/           # Pydantic validation rules (User, Journal)
    │   ├── routes/            # Register, login, profile, and journal controllers
    │   ├── services/          # Hashing, JWT signature, and journal CRUD engines
    │   └── tests/             # Async Pytest suite (Auth & Journaling tests)
    └── alembic/               # Schema evolution versioning
```

---

## 🗄️ Database Schema & Relational Design

MindSpace utilizes a normalized relational schema. Indexes are established on foreign keys and search coordinates to guarantee sub-millisecond retrieval.

### Table: `users`
* `id` (INT, Primary Key, Auto-Increment)
* `email` (VARCHAR(255), Unique, Indexed, Not Null)
* `password_hash` (VARCHAR(255), Not Null)
* `created_at` (TIMESTAMP, Default: CURRENT_TIMESTAMP)
* `updated_at` (TIMESTAMP, Default: CURRENT_TIMESTAMP)

### Table: `journal_entries`
* `id` (INT, Primary Key, Auto-Increment)
* `user_id` (INT, Foreign Key referencing `users(id)` ON DELETE CASCADE, Indexed, Not Null)
* `title` (VARCHAR(255), Not Null)
* `content` (TEXT, Not Null)
* `mood` (TINYINT, Range 1-5, Not Null)
* `stress_level` (TINYINT, Range 1-5, Not Null)
* `energy_level` (TINYINT, Range 1-5, Not Null)
* `sleep_hours` (DECIMAL(4,2), Not Null)
* `created_at` (TIMESTAMP, Default: CURRENT_TIMESTAMP)
* `updated_at` (TIMESTAMP, Default: CURRENT_TIMESTAMP)
* `deleted_at` (TIMESTAMP, Nullable) -- *Used for user soft-deletes*

### Table: `tags`
* `id` (INT, Primary Key, Auto-Increment)
* `user_id` (INT, Foreign Key referencing `users(id)` ON DELETE CASCADE, Indexed, Not Null) -- *Ensures tags remain private and user-scoped*
* `name` (VARCHAR(100), Indexed, Not Null)

### Table: `journal_tags` (Junction Table)
* `entry_id` (INT, Foreign Key referencing `journal_entries(id)` ON DELETE CASCADE, Primary Key)
* `tag_id` (INT, Foreign Key referencing `tags(id)` ON DELETE CASCADE, Primary Key)

---

## ⚙️ Environment Variables

The backend uses a `.env` file to manage configurations. Pydantic validates these variables at server startup, causing the system to fail fast if critical values are missing:

| Variable | Type | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | String | *Required* | Connection string. Format: `mysql+aiomysql://<user>:<pass>@<host>:<port>/<db>` |
| `JWT_SECRET_KEY` | String | *Required* | Cryptographic salt used to sign JWT signatures. |
| `JWT_ALGORITHM` | String | `HS256` | Encrypt signature hashing algorithm used. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Integer | `1440` | Token validity timeframe in minutes (24 hours). |

---

## 📋 API Endpoints Reference

| Protocol | Endpoint | Authorization | Status Codes | Description |
|---|---|---|---|---|
| **POST** | `/api/v1/auth/register` | None | 201, 400, 422 | Register user account. Requires valid email & strong password. |
| **POST** | `/api/v1/auth/login` | None | 200, 401, 422 | Authenticate and retrieve bearer access tokens. |
| **GET** | `/api/v1/profile` | Bearer Token | 200, 401 | Retrieve profile details of the active user. |
| **POST** | `/api/v1/journals` | Bearer Token | 201, 400, 401, 422 | Create new journal entry with metric ratings and tag list. |
| **GET** | `/api/v1/journals` | Bearer Token | 200, 401 | List user journals. Supports filters: `mood`, `tag`, `start_date`, `end_date`, `search`. |
| **GET** | `/api/v1/journals/{id}` | Bearer Token | 200, 401, 403, 404 | Fetch individual entry. Validates user ownership. |
| **PUT** | `/api/v1/journals/{id}` | Bearer Token | 200, 401, 403, 404, 422 | Modify entry text fields, metrics, or rebuild tag mappings. |
| **DELETE** | `/api/v1/journals/{id}` | Bearer Token | 200, 401, 403, 404 | Soft delete entry (sets `deleted_at` timestamp). |

---

## 🛠️ Database Migrations (Alembic)

Alembic runs migrations synchronously. The env script `backend/alembic/env.py` automatically converts async driver protocols `mysql+aiomysql://` and `sqlite+aiosqlite://` to standard sync ones `mysql+pymysql://` and `sqlite://` to avoid event-loop conflicts.

* **Generate a new migration script (autodetect schema changes):**
  ```bash
  DATABASE_URL=sqlite+aiosqlite:///local.db .venv/bin/alembic revision --autogenerate -m "description_of_change"
  ```
* **Apply migrations to database (Upgrade to HEAD):**
  * *Local environment:*
    ```bash
    .venv/bin/alembic upgrade head
    ```
  * *Docker environment:*
    ```bash
    docker-compose exec backend alembic upgrade head
    ```
* **Rollback a migration (Downgrade by 1 step):**
  ```bash
  .venv/bin/alembic downgrade -1
  ```

---

## ⚙️ Setup & Running Guide

### Containerized Execution (Docker Compose)
1. Ensure the Docker Daemon is active on your host.
2. Run the following command in the project root:
   ```bash
   docker-compose up --build
   ```
3. The frontend is accessible at `http://localhost:5173`, and the FastAPI Swagger UI is at `http://localhost:8000/docs`.

### Local Development (Host-Based Execution)

#### Backend Configuration
1. Navigate to `/backend`.
2. Initialize and activate a Python virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install package dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy env template and set local database environment variables:
   ```bash
   cp .env.example .env
   ```
5. Launch the FastAPI development server:
   ```bash
   uvicorn main:app --reload
   ```

#### Frontend Configuration
1. Navigate to `/frontend`.
2. Install npm modules:
   ```bash
   npm install
   ```
3. Boot the local Vite development server:
   ```bash
   npm run dev
   ```

---

## 🧪 Testing and Verification

### Backend Pytest Suite
We test all API handlers (registration checks, duplicates, password hashes, and headers) inside an isolated, async, in-memory SQLite database.
To execute tests locally from the `/backend` directory:
```bash
.venv/bin/pytest
```

### Frontend Build & Lint checks
To verify the client builds cleanly without compilation warnings:
```bash
npm run build
```
And to perform type checks:
```bash
npm run lint
```
