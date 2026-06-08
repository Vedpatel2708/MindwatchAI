# Implementation Plan: Agentic Fraud Detection System

## Overview

Sequential implementation of a full-stack agentic AI fraud detection platform. Tasks are ordered so each file builds on the previous, with no orphaned code. Every code file must include complete inline comments: file-level docstring, function/class docstrings, import-level comments explaining why each import is used, and inline comments on all non-obvious logic blocks (Requirements 10.1–10.4).

## Tasks

---

### Phase 1: Project Scaffolding

- [x] 1. Create top-level folder structure
  - Create the following empty directories: `backend/`, `backend/ml/`, `backend/agent/`, `backend/routers/`, `backend/models/`, `frontend/`, `scripts/`, `data/`, `tests/`, `tests/ml/`, `tests/agent/`, `tests/routers/`, `frontend/__tests__/`, `frontend/app/`, `frontend/app/alerts/[id]/`, `frontend/app/analytics/`, `frontend/components/`, `frontend/lib/`
  - Add a `.gitkeep` in each empty leaf directory so git tracks them
  - _Requirements: 9.1_

- [x] 2. Create `backend/requirements.txt`
  - Pin all Python dependencies with exact versions: `fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings`, `supabase`, `langchain`, `langchain-groq`, `langchain-community`, `sentence-transformers`, `scikit-learn`, `xgboost`, `imbalanced-learn`, `shap`, `joblib`, `pandas`, `numpy`, `hypothesis`, `pytest`, `pytest-asyncio`, `httpx`
  - Include file-level comment explaining the purpose of this file and pinning rationale
  - _Requirements: 9.2_

- [x] 3. Create `backend/.env.example`
  - List all required environment variables: `GROQ_API_KEY`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `FRAUD_THRESHOLD`, `MODEL_PATH`
  - Every variable must have an inline comment explaining what it is, where to obtain it, and its expected format
  - _Requirements: 9.4_

- [x] 4. Create `frontend/package.json`
  - Pin all JS/TS dependencies with exact versions: `next`, `react`, `react-dom`, `typescript`, `tailwindcss`, `@types/react`, `@types/node`, `recharts`, `@supabase/supabase-js`, `fast-check`, `jest`, `@testing-library/react`, `@testing-library/jest-dom`
  - Include standard Next.js scripts (`dev`, `build`, `start`, `test`)
  - _Requirements: 9.3_

- [x] 5. Create `frontend/.env.local.example`
  - List `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_WS_URL`
  - Every variable must have an inline comment explaining its purpose and source
  - _Requirements: 9.4_


---

### Phase 2: Database Setup

- [x] 6. Create `backend/supabase_schema.sql`
  - Implement the full SQL schema: `transactions`, `alerts`, `reports`, `investigation_steps` tables with all columns, types, defaults, and constraints exactly as specified in the design
  - Include all 13 indexes specified in the design for `transactions`, `alerts`, `reports`, and `investigation_steps`
  - Include section-header SQL comments before each table block explaining purpose and audit rationale
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [x] 7. Create `backend/database.py`
  - File-level docstring: purpose, architecture role, design decision (Supabase singleton pattern)
  - Import comments: explain `supabase-py` client and `settings` import
  - Implement a module-level singleton `supabase` client using `SUPABASE_URL` and `SUPABASE_ANON_KEY` from config
  - Implement `check_db_connection()` that raises a descriptive error and exits non-zero if the DB is unreachable
  - Inline comments on every non-obvious line (why singleton, why not per-request client)
  - _Requirements: 8.5, 8.6_


---

### Phase 3: ML Pipeline

- [x] 8. Create `data/fraud_dataset.csv`
  - Generate a CSV with 1,000+ rows of synthetic fraud data with columns: `transaction_id`, `amount`, `currency`, `merchant_name`, `merchant_category`, `card_last_four`, `cardholder_name`, `latitude`, `longitude`, `description`, `hour_of_day`, `day_of_week`, `days_since_last_txn`, `txn_velocity_1h`, `txn_velocity_24h`, `geo_distance_km`, `amount_vs_merchant_mean`, `is_international`, `card_present`, `is_fraud`
  - Fraud rate must be approximately 5% (~50 fraud rows out of 1,000)
  - Include realistic distributions for amounts (gamma), merchant categories, and geographic coordinates
  - _Requirements: 11.5_

- [x] 9. Create `backend/config.py`
  - File-level docstring: purpose, role in architecture, key decisions (Pydantic BaseSettings, env loading)
  - Import comments for `pydantic_settings`, `os`, `pathlib`
  - Implement `Settings(BaseSettings)` with fields: `GROQ_API_KEY: str`, `SUPABASE_URL: str`, `SUPABASE_ANON_KEY: str`, `FRAUD_THRESHOLD: float = 0.70`, `MODEL_PATH: str = "models/fraud_model.joblib"`
  - Instantiate module-level `settings = Settings()` singleton
  - Inline comments on every field explaining validation and default rationale
  - _Requirements: 2.3_

- [x] 10. Create `backend/ml/embeddings.py`
  - File-level docstring: purpose (semantic similarity for agent tool), architecture role, why `all-MiniLM-L6-v2`
  - Import comments for `sentence_transformers`, `numpy`
  - Implement `EmbeddingsService` class with lazy-loaded model singleton
  - Implement `get_embedding(text: str) -> list[float]` returning a 384-dim vector
  - Implement `cosine_similarity(a: list[float], b: list[float]) -> float`
  - Docstrings on every method: parameters, return type, side effects, latency expectations
  - Inline comments on the lazy-loading pattern and why CPU inference is sufficient
  - _Requirements: 4.3, 12.9_

- [x] 11. Create `backend/ml/train.py`
  - File-level docstring: purpose, architecture role, design decisions (SMOTE, three-model comparison, SHAP)
  - Import comments for every import: `pandas`, `sklearn`, `xgboost`, `imblearn`, `shap`, `joblib`, `json`
  - Implement `load_dataset(path: str) -> pd.DataFrame` with descriptive error on missing/malformed file
  - Implement `engineer_features(df) -> tuple[pd.DataFrame, pd.Series]` building all numeric + categorical features listed in the design
  - Implement `build_preprocessor(numeric_cols, categorical_cols) -> ColumnTransformer`
  - Implement `train_models(X_train, y_train, preprocessor) -> dict` training all three models (LogisticRegression, RandomForestClassifier, XGBClassifier) with SMOTE (fallback: class weights)
  - Implement `evaluate_models(models, X_test, y_test, threshold) -> dict` computing precision, recall, F1, AUC-ROC and inference time per model
  - Implement `select_best_model(evaluation_results) -> str` selecting by highest F1
  - Implement `save_model(model, path: str)` using `joblib.dump`
  - Implement `write_training_log(metrics: dict, path: str)` writing structured JSON log
  - Implement `main()` orchestrating the full pipeline
  - Inline comments on SMOTE fallback logic, train/test split rationale, SHAP computation
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

- [x] 12. Create `backend/ml/inference.py`
  - File-level docstring: purpose (real-time scoring), architecture role, design decisions (singleton load, SHAP top-3)
  - Import comments for `joblib`, `numpy`, `shap`, `dataclasses`
  - Define `ScoringResult` dataclass with fields: `fraud_score: float`, `top_features: list[dict]`, `model_name: str`
  - Implement `ModelRegistry` class holding the loaded pipeline and SHAP explainer as module-level singletons (never reloaded after startup)
  - Implement `load_model(path: str) -> None` called once at FastAPI startup
  - Implement `score_transaction(features: dict) -> ScoringResult` returning fraud_score in [0.0, 1.0], top-3 SHAP feature contributions, and model name within 200ms
  - Implement `_extract_top_features(shap_values, feature_names, top_k=3) -> list[dict]`
  - Inline comments on: why singleton, how SHAP tree explainer is initialized, why top-3 only
  - _Requirements: 2.1, 2.2, 2.4_


---

### Phase 4: Backend Core

- [x] 13. Create `backend/models/db_models.py`
  - File-level docstring: purpose (TypedDict DB row definitions), architecture role, why TypedDict over ORM
  - Import comments for `typing`, `datetime`, `uuid`
  - Define `TransactionRow`, `AlertRow`, `ReportRow`, `InvestigationStepRow` as `TypedDict` classes matching every column in the Supabase schema
  - Inline comments on every field explaining the column's purpose and its source (input vs ML output vs agent output)
  - _Requirements: 8.1, 8.2, 8.3_

- [x] 14. Create `backend/models/schemas.py`
  - File-level docstring: purpose (Pydantic request/response schemas), architecture role, design decisions (APIEnvelope generic wrapper)
  - Import comments for `pydantic`, `typing`, `datetime`
  - Implement all schemas exactly as specified in the design: `ErrorDetail`, `APIEnvelope[T]`, `FeatureContribution`, `ScoringResult`, `TransactionRequest`, `TransactionResponse`, `AlertSummary`, `ReportSummary`, `AlertResponse`, `ReportResponse`, `InvestigationStep`, `PaginatedList[T]`, `AnalyticsSummary`
  - Docstrings on every class and field explaining purpose, valid ranges, and constraints
  - _Requirements: 5.2, 5.3_

- [x] 15. Create `backend/websocket_manager.py`
  - File-level docstring: purpose (connection management + broadcast), architecture role, design decisions (heartbeat, stale cleanup)
  - Import comments for `fastapi`, `asyncio`, `json`, `logging`
  - Implement `WebSocketManager` class with:
    - `connect(websocket)` — registers connection
    - `disconnect(websocket)` — removes connection safely
    - `broadcast(event_type: str, payload: dict)` — sends typed event JSON to all active connections, catching `WebSocketDisconnect` silently
    - `send_heartbeat()` — background task pinging all connections every 30s and closing non-responsive ones after 60s
  - Inline comments on: why `asyncio.gather` for broadcast, stale-connection detection logic, why heartbeat interval is 30s
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [x] 16. Create `backend/main.py`
  - File-level docstring: purpose (FastAPI entry point), architecture role, key decisions (startup hooks, CORS, router mounting)
  - Import comments for every import: `fastapi`, `uvicorn`, `cors`, `database`, all routers, `websocket_manager`, `inference`
  - Create `FastAPI` app instance with title, description, version
  - Configure `CORSMiddleware` allowing the dashboard origin
  - Mount all routers with correct prefixes (`/transactions`, `/alerts`, `/reports`, `/analytics`, `/ws`)
  - Implement `@app.on_event("startup")` calling `check_db_connection()` and `load_model(settings.MODEL_PATH)`
  - Implement `/ws` WebSocket endpoint wiring to `WebSocketManager`
  - Inline comments on startup sequence rationale and CORS configuration
  - _Requirements: 5.4, 5.5, 8.6_


---

### Phase 5: Backend Routers

- [x] 17. Create `backend/routers/transactions.py`
  - File-level docstring: purpose, architecture role, pipeline overview (submit → score → alert → agent)
  - Import comments for every import
  - Implement `POST /transactions`: validate `TransactionRequest`, call `score_transaction()`, insert `transactions` row, conditionally insert `alerts` row if `fraud_score > FRAUD_THRESHOLD`, emit `transaction.scored` and optionally `alert.created` WebSocket events, dispatch `run_investigation()` as `BackgroundTask`, return `APIEnvelope[TransactionResponse]`
  - Implement `GET /transactions`: pagination (`page`, `page_size` max 100), filtering by `from_date`, `to_date`, `is_fraud`; return `APIEnvelope[PaginatedList[TransactionResponse]]`
  - Implement `GET /transactions/{id}`: return single transaction with nested alert + report; return 404 envelope if not found
  - Inline comments on: background task dispatch rationale, pagination query construction, alert threshold comparison
  - _Requirements: 2.1, 2.2, 2.3, 2.5, 5.1, 6.2, 6.3_

- [x] 18. Create `backend/routers/alerts.py`
  - File-level docstring: purpose, architecture role
  - Import comments for every import
  - Implement `GET /alerts`: pagination + `status` filter (open | investigating | resolved | escalated), sort by `fraud_score DESC`, return `APIEnvelope[PaginatedList[AlertResponse]]`
  - Implement `GET /alerts/{id}`: return alert with nested full `ReportResponse` including `reasoning_trace`; return 404 envelope if not found
  - Inline comments on join/fetch logic for attaching report to alert response
  - _Requirements: 5.1, 5.3_

- [x] 19. Create `backend/routers/reports.py`
  - File-level docstring: purpose, architecture role
  - Import comments for every import
  - Implement `GET /reports/{id}`: fetch report row + all `investigation_steps` ordered by `step_number`, assemble `ReportResponse`; return 404 envelope if not found
  - Inline comments on ordering of steps and assembly into `reasoning_trace`
  - _Requirements: 5.1, 8.3_

- [x] 20. Create `backend/routers/analytics.py`
  - File-level docstring: purpose, architecture role
  - Import comments for every import
  - Implement `GET /analytics/summary`: compute `total_transactions_today`, `fraud_rate_today`, `total_alerts_open`, `alert_resolution_rate`, `model_accuracy` (from training log), `top_fraud_signal_categories` (top 5 merchant categories by fraud count), `daily_series` (last 7 days of transaction + alert counts)
  - Return `APIEnvelope[AnalyticsSummary]`
  - Inline comments on each aggregation query, why 7-day window, how model_accuracy is sourced from training log
  - _Requirements: 5.1, 7.4_


---

### Phase 6: Agent

- [x] 21. Create `backend/agent/prompts.py`
  - File-level docstring: purpose (prompt templates), architecture role, design decisions (ReAct persona, structured JSON output format)
  - Import comment for string/template usage
  - Define `SYSTEM_PROMPT`: investigation persona, available tools overview, output format instructions (JSON report with `verdict`, `confidence`, `explanation`, `recommended_actions`, `clarifying_questions`)
  - Define `INVESTIGATION_PROMPT_TEMPLATE`: per-alert context injection (transaction ID, fraud score, amount, merchant)
  - Inline comments explaining each section of the prompt and why the output format is structured as JSON
  - _Requirements: 3.2, 3.4, 3.8_

- [x] 22. Create `backend/agent/tools.py`
  - File-level docstring: purpose (5 LangChain tools), architecture role, why tool-use grounds reasoning in real data
  - Import comments for `langchain`, `pydantic`, `database`, `embeddings`
  - Implement all 5 tool input schemas as `BaseModel` subclasses: `GetTransactionDetailsInput`, `GetHistoricalTransactionsInput`, `ComputeSimilarityScoreInput`, `GetFraudStatisticsInput`, `FlagForHumanReviewInput`
  - Implement all 5 tool functions with the exact signatures from the design document
  - Wrap each function as a `Tool(name=..., func=..., description=..., args_schema=...)` LangChain object
  - Export `ALL_TOOLS: list[Tool]`
  - Inline comments on: why each tool exists, what DB table/query it hits, why embedding cosine similarity is used for tool 3
  - _Requirements: 4.1, 4.3, 4.5_

- [x] 23. Create `backend/agent/agent.py`
  - File-level docstring: purpose (LangChain ReAct agent), architecture role, design decisions (AgentExecutor, callback handler, retry logic)
  - Import comments for `langchain`, `langchain_groq`, `tools`, `prompts`, `database`, `config`
  - Implement `InvestigationCallbackHandler(BaseCallbackHandler)` with `on_agent_action`, `on_tool_end`, `on_tool_error`, and `on_agent_finish` methods that write each step to `investigation_steps` and update the `reports` row in real time
  - Implement `build_agent() -> AgentExecutor` creating the Groq LLM, binding all 5 tools, and attaching the callback handler
  - Implement `run_investigation(alert_id: str) -> None`:
    - Create a pending `reports` row in DB
    - Invoke the agent with alert context from `INVESTIGATION_PROMPT_TEMPLATE`
    - On `Final Answer`: parse the structured report JSON, update the `reports` row to `completed`
    - On Groq 5xx: retry up to 3x with exponential backoff (1s, 2s, 4s); on exhaustion set `status = 'failed'` and store `error_message`
    - Emit `report.completed` WebSocket event on success
  - Inline comments on: retry logic, callback handler step interception, JSON parsing, error state persistence
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.7, 4.2, 4.4, 6.4_


---

### Phase 7: Frontend Setup

- [x] 24. Create `frontend/lib/supabase.ts`
  - File-level docstring: purpose (Supabase JS client for frontend), architecture role, design decision (public anon key, direct Realtime subscriptions)
  - Import comments for `@supabase/supabase-js`
  - Implement `createClient` call using `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`
  - Export as named `supabase`
  - Inline comments on why the public anon key is safe for browser use and what RLS provides
  - _Requirements: 8.5_

- [x] 25. Create `frontend/lib/api.ts`
  - File-level docstring: purpose (type-safe REST client), architecture role, design decisions (fetch wrapper, APIEnvelope types)
  - Import comments for fetch, environment variables, TypeScript interfaces
  - Define TypeScript interfaces matching all API response shapes: `Transaction`, `Alert`, `Report`, `InvestigationStep`, `AnalyticsSummary`, `APIEnvelope<T>`, `PaginatedList<T>`
  - Implement typed async functions for all 7 endpoints: `fetchTransactions(params)`, `fetchTransaction(id)`, `submitTransaction(body)`, `fetchAlerts(params)`, `fetchAlert(id)`, `fetchReport(id)`, `fetchAnalyticsSummary()`
  - Inline comments on error handling, how `APIEnvelope` is unwrapped, and base URL sourcing
  - _Requirements: 5.1, 5.3_

- [ ] 26. Create `frontend/components/WebSocketProvider.tsx`
  - File-level docstring: purpose (WS connection + React context), architecture role, design decisions (exponential backoff, context API)
  - Import comments for `react`, `WebSocket`
  - Implement `WebSocketContext` with `subscribe`, `isConnected`, `isReconnecting`
  - Implement `WebSocketProvider` component with exponential backoff reconnection: initial delay 1s, doubles each failure, max 30s cap
  - Implement `useWebSocket()` custom hook
  - Inline comments on: backoff formula `min(delay * 2^k, 30000)`, event subscription map pattern, cleanup on unmount
  - _Requirements: 6.1, 7.8_

- [x] 27. Create `frontend/app/layout.tsx`
  - File-level docstring: purpose (root Next.js layout), architecture role
  - Import comments for `WebSocketProvider`, Tailwind global CSS
  - Wrap `{children}` in `WebSocketProvider`
  - Include `<html>`, `<body>` tags with Tailwind base classes
  - Inline comments on why layout wraps all pages with the WS provider
  - _Requirements: 7.1, 7.2_


---

### Phase 8: Frontend Components

- [x] 28. Create `frontend/components/TransactionFeed.tsx`
  - File-level docstring: purpose (live transaction list), architecture role, design decisions (capped at 50, WebSocket subscription)
  - Import comments for `react`, `useWebSocket`, `Transaction` type
  - Use `useState<Transaction[]>` initialized empty; on `transaction.scored` WS event prepend new transaction and `slice(0, 50)`
  - Render a scrollable list of transaction rows showing: amount, merchant name, fraud score badge (color-coded: green below 0.4, yellow 0.4-0.7, red above 0.7), timestamp
  - Inline comments on the `slice(0, 50)` cap rationale and badge color thresholds
  - _Requirements: 7.1_

- [ ] 29. Create `frontend/components/AlertPanel.tsx`
  - File-level docstring: purpose (alerts sidebar), architecture role, design decisions (sorted by fraud_score desc, severity colors)
  - Import comments for `react`, `useWebSocket`, `Alert` type, `Link`
  - Use `useState<Alert[]>` initialized from initial fetch; on `alert.created` WS event insert and re-sort by `fraud_score` descending
  - Render alert cards with severity color indicator (red >= 0.9, orange 0.7-0.9, yellow below), merchant name, score, and link to alert detail page
  - Inline comments on sort logic and color mapping
  - _Requirements: 7.2_

- [x] 30. Create `frontend/components/ReasoningTrace.tsx`
  - File-level docstring: purpose (agent reasoning timeline), architecture role, design decision (collapsible cards)
  - Import comments for `react`, `InvestigationStep` type
  - Accept `steps: InvestigationStep[]` and `clarifyingQuestions?: string[]` as props
  - Render each step as a collapsible card showing: step type badge (thought/action/observation/final_answer), tool name if action, tool input + output collapsed by default, content text
  - If `clarifyingQuestions` is non-empty, render each question with a labeled `<textarea>` input
  - Inline comments on collapsible toggle logic and why each step type gets a distinct visual treatment
  - _Requirements: 7.3, 7.5, 7.9_

- [x] 31. Create `frontend/components/AnalyticsChart.tsx`
  - File-level docstring: purpose (Recharts time-series), architecture role, design decision (LineChart over bar for trend visibility)
  - Import comments for `react`, `recharts`, `AnalyticsSummary` type
  - Accept `dailySeries: Array<{date: string, transactions: number, alerts: number}>` as prop
  - Render `LineChart` with two lines: transaction volume (blue) and fraud alerts (red), with `XAxis`, `YAxis`, `Tooltip`, `Legend`, wrapped in `ResponsiveContainer`
  - Inline comments on `ResponsiveContainer` usage and why two lines instead of stacked bar
  - _Requirements: 7.4_


---

### Phase 9: Frontend Pages

- [x] 32. Create `frontend/app/page.tsx` (Dashboard)
  - File-level docstring: purpose (main dashboard), architecture role, component composition
  - Import comments for `TransactionFeed`, `AlertPanel`, `AnalyticsChart`, `fetchAnalyticsSummary`
  - Implement as a Client Component (`"use client"`)
  - Fetch `analyticsSummary` on mount; refresh every 5 minutes via `setInterval`
  - Render responsive grid: left column `TransactionFeed`, center/right `AlertPanel`, bottom `AnalyticsChart` with stat cards for `total_transactions_today`, `fraud_rate_today`, `total_alerts_open`
  - Show reconnecting banner when `isReconnecting === true`
  - Inline comments on grid layout breakpoints and reconnection banner visibility logic
  - _Requirements: 7.1, 7.2, 7.4, 7.6, 7.7, 7.8_

- [x] 33. Create `frontend/app/alerts/[id]/page.tsx` (Alert Detail)
  - File-level docstring: purpose (alert detail + reasoning trace), architecture role
  - Import comments for `fetchAlert`, `ReasoningTrace`, `react`
  - Implement as Server Component: fetch alert + report by `id` param
  - If report `status === 'pending'`, poll `GET /reports/{id}` every 3s via client-side sub-component until completed
  - Render: transaction summary card, verdict badge, confidence label, explanation text, `ReasoningTrace` component, clarifying questions section
  - Inline comments on polling logic and pending state skeleton display
  - _Requirements: 7.3, 7.5, 7.9_

- [x] 34. Create `frontend/app/analytics/page.tsx` (Analytics)
  - File-level docstring: purpose (dedicated analytics page), architecture role
  - Import comments for `fetchAnalyticsSummary`, `AnalyticsChart`
  - Implement as Server Component fetching summary data at render time
  - Render `AnalyticsChart` with full `daily_series`, plus stat summary cards and `top_fraud_signal_categories` list
  - Inline comments on data fetching pattern (server component vs client) and why server-side fetch is preferred here
  - _Requirements: 7.4_


---

### Phase 10: Simulation Script

- [x] 35. Create `scripts/simulate_transactions.py`
  - File-level docstring: purpose (synthetic transaction generator + API submitter), architecture role, design decisions
  - Import comments for `argparse`, `random`, `time`, `requests`, `uuid`, `json`
  - Implement `generate_transaction(is_fraud: bool) -> dict` producing a realistic `TransactionRequest`-compatible dict with: gamma-distributed amount (fraud skewed high), random merchant from a realistic list, random geographic coordinates, card last four
  - Implement `main()` with `argparse` CLI: `--count` (default 100), `--fraud-rate` (default 0.05), `--rate` (transactions per second, default 1.0), `--api-url` (default `http://localhost:8000`)
  - Submit each transaction via `POST /transactions` and print progress
  - Print a summary line after all submissions: total submitted, fraud count, elapsed time
  - Inline comments on: how fraud rate is applied via `random.random() < fraud_rate`, rate limiting with `time.sleep`
  - _Requirements: 11.1, 11.2, 11.3, 11.4_

---

### Phase 11: Tests

- [x] 36. Create `tests/ml/test_train_properties.py`
  - File-level docstring and import comments
  - Implement property test for **Property 1** (all 3 model types produced): generate a small synthetic dataset, run `train_models`, assert all three keys (`logistic_regression`, `random_forest`, `xgboost`) are present in the result dict
  - Implement property test for **Property 2** (serialization round-trip): train a model, serialize to temp file, load it back, assert predictions match exactly for the same inputs
  - Tag each test: `# Feature: agentic-fraud-detection, Property {N}: {property_text}`
  - Use `@settings(max_examples=100)`
  - _Requirements: 1.1, 1.3, 1.4_

  - [ ]* 36.1 Write unit tests in `tests/ml/test_train.py`
    - Test training log contains all expected keys: `timestamp`, `dataset_path`, `models`, `best_model`, `model_path`
    - Test SMOTE step is present in the preprocessing pipeline
    - Test `load_dataset` raises `FileNotFoundError` for a missing CSV path
    - Test `load_dataset` raises `ValueError` for a malformed (non-parseable) CSV
    - _Requirements: 1.5, 1.6_

- [x] 37. Create `tests/ml/test_inference_properties.py`
  - File-level docstring and import comments
  - Implement property test for **Property 3** (inference output completeness): `@given` a synthetic transaction dict, call `score_transaction()`, assert `0.0 <= fraud_score <= 1.0`, `1 <= len(top_features) <= 3`, `model_name != ""`
  - Tag: `# Feature: agentic-fraud-detection, Property 3: Inference output completeness`
  - Use `@settings(max_examples=100)`
  - _Requirements: 2.2_

  - [ ]* 37.1 Write unit tests in `tests/ml/test_inference.py`
    - Test model is loaded only once at startup: call `load_model` twice, assert the in-memory singleton object identity is unchanged
    - _Requirements: 2.4_

- [x] 38. Create `tests/routers/test_transaction_properties.py`
  - File-level docstring and import comments
  - Implement property test for **Property 4** (alert creation invariant): `@given` a transaction where `fraud_score > FRAUD_THRESHOLD`, POST it to the API, assert a corresponding alert row exists in the DB
  - Tag: `# Feature: agentic-fraud-detection, Property 4: Alert creation invariant`
  - Use `@settings(max_examples=100)`
  - _Requirements: 2.3_

- [x] 39. Create `tests/routers/test_api_properties.py`
  - File-level docstring and import comments
  - Implement property test for **Property 5** (422 on invalid input): `@given` an incomplete transaction dict missing required fields, POST to the API, assert HTTP 422 and offending field name in response body
  - Implement property test for **Property 6** (response envelope contract): `@given` any valid transaction, assert every successful response has `{"data": <non-null>, "error": null}` shape; every error response has `{"data": null, "error": {"code": ..., "message": ...}}`
  - Tag each: `# Feature: agentic-fraud-detection, Property 5: ...` and `Property 6: ...`
  - Use `@settings(max_examples=100)`
  - _Requirements: 5.2, 5.3_

  - [ ]* 39.1 Write unit tests in `tests/routers/test_api.py`
    - Test CORS headers are present in responses for the configured Dashboard origin
    - Test `GET /docs` returns HTTP 200
    - _Requirements: 5.4, 5.5_

- [x] 40. Create `tests/agent/test_agent_properties.py`
  - File-level docstring and import comments
  - Implement property test for **Property 7** (investigation for every alert): `@given` an alert_id, call `run_investigation`, assert a `reports` row exists for that alert_id in the DB
  - Implement property test for **Property 8** (completed report structure): `@given` a completed report, assert `verdict in {'fraudulent','suspicious','legitimate'}`, `confidence in {'high','medium','low'}`, `explanation` non-empty, `reasoning_trace` non-empty list
  - Implement property test for **Property 9** (clarifying questions bounded): `@given` a report with questions, assert `len(clarifying_questions) <= 3`
  - Implement property test for **Property 10** (tool call steps fully logged): `@given` an investigation containing action steps, assert each row with `step_type='action'` has non-null `tool_name`, `tool_input`, `tool_output` OR has `is_error=true` with non-empty `error_detail`
  - Tag each appropriately
  - Use `@settings(max_examples=100)`
  - _Requirements: 3.1, 3.3, 3.4, 3.8, 4.2_

  - [ ]* 40.1 Write unit tests in `tests/agent/test_agent.py`
    - Test agent retries exactly 3x on Groq 5xx before marking report as failed (mock Groq client)
    - Test a tool failure is recorded in `investigation_steps` with `is_error=true` and investigation continues
    - Test `EmbeddingsService.get_embedding` is called during investigation (mock and assert call count)
    - _Requirements: 3.7, 4.3, 4.4_

  - [ ]* 40.2 Write unit tests in `tests/agent/test_tools.py`
    - Test `ALL_TOOLS` has exactly 5 entries
    - Test each tool's `name` and `description` are non-empty strings
    - _Requirements: 4.1_

- [ ] 41. Create `tests/test_websocket_properties.py`
  - File-level docstring and import comments
  - Implement property test for **Property 11** (WS broadcast on events): `@given` an event payload dict, call `broadcast()` with a set of mock WebSocket connections, assert every connection received a message with the correct `event` type and required payload fields
  - Implement property test for **Property 12** (WS client isolation): `@given` n >= 2 connected clients, disconnect one, call `broadcast()`, assert all remaining clients still received the message
  - Tag each appropriately
  - Use `@settings(max_examples=100)`
  - _Requirements: 6.2, 6.3, 6.4, 6.6_

  - [ ]* 41.1 Write unit tests in `tests/test_websocket.py`
    - Test `/ws` endpoint accepts a WebSocket connection (HTTP 101 upgrade)
    - Test heartbeat task sends a ping every 30s (mock asyncio timer)
    - Test stale connection is closed after 60s without a pong response
    - _Requirements: 6.1, 6.5_

- [x] 42. Create `tests/test_database.py`
  - File-level docstring and import comments

  - [ ]* 42.1 Write unit test: Supabase connection failure exits non-zero
    - Mock the Supabase client to raise a connection error on first call; invoke `check_db_connection()`; assert `SystemExit` is raised with a non-zero exit code
    - _Requirements: 8.6_

- [ ] 43. Create `tests/routers/test_analytics.py`
  - File-level docstring and import comments

  - [ ]* 43.1 Write unit test: analytics summary contains all required keys
    - Seed test data; call `GET /analytics/summary`; assert all keys present: `total_transactions_today`, `fraud_rate_today`, `total_alerts_open`, `alert_resolution_rate`, `model_accuracy`, `top_fraud_signal_categories`, `daily_series`
    - _Requirements: 7.4_

- [x] 44. Create `tests/test_simulation_properties.py`
  - File-level docstring and import comments
  - Implement property test for **Property 18** (simulation fraud rate accuracy): `@given` a `fraud_rate` in [0.01, 0.5] and `count >= 100`, generate transactions using `generate_transaction`, assert actual fraud fraction is within +/-0.05 of the target rate
  - Implement property test for **Property 19** (simulation output field completeness): `@given` a boolean `is_fraud`, call `generate_transaction(is_fraud)`, assert all required fields are present and `amount > 0`, `merchant_name != ""`, `card_last_four` is 4 chars, `cardholder_name != ""`
  - Tag each appropriately
  - Use `@settings(max_examples=100)`
  - _Requirements: 11.1, 11.2_

  - [ ]* 44.1 Write unit tests in `tests/test_simulation.py`
    - Test `argparse` correctly parses `--count`, `--fraud-rate`, and `--rate` CLI arguments with correct types and defaults
    - _Requirements: 11.4_

- [x] 45. Create `frontend/__tests__/TransactionFeed.test.ts`
  - File-level docstring and import comments for `fast-check`, `@testing-library/react`
  - Implement property test for **Property 13** (feed capped at 50): `fc.property(fc.array(transactionArb, {minLength: 51, maxLength: 200}), ...)` simulating WS `transaction.scored` events, asserting the rendered list length never exceeds 50
  - Tag: `// Feature: agentic-fraud-detection, Property 13: Transaction feed capped at 50`
  - Use `fc.assert(property, { numRuns: 100 })`
  - _Requirements: 7.1_

- [x] 46. Create `frontend/__tests__/AlertPanel.test.ts`
  - File-level docstring and import comments
  - Implement property test for **Property 14** (alerts sorted descending by fraud_score): `fc.property(fc.array(alertArb, {minLength: 2}), ...)` asserting for all valid i: `alerts[i].fraud_score >= alerts[i+1].fraud_score`
  - Tag: `// Feature: agentic-fraud-detection, Property 14: Alerts sorted descending by fraud_score`
  - Use `fc.assert(property, { numRuns: 100 })`
  - _Requirements: 7.2_

- [x] 47. Create `frontend/__tests__/ReasoningTrace.test.ts`
  - File-level docstring and import comments
  - Implement property test for **Property 15** (trace cards match step count): `fc.property(fc.array(stepArb, {minLength: 1, maxLength: 20}), steps => ...)` rendering `ReasoningTrace`, asserting rendered card count equals `steps.length`
  - Implement property test for **Property 17** (clarifying questions render with inputs): `fc.property(fc.array(fc.string({minLength:1}), {minLength:1, maxLength:3}), questions => ...)` asserting one `<textarea>` or `<input>` per question
  - Tag each: `// Feature: agentic-fraud-detection, Property 15: ...` and `Property 17: ...`
  - Use `fc.assert(property, { numRuns: 100 })`
  - _Requirements: 7.3, 7.5, 7.9_

- [x] 48. Create `frontend/__tests__/WebSocketProvider.test.ts`
  - File-level docstring and import comments
  - Implement property test for **Property 16** (exponential backoff): `fc.property(fc.integer({min:1, max:10}), k => ...)` simulating k consecutive connection failures, asserting the retry delay after failure k equals `Math.min(1000 * Math.pow(2, k-1), 30000)`
  - Tag: `// Feature: agentic-fraud-detection, Property 16: WebSocket reconnection uses exponential backoff`
  - Use `fc.assert(property, { numRuns: 100 })`
  - _Requirements: 7.8_


---

### Phase 12: Documentation

- [ ] 49. Create `README.md`
  - Project overview paragraph describing the three-layer architecture (ML scoring, agentic investigation, live dashboard)
  - Mermaid architecture diagram (matching the design doc)
  - Prerequisites section: Python 3.11+, Node 18+, Groq API key (free at console.groq.com), Supabase project (free at supabase.com)
  - Step-by-step setup instructions: clone -> install Python deps -> install JS deps -> copy env files -> run DB schema SQL in Supabase editor -> train model -> start backend -> start frontend -> run simulation script
  - Environment variable reference table: Variable | Description | Example Value
  - Example API calls section with `curl` commands for `POST /transactions`, `GET /alerts`, `GET /analytics/summary`
  - Tech stack justification table summarizing the Req 12.1-12.12 decisions in one line each
  - _Requirements: 10.5_

- [x] 50. Checkpoint — Ensure all tests pass
  - Run `pytest tests/ -v` and verify all property-based and unit tests pass
  - Run `cd frontend && npx jest --testPathPattern="__tests__"` and verify all frontend property tests pass
  - Fix any failures before closing out
  - Ask the user if any questions arise about test failures

---

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Every code file must include: file-level docstring, per-function/class docstrings, import-level comments, inline logic comments (Requirements 10.1-10.4)
- Property tests use `@settings(max_examples=100)` in Python (Hypothesis) and `{ numRuns: 100 }` in TypeScript (fast-check)
- Each property test must be tagged: `# Feature: agentic-fraud-detection, Property {N}: {property_text}`
- Checkpoints validate incremental correctness before the next phase begins
