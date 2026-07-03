# Walkthrough - Sprint 4: Analytics Dashboard & Data Visualizations

This walkthrough details the design, completed features, APIs, database logic, and testing validations for Sprint 4.

---

## 📈 Sprint 4: Analytics Dashboard

A production-quality Analytics Dashboard has been built to translate user journaling logs and metric indicators into actionable mental health trends.

### 1. Consolidated Analytics Engine (FastAPI)
* **Consolidated API Endpoint:** Developed `GET /api/v1/analytics/dashboard` which returns summary data, streak counts, time-series trends, and tag distribution metrics in a single network request.
* **Dialect-Neutral Queries:** Implemented dynamic query wrappers inside `app/services/analytics.py` that aggregate data using dialect-neutral SQLAlchemy methods, allowing:
  * Unit tests to run seamlessly in-memory on SQLite.
  * Production containers to run successfully on MySQL 8.0.
* **Consolidated reflections:** Appended the user's top three recent AI reflections directly to the dashboard response payload via optimized ORM queries.

### 2. High Fidelity Visual Widgets (React + TypeScript + Recharts)
* **Summary Metrics Deck:** Renders cards for streak counters, total entry counts, average mood indexes, and sleep averages.
* **Trend Area Chart:** Employs Recharts curves with custom tooltips matching the MindSpace dark slate palette. Custom domain scale rules are mapped dynamically:
  * A fixed `[1, 5]` scale for mood, stress, and energy curves.
  * An auto-scaling `[0, 'auto']` scale for sleep duration coordinates.
* **Tag Distribution Donut:** Visualizes top-used tag categories using segmented slices with clear legends.
* **Nav Links:** Mounted direct links to `/analytics` inside all header blocks (`Dashboard.tsx`, `Timeline.tsx`, `JournalEditor.tsx`).

---

## 🛠️ Sprint 3 Manual Testing Bug Investigations & Fixes

*(Previous fix records for the AI Reflection Engine configuration issues, cache invalidation, and crisis safety filters are preserved here).*

---

## 1. Features Completed

### Backend Analytics
* **Schemas:** Created `app/schemas/analytics.py` defining response structures for summaries, trends, and tag counts.
* **Streaks:** Integrated consecutive days logic in python, ensuring that gaps of > 1 day reset the streak counter.
* **Aggregations:** Programmed averages calculators for ratings and sleep.
* **Routes:** Mounted the router inside `app/main.py`.

### Frontend Visualizations
* **Recharts:** Installed the library and created `SummaryCards.tsx`, `TrendLineChart.tsx`, and `TagPieChart.tsx`.
* **Analytics Dashboard Page:** Created `Analytics.tsx` with selectors for day ranges and binning intervals.
* **ProtectedRoute:** Bound the route guard in `App.tsx`.

---

## 2. API Endpoints Reference

| Protocol | Endpoint | Authorization | Status Codes | Description |
|---|---|---|---|---|
| **GET** | `/api/v1/analytics/dashboard` | Bearer Token | 200, 401 | Consolidates streaks, trends, tags, and reflections. |
| **GET** | `/api/v1/analytics/summary` | Bearer Token | 200, 401 | Returns KPI metrics summary. |
| **GET** | `/api/v1/analytics/tag-distribution` | Bearer Token | 200, 401 | Returns tag counts. |
| **GET** | `/api/v1/analytics/mood-trend` | Bearer Token | 200, 401 | Returns mood average list. |

---

## 3. Verification & Testing

### Backend Unit Tests
We executed the async tests inside an in-memory SQLite environment using `pytest`.

```
============================= test session starts ==============================
collected 25 items

app/tests/test_analytics.py .....                                        [ 20%]
app/tests/test_auth.py ........                                          [ 52%]
app/tests/test_journal.py .....                                          [ 72%]
app/tests/test_reflection.py .......                                     [100%]

============================= 25 passed in 11.69s ==============================
```

### Frontend Production Build & Type Checking
* **Type Validation:** `npm run lint` -> Passed.
* **Client compile:** `npm run build` -> Succeeded in 1.77 seconds.
