# Requirements Document

## Introduction

An agentic AI system for real-time financial fraud detection and autonomous investigation. The system trains multiple ML models on fraud datasets, performs real-time inference on incoming transactions, and uses an LLM-powered agent (via Groq API) to autonomously investigate flagged transactions — explaining decisions, asking clarifying questions, and generating investigation reports. A React/Next.js dashboard provides live transaction monitoring, fraud alerts, agent reasoning traces, and analytics. The entire stack uses free-tier services and open-source libraries.

## Glossary

- **System**: The overall agentic fraud detection application
- **ML_Pipeline**: The machine learning subsystem that trains, evaluates, and serves fraud detection models
- **Agent**: The LLM-powered autonomous investigator that analyzes flagged transactions using Groq API
- **Transaction**: A financial event submitted to the system for fraud evaluation
- **Fraud_Score**: A numeric probability (0.0–1.0) output by the ML_Pipeline indicating likelihood of fraud
- **Alert**: A notification generated when a Transaction's Fraud_Score exceeds the configured threshold
- **Investigation**: An autonomous Agent workflow that gathers evidence, reasons through signals, and produces a Report
- **Report**: A structured document produced by the Agent summarizing fraud investigation findings
- **Reasoning_Trace**: The step-by-step chain-of-thought output produced by the Agent during an Investigation
- **Dashboard**: The React/Next.js frontend that displays Transactions, Alerts, Reasoning_Traces, and analytics
- **API_Server**: The FastAPI backend that exposes REST endpoints and WebSocket connections
- **Embeddings_Service**: A Hugging Face free model used to compute semantic embeddings for transaction descriptions
- **DB**: The Supabase-hosted PostgreSQL database storing Transactions, Alerts, Reports, and model metadata
- **Threshold**: A configurable Fraud_Score cutoff above which a Transaction is flagged and triggers an Alert

---

## Requirements

### Requirement 1: ML Model Training Pipeline

**User Story:** As a data scientist, I want the system to train multiple ML models on a labeled fraud dataset, so that I can compare model performance and select the best one for inference.

#### Acceptance Criteria

1. THE ML_Pipeline SHALL train at minimum three models: Logistic Regression, Gradient Boosting (XGBoost), and a Random Forest classifier using scikit-learn and XGBoost libraries.
2. THE ML_Pipeline SHALL perform feature engineering including scaling of numeric features, encoding of categorical features, and handling of class imbalance using SMOTE or class weights.
3. WHEN training completes, THE ML_Pipeline SHALL evaluate each model using precision, recall, F1-score, and AUC-ROC on a held-out test set.
4. WHEN training completes, THE ML_Pipeline SHALL serialize the best-performing model and its preprocessing pipeline to disk in a format loadable at inference time.
5. THE ML_Pipeline SHALL log all training metrics and model parameters to a structured training log file.
6. IF a training dataset file is missing or malformed, THEN THE ML_Pipeline SHALL raise a descriptive error message identifying the file path and the detected issue.

---

### Requirement 2: Real-Time Fraud Inference

**User Story:** As a fraud analyst, I want submitted transactions to be scored in real time, so that I can act on fraud signals immediately.

#### Acceptance Criteria

1. WHEN a Transaction is submitted to the API_Server, THE ML_Pipeline SHALL return a Fraud_Score within 200ms under normal operating load.
2. WHEN a Transaction is submitted, THE ML_Pipeline SHALL return the Fraud_Score, the top three feature contributions to that score, and the model name used for inference.
3. WHEN a Transaction's Fraud_Score exceeds the configured Threshold, THE API_Server SHALL create an Alert and store it in the DB.
4. THE ML_Pipeline SHALL load the trained model and preprocessing pipeline once at startup and reuse them for all subsequent inference calls without reloading from disk.
5. IF the ML_Pipeline encounters a Transaction with missing required fields, THEN THE API_Server SHALL return an HTTP 422 response with a field-level error description.

---

### Requirement 3: Agentic Investigation Loop

**User Story:** As a fraud analyst, I want an AI agent to autonomously investigate flagged transactions, so that I receive a reasoned explanation and investigation report without manual analysis.

#### Acceptance Criteria

1. WHEN an Alert is created, THE Agent SHALL autonomously begin an Investigation of the associated Transaction.
2. DURING an Investigation, THE Agent SHALL execute a multi-step reasoning loop using the Groq API LLM that includes: retrieving transaction context, querying historical patterns, evaluating fraud signals, and forming a conclusion.
3. THE Agent SHALL produce a Reasoning_Trace documenting each step taken, the tools called, and the intermediate conclusions reached during the Investigation.
4. WHEN an Investigation concludes, THE Agent SHALL produce a Report containing: a fraud verdict (fraudulent / suspicious / legitimate), a confidence level (high / medium / low), a plain-English explanation of the decision, and recommended next actions.
5. THE Agent SHALL complete an Investigation and produce a Report within 30 seconds of Alert creation under normal operating conditions.
6. WHERE historical transaction data is available in the DB, THE Agent SHALL query and reference similar past transactions as evidence in the Investigation.
7. IF the Groq API returns an error or is unavailable, THEN THE Agent SHALL retry up to three times with exponential backoff before marking the Investigation as failed and storing the error in the DB.
8. THE Agent SHALL support a clarifying-question capability: WHEN the Agent determines that additional context would materially change the verdict, THE Agent SHALL generate up to three targeted clarifying questions and store them in the Report for analyst review.

---

### Requirement 4: Agent Tool Use

**User Story:** As a developer, I want the Agent to use structured tools during investigation, so that its reasoning is grounded in real data rather than hallucination.

#### Acceptance Criteria

1. THE Agent SHALL have access to at minimum the following tools: `get_transaction_details`, `get_historical_transactions`, `compute_similarity_score`, `get_fraud_statistics`, and `flag_for_human_review`.
2. WHEN THE Agent calls a tool, THE API_Server SHALL log the tool name, input parameters, and output to the Reasoning_Trace.
3. THE Agent SHALL use the Embeddings_Service to compute semantic similarity between the current Transaction description and historical transactions flagged as fraudulent.
4. IF a tool call fails, THEN THE Agent SHALL record the failure in the Reasoning_Trace and continue the Investigation using available information.
5. THE Agent SHALL not fabricate transaction data; WHEN a tool returns no results, THE Agent SHALL explicitly state the absence of evidence in the Report.

---

### Requirement 5: REST API

**User Story:** As a frontend developer, I want a well-defined REST API, so that the Dashboard can retrieve and display all relevant data.

#### Acceptance Criteria

1. THE API_Server SHALL expose the following REST endpoints:
   - `POST /transactions` — submit a new Transaction for scoring
   - `GET /transactions` — list Transactions with pagination (page, page_size) and filtering by date range and fraud status
   - `GET /transactions/{id}` — retrieve a single Transaction with its Fraud_Score, Alert, and Report
   - `GET /alerts` — list Alerts with pagination and filtering by status
   - `GET /alerts/{id}` — retrieve a single Alert with its associated Investigation Report
   - `GET /reports/{id}` — retrieve a full Investigation Report including Reasoning_Trace
   - `GET /analytics/summary` — return aggregate counts of transactions, fraud rate, model accuracy, and alert resolution rate
2. THE API_Server SHALL validate all request bodies against defined schemas and return HTTP 422 with field-level error details on validation failure.
3. THE API_Server SHALL return all responses in JSON format with consistent envelope structure: `{ "data": ..., "error": null }` on success and `{ "data": null, "error": { "code": ..., "message": ... } }` on failure.
4. THE API_Server SHALL support CORS for the Dashboard origin.
5. THE API_Server SHALL include OpenAPI documentation accessible at `/docs`.

---

### Requirement 6: WebSocket Real-Time Updates

**User Story:** As a fraud analyst, I want the Dashboard to update in real time when new transactions and alerts arrive, so that I don't need to manually refresh.

#### Acceptance Criteria

1. THE API_Server SHALL expose a WebSocket endpoint at `/ws` that clients can subscribe to for real-time events.
2. WHEN a new Transaction is scored, THE API_Server SHALL emit a `transaction.scored` WebSocket event containing the Transaction ID, Fraud_Score, and timestamp.
3. WHEN a new Alert is created, THE API_Server SHALL emit a `alert.created` WebSocket event containing the Alert ID, Transaction ID, and Fraud_Score.
4. WHEN an Investigation Report is completed, THE API_Server SHALL emit a `report.completed` WebSocket event containing the Report ID and Alert ID.
5. THE API_Server SHALL maintain WebSocket connections with a heartbeat ping every 30 seconds and close stale connections that have not responded within 60 seconds.
6. IF a WebSocket client disconnects, THEN THE API_Server SHALL cleanly remove the connection without affecting other connected clients.

---

### Requirement 7: React/Next.js Dashboard

**User Story:** As a fraud analyst, I want a modern dashboard, so that I can monitor transactions, review alerts, and read agent investigation reports in one place.

#### Acceptance Criteria

1. THE Dashboard SHALL display a live transaction feed showing the most recent 50 transactions with their Fraud_Score, amount, timestamp, and fraud status, updating in real time via WebSocket.
2. THE Dashboard SHALL display an alerts panel listing all open Alerts sorted by Fraud_Score descending, with visual severity indicators (color-coded by score range).
3. WHEN an analyst clicks an Alert, THE Dashboard SHALL display the full Investigation Report including the Reasoning_Trace rendered as a collapsible step-by-step timeline.
4. THE Dashboard SHALL display an analytics panel showing: total transactions today, fraud rate percentage, top fraud signal categories, and a time-series chart of transactions vs. fraud alerts over the past 7 days.
5. THE Dashboard SHALL display the Agent's Reasoning_Trace as a structured, human-readable chain-of-thought showing each step, tool calls made, and intermediate conclusions.
6. THE Dashboard SHALL be fully responsive and render correctly on viewport widths from 375px to 1920px.
7. THE Dashboard SHALL use Tailwind CSS for all styling with no paid UI component libraries.
8. WHEN the WebSocket connection is lost, THE Dashboard SHALL display a visible reconnecting indicator and attempt reconnection with exponential backoff.
9. WHERE clarifying questions are present in a Report, THE Dashboard SHALL render them prominently with an option for the analyst to submit answers.

---

### Requirement 8: Data Persistence

**User Story:** As a developer, I want all transactions, alerts, and reports stored persistently, so that historical data is available for analysis and agent context.

Supabase is used as the database platform for this system. Supabase is a free-tier hosted PostgreSQL service that eliminates local database installation and configuration. The free tier includes 500MB storage and 2GB bandwidth — sufficient for development and demonstration. Its built-in REST API (PostgREST) allows direct database queries from the frontend for read-heavy analytics without routing through the FastAPI backend. The visual Table Editor lets developers inspect fraud data, alerts, and reports during development without writing SQL. Supabase Realtime (Postgres logical replication exposed as WebSocket events) can emit DB-level change events, complementing the FastAPI WebSocket for broadcasting scored transactions. Row Level Security (RLS) policies provide production-grade access control without application-layer middleware. The backend uses the `supabase-py` Python client for all DB operations — no SQLAlchemy ORM is needed.

#### Acceptance Criteria

1. THE DB SHALL store all Transactions including raw input fields, Fraud_Score, feature contributions, model name, and inference timestamp.
2. THE DB SHALL store all Alerts including the associated Transaction ID, Threshold at time of creation, creation timestamp, and resolution status.
3. THE DB SHALL store all Reports including full Reasoning_Trace as JSON, verdict, confidence level, explanation text, clarifying questions, and completion timestamp.
4. THE DB SHALL support indexed queries on Transaction timestamp, Fraud_Score, and Alert status to enable pagination response times under 100ms for datasets up to 100,000 records.
5. THE System SHALL use Supabase as the DB, accessed via the `supabase-py` client using the SUPABASE_URL and SUPABASE_ANON_KEY environment variables, with no local database installation required.
6. IF the DB connection fails at startup, THEN THE API_Server SHALL log a descriptive error and exit with a non-zero status code.

---

### Requirement 9: Free Tech Stack Compliance

**User Story:** As a developer, I want the entire system to run on free-tier and open-source tools, so that anyone can clone and run it without cost.

#### Acceptance Criteria

1. THE System SHALL use only the following libraries and services: Groq API (free tier), Hugging Face Inference API or local Hugging Face models (free), scikit-learn, XGBoost, FastAPI, Supabase (free tier — hosted Postgres with REST API, Realtime, and dashboard), React, Next.js, and Tailwind CSS.
2. THE System SHALL include a `requirements.txt` pinning all Python dependency versions.
3. THE System SHALL include a `package.json` pinning all JavaScript dependency versions.
4. THE System SHALL provide a `.env.example` file listing all required environment variables with placeholder values and inline comments explaining each variable, including SUPABASE_URL (the project REST endpoint) and SUPABASE_ANON_KEY (the public anon key for client-side and backend access).
5. IF the Groq API free-tier rate limit is reached, THEN THE Agent SHALL queue pending Investigations and retry after the rate-limit reset window, logging the delay in the DB.

---

### Requirement 10: Code Documentation Quality

**User Story:** As a learner and hiring manager reviewer, I want every code file to contain detailed inline comments, so that the codebase demonstrates deep understanding and serves as a learning resource.

#### Acceptance Criteria

1. THE System SHALL include a file-level docstring at the top of every Python and JavaScript/TypeScript file explaining the file's purpose, its role in the overall architecture, and the key design decisions made.
2. THE System SHALL include a docstring or JSDoc comment on every function and class explaining: what it does, why it exists, its parameters, its return value, and any side effects.
3. THE System SHALL include inline comments on non-obvious logic blocks explaining what the code is doing and why that approach was chosen over alternatives.
4. THE System SHALL include comments on every import statement explaining what the imported module provides and why it is used in this file.
5. THE System SHALL include a root-level `README.md` with: project overview, architecture diagram (ASCII or Mermaid), setup instructions, environment variable reference, and example API calls.

---

### Requirement 11: Transaction Simulation and Demo Data

**User Story:** As a developer evaluating the project, I want a data simulation script, so that I can populate the system with realistic transactions and see the full pipeline in action without real banking data.

#### Acceptance Criteria

1. THE System SHALL include a simulation script that generates synthetic Transaction records with realistic distributions of amounts, merchant categories, geographic locations, and timestamps.
2. THE simulation script SHALL generate both legitimate and fraudulent transactions at a configurable fraud rate (default 5%).
3. WHEN the simulation script is run, THE System SHALL submit generated Transactions to the API_Server via its REST API, triggering the full pipeline including ML inference and Agent investigation.
4. THE simulation script SHALL accept command-line arguments for: number of transactions, fraud rate, and submission rate (transactions per second).
5. THE System SHALL include a pre-seeded demo dataset of at least 1,000 synthetic transactions loadable via a single command for instant demo capability.

---

### Requirement 12: Tech Stack Justification

**User Story:** As a hiring manager or technical interviewer, I want to understand why each technology was chosen, so that I can evaluate whether the engineer made deliberate, well-reasoned architectural decisions rather than defaulting to familiar tools.

#### Acceptance Criteria

1. THE System documentation SHALL justify the use of Gradient Boosting (XGBoost) as the primary production model: XGBoost consistently outperforms Logistic Regression on tabular fraud data because fraud signals are rarely linear — transaction amount, time-of-day, merchant category, and geographic distance interact in complex non-linear ways that tree ensembles capture natively. XGBoost is robust to outliers (high-value transactions don't distort the model), handles missing values internally, and is the industry standard at Stripe, PayPal, and Mastercard. It supports SHAP-based feature importance, enabling explainability required for regulatory compliance. Logistic Regression would require extensive manual feature engineering to approximate the same accuracy.

2. THE System documentation SHALL justify the use of Random Forest as the ensemble comparator: Random Forest provides ensemble diversity through bootstrap aggregation (bagging), where each tree is trained on a random feature subset, reducing variance and overfitting. It provides interpretable feature importance scores via mean decrease in impurity, making it an excellent baseline comparator against XGBoost. Its prediction averaging approach is less prone to overfitting on noisy fraud labels compared to boosting, and it performs well without hyperparameter tuning — making it a strong and honest second model in the comparison.

3. THE System documentation SHALL justify the use of Logistic Regression as the interpretable baseline: Logistic Regression serves as the mandatory baseline that all other models must beat to justify their added complexity. Its coefficients are directly interpretable as log-odds, allowing analysts to understand exactly which features drive the fraud score. It has near-zero inference latency, making it the fallback model if XGBoost is unavailable. Including it in the comparison demonstrates model evaluation discipline — shipping a complex model without proving it beats a simple one is a red flag in production ML systems.

4. THE System documentation SHALL justify the use of SMOTE (Synthetic Minority Oversampling Technique) for class imbalance: In real-world fraud datasets, fraud represents 0.1–5% of all transactions. A naive model that predicts "not fraud" for every transaction achieves 95–99.9% accuracy while being useless. SMOTE generates synthetic minority-class samples by interpolating between existing fraud examples in feature space, giving the model sufficient signal to learn fraud boundaries without simply duplicating existing fraud records (which causes overfitting). Alternatives considered: class weights (simpler, often sufficient, used as a fallback), random undersampling (loses legitimate transaction information), and cost-sensitive learning (requires careful cost matrix calibration). SMOTE is preferred because it preserves information from both classes and is compatible with scikit-learn pipelines.

5. THE System documentation SHALL justify the use of the Groq API for LLM inference: Groq runs on custom LPU (Language Processing Unit) hardware, making it the fastest LLM inference service publicly available — delivering 300–800 tokens per second compared to OpenAI GPT-4's 30–60 tokens/second. This speed is critical for a fraud investigation agent that must complete a multi-step reasoning loop within a 30-second SLA. The free tier allows hundreds of requests per day, making the system fully runnable at zero cost. OpenAI was excluded because its API is paid with no meaningful free tier. Ollama was excluded because it requires a local GPU (8–24GB VRAM) to run capable models, making the project non-reproducible for most developers. Groq requires only an API key, runs state-of-art open models (Llama 3, Mixtral), and is accessible from any machine with internet access.

6. THE System documentation SHALL justify the use of LangChain and a ReAct agent loop over single-prompt LLMs: A single LLM prompt asking "is this transaction fraudulent?" produces a hallucinated answer because the model has no access to real transaction data, historical patterns, or live statistics. The ReAct (Reasoning + Acting) pattern interleaves reasoning steps with tool calls — the agent reasons about what it needs to know, calls a tool to retrieve that data, incorporates the result into its reasoning, and repeats until it has enough evidence to reach a verdict. This grounds the agent's conclusions in real data and produces an auditable Reasoning_Trace that satisfies explainability requirements under PSD2 and GDPR. LangChain provides the structured tool-use scaffolding, tool call logging, and retry logic that would otherwise require hundreds of lines of custom code. The alternative — a custom agent loop — was considered but LangChain's abstractions (Tool, AgentExecutor, memory) accelerate development while remaining fully transparent.

7. THE System documentation SHALL justify the use of FastAPI over Flask or Django: FastAPI is async-native using Python's asyncio, which is architecturally critical for this system — it must handle concurrent WebSocket connections, simultaneous ML inference requests, and background Agent investigations without blocking. Flask is synchronous by default; achieving equivalent concurrency requires Gunicorn worker pools and careful thread management. FastAPI generates OpenAPI documentation automatically from Python type hints with zero additional code, satisfying the `/docs` requirement. Pydantic request validation is built in, providing field-level error messages with no boilerplate. Benchmarks consistently place FastAPI 2–3x faster than Flask on I/O-bound workloads. Django was excluded as architecturally oversized for an API-only backend with no server-side templating needs.

8. THE System documentation SHALL justify the use of Supabase over SQLAlchemy + raw SQLite/PostgreSQL: Supabase eliminates the need for local database installation, schema migration tooling, and connection pool management. The free tier provides a fully managed PostgreSQL instance accessible from any machine with just two environment variables (SUPABASE_URL, SUPABASE_ANON_KEY). The built-in REST API (PostgREST) means the frontend can query the database directly for read-heavy analytics queries without routing through the FastAPI backend. The visual Table Editor lets developers inspect fraud data, alerts, and reports during development without writing SQL. Supabase Realtime (Postgres logical replication exposed as WebSocket events) can emit DB-level change events, complementing the FastAPI WebSocket for broadcasting scored transactions. Row Level Security (RLS) policies provide production-grade access control without application-layer middleware. The alternative — SQLAlchemy + local PostgreSQL — requires Docker or a local Postgres installation, adds ORM complexity, and provides none of the built-in tooling that accelerates development and demonstration.

9. THE System documentation SHALL justify the use of Hugging Face `all-MiniLM-L6-v2` sentence-transformers for semantic embeddings: The Embeddings_Service computes vector representations of transaction descriptions to find semantically similar historical fraud cases — a capability that keyword matching cannot provide ("iPhone purchase" and "electronics retail — mobile device" should have high similarity despite sharing no words). `all-MiniLM-L6-v2` is 80MB, runs on CPU in under 50ms per embedding, achieves state-of-art performance on the SBERT benchmark for semantic similarity tasks, and is completely free to run locally. It requires no API key or internet connection after the initial download. The alternative — using OpenAI's `text-embedding-ada-002` — produces marginally better embeddings but costs $0.0001 per 1K tokens and requires an API key, violating the free-tier constraint.

10. THE System documentation SHALL justify the use of Next.js over plain React: Next.js provides server-side rendering (SSR) and static site generation (SSG) out of the box, meaning the initial page load is fully rendered HTML rather than a blank `<div id="root">`. This improves perceived performance (critical for a live fraud dashboard where analysts need immediate situational awareness) and enables eventual SEO indexing if the dashboard becomes publicly accessible. File-based routing eliminates the need for a router configuration file. The API routes feature allows lightweight BFF (Backend for Frontend) endpoints without a separate server. Plain React was excluded because it produces a client-side-only SPA with worse initial load performance and no SSR path without significant additional configuration (e.g., Vite + React Router).

11. THE System documentation SHALL justify the use of Tailwind CSS over Material UI, Chakra UI, or Bootstrap: Tailwind is a utility-first framework that generates only the CSS classes actually used in production (via PurgeCSS), resulting in stylesheet sizes under 10KB compared to Material UI's 300KB+ bundle. It has zero runtime overhead — unlike CSS-in-JS libraries (Emotion, styled-components) that compute styles at render time. Material UI and Chakra UI are paid for commercial use at scale, violating the free-tier constraint. Bootstrap imposes an opinionated visual style that requires overrides to achieve a custom look. Tailwind provides full design control with consistent spacing, color, and typography scales defined in a single config file.

12. THE System documentation SHALL justify the use of WebSockets over HTTP polling for real-time updates: Fraud detection is a latency-sensitive domain — an alert that arrives 5 seconds late because of a polling interval is 5 seconds in which a fraudulent transaction could be approved. HTTP long-polling requires the client to maintain an open HTTP request continuously, consuming a server thread per connected client; WebSockets use a single persistent connection and emit events as they occur. At 100 concurrent analysts, polling every 2 seconds generates 3,000 HTTP requests per minute; WebSockets generate zero requests during idle periods. Server-Sent Events (SSE) were considered but excluded because they are unidirectional — the Dashboard needs to both receive alerts and send analyst responses to clarifying questions over the same connection.

---

### Requirement 13: Real-World Applications and Industry Impact

**User Story:** As a hiring manager, technical interviewer, or developer evaluating this project, I want to understand how this system maps to real production fraud detection deployments, so that I can assess its practical value and the depth of domain knowledge it demonstrates.

#### Acceptance Criteria

1. THE System documentation SHALL describe the Banking and Fintech deployment context: Visa processes 65,000 transactions per second globally. At that scale, manual fraud review is physically impossible — every decision must be automated. Production systems at Visa, Mastercard, and major banks run ML scoring models with sub-100ms SLA requirements identical to Requirement 2.1 of this system. The difference between this project and a production deployment is horizontal scaling (multiple API_Server instances behind a load balancer), a streaming data pipeline (Kafka instead of REST submission), and a more complex feature store. The core architecture — ML inference → threshold trigger → agent investigation → analyst report — is structurally identical.

2. THE System documentation SHALL describe the E-commerce deployment context: Card-not-present (CNP) fraud — where a stolen card number is used for online purchases without the physical card — costs the global e-commerce industry $32 billion per year. Autonomous fraud investigation agents reduce fraud analyst workload by approximately 80% by auto-resolving high-confidence cases and escalating only ambiguous ones. This project's agentic layer directly models this triage pattern: the Agent produces a verdict with confidence level, and only low-confidence investigations include clarifying questions for analyst review, mirroring how Stripe's risk team triages disputes.

3. THE System documentation SHALL describe the Insurance Claim Fraud deployment context: Property and casualty insurers lose $40 billion per year to fraudulent claims in the US alone. The detection pattern is identical to financial fraud: anomaly scoring on claim characteristics (amount, timing, claimant history, provider patterns) followed by an investigation report for claims adjusters. This system's architecture ports directly to insurance by swapping the transaction feature set for claim features — demonstrating that the agentic investigation pattern is domain-agnostic.

4. THE System documentation SHALL describe the Cryptocurrency Exchange deployment context: Crypto exchanges must detect unusual wallet activity including wash trading, pump-and-dump coordination, and stolen-wallet fund movement. The behavioral signals (transaction velocity, counterparty graph patterns, amount clustering) are analogous to credit card fraud signals. The Embeddings_Service's semantic similarity capability is particularly applicable here — finding wallet addresses with behavioral patterns similar to previously flagged fraud wallets, even when the raw transaction data looks superficially different.

5. THE System documentation SHALL describe the Healthcare Billing Fraud deployment context: Medicare and Medicaid fraud costs the US healthcare system approximately $100 billion per year according to the FBI. Common patterns include upcoding (billing for a more expensive procedure than performed), phantom billing (billing for services never rendered), and provider collusion. The ML scoring model and agentic investigation layer in this system map directly to CMS (Centers for Medicare and Medicaid Services) fraud detection workflows, where a score triggers a structured investigation report consumed by program integrity contractors.

6. THE System documentation SHALL describe how this project maps to real systems at major payment companies:
   - Stripe's risk infrastructure combines a rules engine (deterministic blocks for known fraud patterns) with an ML scoring layer (gradient boosting on transaction features) and an agent-assisted triage system for disputed charges — the three-layer architecture this project implements.
   - PayPal's fraud detection uses Graph Neural Networks to detect fraud rings (coordinated groups of accounts) combined with agent-based triage that generates investigation summaries for human reviewers — the Embeddings_Service's similarity search is a simplified analog of PayPal's graph-based pattern matching.
   - Mastercard's Decision Intelligence product scores every transaction in real time using an ML model that considers global transaction patterns across all Mastercard-network merchants — equivalent to this system's Requirement 2 with a globally distributed feature store replacing the local DB.

7. THE System documentation SHALL describe the explainability and regulatory compliance value of the agentic layer: Human-in-the-loop review of every flagged transaction is not scalable — a bank processing 1 million transactions per day at a 1% fraud rate would require analysts to review 10,000 cases daily. The Agent's Reasoning_Trace solves this by producing an auditable explanation of every decision, enabling analysts to sample-audit agent verdicts rather than review every case. Under the EU's Payment Services Directive 2 (PSD2), payment service providers must be able to explain automated fraud decisions to regulators and consumers. Under GDPR Article 22, automated decisions with significant effects must be explainable. The Reasoning_Trace, feature contributions, and structured Report produced by this system directly satisfy these regulatory explainability requirements, making the agentic approach not just more efficient but legally necessary for EU-market deployment.

8. THE System documentation SHALL describe the scalability path from this demo to production scale: This project runs on a single machine with Supabase and a single FastAPI process. The production scaling path is additive, not architectural: upgrade the Supabase project tier for higher limits, add a Redis cache for feature lookups, front the API_Server with Nginx and run multiple Uvicorn workers, replace direct REST submission with a Kafka consumer for streaming transaction ingestion, and deploy the ML_Pipeline to a dedicated inference server (e.g., Triton Inference Server). The core architecture — the agent loop, tool use pattern, WebSocket event system, and React dashboard — requires no changes at production scale, demonstrating that this project was designed with production concerns in mind from the start.
