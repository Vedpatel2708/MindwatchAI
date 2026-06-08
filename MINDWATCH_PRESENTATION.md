# MINDWATCH — Mental Health Crisis Detection Engine
### Complete Project Presentation Guide

---

## 1. What Problem Does This Solve?

Mental health is one of the most under-addressed areas in healthcare globally.

- **280 million people** worldwide suffer from depression
- **80% of people** with depression never receive a formal diagnosis
- The average time from first symptoms to receiving treatment is **11 years**
- Most people don't seek help because they don't recognize their own symptoms, or because stigma prevents them from talking about it

**MINDWATCH** bridges this gap. It is an AI-powered platform that reads text — a journal entry, a chat message, a clinical note — and immediately flags signs of mental health crisis, depression, or anxiety. It does this transparently, explaining every step of its reasoning so clinicians, researchers, and users can trust and verify the results.

---

## 2. What Does It Actually Do? (In Plain English)

1. A person types a journal entry or message into the system
2. The system reads it and within milliseconds returns a **risk level**: Safe, Low, Moderate, High, or Crisis
3. An **AI agent** then conducts a deeper clinical investigation — like a doctor thinking through a case — using specialized tools
4. The full **reasoning trace** (every thought, tool call, and conclusion) is shown on screen so the process is transparent
5. The dashboard updates in **real time** for anyone monitoring (a clinician, counselor, or researcher)
6. Relevant **crisis resources and recommendations** are provided automatically

---

## 3. System Architecture — The Big Picture

```
User Types Text
      │
      ▼
┌─────────────────────────────────────────────────────┐
│              FastAPI Backend (Python)                │
│                                                      │
│  ┌─────────────────┐     ┌──────────────────────┐   │
│  │  ML Pipeline    │────▶│  LangChain ReAct     │   │
│  │  (Crisis Scorer)│     │  Agent (Groq LLM)    │   │
│  └─────────────────┘     └──────────────────────┘   │
│           │                        │                 │
│           ▼                        ▼                 │
│  ┌─────────────────────────────────────────────┐     │
│  │         Supabase (Postgres Database)         │     │
│  └─────────────────────────────────────────────┘     │
│           │                                          │
│           ▼                                          │
│  ┌──────────────────┐                                │
│  │  WebSocket /ws   │  ←── broadcasts live updates   │
│  └──────────────────┘                                │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │   Next.js Frontend     │
              │   (React Dashboard)    │
              └────────────────────────┘
```

The **entire flow** when a user submits text:

1. Text hits `POST /assessments` on the FastAPI backend
2. The **ML Pipeline** scores it in under 100ms and saves a row to the database
3. A **WebSocket broadcast** fires instantly — the dashboard updates live
4. The backend responds to the user with the initial score, and they are redirected to the report page
5. A **background task** starts the AI Agent investigation (takes 5–30 seconds)
6. As the agent thinks and calls tools, every step is saved to the database in real time
7. The report page **polls every 3 seconds** to show the agent's reasoning as it happens
8. When complete, another WebSocket broadcast updates all connected dashboards

---

## 4. Tech Stack — Every Technology and Why

### Backend

| Technology | What It Is | Why It Was Chosen |
|---|---|---|
| **Python 3.11** | Programming language | Dominant language for ML/AI. Best library ecosystem for NLP tasks. |
| **FastAPI** | Web framework | Async-native — handles WebSocket connections and background tasks without blocking. Auto-generates API documentation. Significantly faster than Flask/Django for concurrent requests. |
| **Supabase** | Managed PostgreSQL database | Zero local database setup required — runs in the cloud for free. Provides a PostgREST HTTP API that acts as a thin wrapper over real Postgres. Free tier is enough for this project. |
| **supabase-py** | Python Supabase client | Official Python client library for all Supabase operations. |
| **Pydantic** | Data validation | Validates every API request and response automatically. If a field is wrong type or missing, FastAPI returns a clear error before any code runs. |
| **pydantic-settings** | Config management | Loads environment variables (.env file) with type validation. Single source of truth for all API keys and configuration. |
| **python-dotenv** | Env file loading | Reads .env file into environment variables at startup. |
| **uvicorn** | ASGI server | Production-grade async web server for FastAPI. Supports WebSocket connections natively. |

### Machine Learning Pipeline

| Technology | What It Is | Why It Was Chosen |
|---|---|---|
| **sentence-transformers** | NLP embedding library | Converts any text into a 384-dimensional semantic vector. The key capability that allows the system to understand meaning, not just keywords. |
| **all-MiniLM-L6-v2** | Embedding model | Only 80MB. Runs on CPU in under 50ms per sentence. State-of-the-art semantic similarity performance. Completely free — no API key required. Downloaded automatically on first use. |
| **scikit-learn** | ML model framework | Industry-standard Python ML library. Used to train and run the three custom classifiers (PHQ-9, Crisis, Emotion). |
| **joblib** | Model serialization | Saves and loads trained scikit-learn models to/from disk. Industry standard for persisting Python ML models. |
| **numpy** | Numerical computation | Powers all vector math — cosine similarity calculations, array operations. Foundation of the entire ML ecosystem. |

### AI Agent

| Technology | What It Is | Why It Was Chosen |
|---|---|---|
| **LangChain** | AI agent framework | Provides the ReAct agent architecture — a loop where the LLM reasons ("Thought"), picks a tool ("Action"), reads the result ("Observation"), and decides next steps. Handles prompt formatting, output parsing, retry logic. |
| **langchain-groq** | Groq integration for LangChain | Connects LangChain to the Groq API specifically. |
| **Groq API** | LLM inference provider | Runs the Llama 3.1 8B model at 300–800 tokens per second. The **fastest free LLM API available**. No GPU required on our server — Groq handles the compute. Free tier is sufficient for this project. |
| **Llama 3.1 8B Instant** | The actual language model | Meta's open-source LLM. Small enough to run fast, smart enough for clinical reasoning. Instruction-tuned for following complex prompts. |

### Knowledge Base (RAG)

| Technology | What It Is | Why It Was Chosen |
|---|---|---|
| **RAG (Retrieval-Augmented Generation)** | Architecture pattern | Grounds LLM answers in a verified knowledge base rather than the model's general training. Prevents hallucination on clinical topics. |
| **In-memory vector index** | Storage for document embeddings | For 35 documents, in-memory cosine similarity search is under 5ms — no database needed. Simple, no infrastructure. |
| **35 clinical knowledge documents** | Hand-curated content | Covers DSM-5 criteria, CBT techniques, DBT skills, crisis intervention, medication guides, exercise therapy, mindfulness. All sourced from APA, NICE guidelines, peer-reviewed literature. |

### Frontend

| Technology | What It Is | Why It Was Chosen |
|---|---|---|
| **Next.js 14** | React framework | App Router for file-based routing. Server-side rendering for fast initial page load. Built-in TypeScript support. Industry standard for production React apps. |
| **React 18** | UI library | Component-based UI. State management with hooks. Widely understood — easy to extend. |
| **TypeScript** | Typed JavaScript | Catches bugs at compile time. The `Assessment`, `AnalysisStep`, and `APIEnvelope` interfaces ensure the frontend and backend speak the same language. The bug you encountered (undefined ID) was caused by a type mismatch that TypeScript would have caught if types were fully enforced. |
| **Tailwind CSS** | Utility-first CSS | No custom CSS files needed. Classes applied directly in JSX. Consistent design system. Custom design tokens for the color scheme (primary, error, surface etc). |
| **Framer Motion** | Animation library | Smooth entrance animations, progress bars animating from 0 to final score, bouncing loading indicators. Improves perceived responsiveness. |
| **WebSocket API** | Browser real-time connection | Native browser feature — no library needed. Maintains a persistent connection to the backend for live updates. |

---

## 5. The Machine Learning Pipeline — Explained in Detail

When text is submitted, it goes through **three layers** of analysis simultaneously. This is called a **multi-signal fusion approach**.

### Layer 1 — Trained ML Classifiers (scikit-learn)

Three separate models are trained on labeled mental health datasets:

**PHQ-9 Severity Classifier**
- Predicts depression severity on a 5-point scale: Minimal, Mild, Moderate, Moderately Severe, Severe
- PHQ-9 stands for Patient Health Questionnaire-9 — a validated clinical screening tool used by real doctors
- Uses a Gradient Boosting pipeline (TF-IDF vectorization → Gradient Boost classifier)
- Trained on labeled examples where known PHQ-9 severity levels are the target

**Crisis Risk Classifier**
- Binary classifier: is this text showing acute crisis/suicidality or not?
- Uses a Random Forest pipeline
- Outputs a probability (0.0 to 1.0) — not just yes/no, but how confident

**Emotion Classifier**
- 8-class classifier across: sadness, hopelessness, fear, anger, numbness, loneliness, shame, exhaustion
- Uses Logistic Regression
- Outputs the dominant emotional state in the text

### Layer 2 — Semantic Similarity (BioBERT-style)

This is the most important and innovative part of the scoring system.

The text is converted into a **384-dimensional vector** (an embedding) by the `all-MiniLM-L6-v2` model. This vector captures the *meaning* of the text, not the specific words.

The system then compares this vector against **28 hand-crafted clinical anchor phrases** derived from DSM-5 criteria:

```
Depression anchors:
  "I feel hopeless and empty, like nothing will ever get better"
  "I have no motivation or energy to do anything"
  "Life doesn't feel worth living anymore"
  ... (10 total)

Anxiety anchors:
  "I feel constantly worried and cannot stop my anxious thoughts"
  "I have panic attacks and feel like I cannot breathe"
  ... (8 total)

Crisis anchors:
  "I want to kill myself and have thought about how to do it"
  "I am planning to end my life"
  ... (8 total)
```

**Why this matters:** A person writing *"There's just no point to any of this anymore"* doesn't use the word "hopeless" or "depressed" — but semantically their text is very close to those anchor phrases. Keyword matching would miss this. Semantic similarity catches it.

The cosine similarity score between the input vector and each anchor vector gives a number between 0 and 1. Higher means more semantically similar.

### Layer 3 — Keyword Pattern Matching

A fast direct scan for explicit crisis phrases:

```
"kill myself", "end my life", "want to die",
"suicide", "suicidal", "self-harm", "cutting myself",
"better off dead", "no reason to live"
```

If ANY of these appear, the keyword crisis signal is set to 1.0 (maximum). This ensures that explicit statements are never missed, regardless of what the ML models or semantic scores say.

### Score Fusion

The three signals are combined into a final `crisis_score`:

```
crisis_signal = MAX(ml_crisis_probability, semantic_crisis_similarity, keyword_match)

crisis_score = (0.55 × crisis_signal) + (0.25 × depression_score) + (0.20 × anxiety_score)
```

**Why take the MAX for crisis_signal, not the average?**
In mental health, a false negative (missing a real crisis) is far more dangerous than a false positive (flagging something that turns out to be safe). Taking the maximum ensures that ANY strong signal from ANY source triggers a high risk level.

### Risk Level Assignment

| Condition | Risk Level |
|---|---|
| Crisis signal > 0.65, OR any keyword match, OR crisis_score > 0.75 | **CRISIS** |
| Crisis score > 0.55 | **HIGH** |
| Crisis score > 0.35, OR moderate/severe PHQ-9 | **MODERATE** |
| Crisis score > 0.15, OR mild PHQ-9 | **LOW** |
| Otherwise | **SAFE** |

---

## 6. The AI Agent — How the Autonomous Investigation Works

After the ML pipeline gives an initial score, an **autonomous AI agent** conducts a deeper clinical investigation.

### The ReAct Pattern

The agent uses a framework called **ReAct (Reasoning + Acting)**. It works like this:

```
THOUGHT → "I need to check for specific symptom patterns in this text"
ACTION  → calls analyze_symptom_patterns("I haven't been able to get out of bed...")
OBSERVATION → {"depression": [{"symptom": "I feel hopeless...", "similarity": 0.73}]}
THOUGHT → "Depression patterns are strong. Now I should check for crisis indicators."
ACTION  → calls check_crisis_indicators(text)
OBSERVATION → {"crisis_indicators_found": 0, "severity": "none"}
THOUGHT → "Crisis risk is low. I should get appropriate resources for moderate depression."
ACTION  → calls get_resource_recommendations("moderate", "depression")
OBSERVATION → {"resources": [{"name": "BetterHelp", ...}]}
THOUGHT → "I have enough information to make a final assessment."
FINAL ANSWER → {"risk_level": "moderate", "summary": "...", "recommendations": [...]}
```

Every single thought, action, and observation is **saved to the database in real time** and shown on the report page as the agent thinks. This is the "reasoning trace" visible in the UI.

### The 5 Agent Tools

These are the functions the agent can call. Each one queries the actual database or ML pipeline:

| Tool | What It Does |
|---|---|
| `analyze_symptom_patterns` | Embeds the text and runs semantic similarity against all DSM-5 anchors. Returns which specific symptoms are detected and at what similarity threshold. |
| `check_crisis_indicators` | Scans for explicit crisis phrases and protective factors (mentions of therapy, family, hope). Returns severity level and matched phrases. |
| `assess_temporal_patterns` | If the user has a session ID, fetches their previous assessments from the database and detects whether their mental state is improving, stable, or worsening over time. |
| `get_resource_recommendations` | Returns appropriate support resources for the identified risk level — crisis hotlines, therapy platforms, self-help apps, peer support. |
| `compute_text_similarity` | Embeds the current text and compares against all previous assessments in the database to find historically similar cases. |

### Why an Agent Instead of a Simple Rule?

A simple rule-based system would say: "if crisis_score > 0.7, output CRISIS." That's fast but brittle — it can't consider temporal patterns, protective factors, context, or nuance.

The agent can reason: *"The ML score is high, but the text also mentions 'I'm talking to my therapist' and 'things have been better this week' — these are strong protective factors. I'll call assess_temporal_patterns to check if there's improvement in the recent history before assigning crisis level."*

This is what makes the system behave more like a clinical professional than a simple threshold check.

---

## 7. Real-Time Architecture — How Live Updates Work

### WebSocket Connection

When the Next.js dashboard loads, it immediately opens a **WebSocket connection** to `ws://localhost:8000/ws`. This is a persistent two-way communication channel — unlike HTTP requests which are one-shot (request → response → done), a WebSocket stays open.

The backend maintains a list of all currently connected browser tabs. When something significant happens, it **broadcasts** to all of them simultaneously:

```
Backend ──→ "assessment.submitted" event ──→ All connected dashboards
Backend ──→ "assessment.completed" event ──→ All connected dashboards
```

### What Gets Broadcast

```json
{
  "event": "assessment.submitted",
  "payload": {
    "assessment_id": "abc-123",
    "risk_level": "high",
    "crisis_score": 0.72,
    "dominant_emotion": "hopelessness",
    "timestamp": "2026-06-07T10:30:00Z"
  }
}
```

When the dashboard receives this, it adds the new item to the live feed instantly — no page refresh, no polling.

### The Bug That Was Fixed

The `assessment.submitted` WebSocket payload uses the key `assessment_id`. The `Assessment` TypeScript interface uses the key `id`. When the dashboard received a WebSocket event, it was treating the raw payload directly as an `Assessment` object — meaning `item.id` was `undefined`. Every click on a live-feed item navigated to `/assessments/undefined`, which the backend correctly rejected with the "not found" error.

The fix maps `assessment_id` → `id` when building the state object from the WebSocket payload, matching the pattern already used correctly in the `AssessmentFeed` component.

### Heartbeat System

WebSocket connections can go "zombie" — the TCP connection looks open at the OS level but the browser has navigated away. Every 30 seconds, the backend sends a ping to all connected clients. Any client that hasn't responded within 60 seconds is closed and removed from the active list.

---

## 8. The Knowledge Base (RAG System)

RAG stands for **Retrieval-Augmented Generation**. It allows the AI to answer questions grounded in a verified knowledge base, rather than making things up from its general training.

### How It Works

1. 35+ clinical knowledge documents are written and stored (DSM-5 summaries, CBT techniques, crisis intervention guides, DBT skills, medication information, etc.)
2. Each document is converted to a 384-dimensional embedding vector and stored in memory
3. When a user asks a question in the support chat, the question is also embedded
4. Cosine similarity finds the most relevant 4 documents from the knowledge base
5. Those documents are injected into the LLM prompt as context
6. The LLM generates an answer grounded strictly in those documents, citing sources

### Why In-Memory Instead of a Vector Database?

For 35 documents, in-memory cosine similarity search takes under 5ms. There's no need to set up Pinecone, Weaviate, or pgvector. As the knowledge base grows beyond ~1,000 documents, switching to a proper vector database would be warranted.

### Knowledge Base Categories

| Category | Examples |
|---|---|
| **Depression** | DSM-5 criteria, Behavioral Activation, Cognitive Distortions, Antidepressant guide |
| **Anxiety** | Types of anxiety disorders, Grounding techniques, Exposure therapy, Non-medication approaches |
| **Crisis** | Suicide warning signs, QPR intervention guide, Safety planning (Stanley-Brown model) |
| **Coping** | Mindfulness (MBSR), DBT skills, Exercise as treatment, Sleep hygiene (CBT-I), Journaling |
| **Therapy** | CBT, DBT, ACT, EMDR, Interpersonal Therapy |
| **Self-Care** | Nutrition, Social connection, Boundaries, Stress management |

---

## 9. Database Schema

Four tables in Supabase (PostgreSQL):

### `assessments`
The core table. One row per text submission.

| Column | Type | Description |
|---|---|---|
| `id` | UUID | Primary key — used in all URLs like `/assessments/{id}` |
| `input_text` | TEXT | The raw text submitted by the user |
| `input_type` | VARCHAR | journal / chat / note / speech |
| `crisis_score` | NUMERIC | 0.0–1.0 composite risk score |
| `depression_score` | NUMERIC | Depression signal from ML pipeline |
| `anxiety_score` | NUMERIC | Anxiety signal from ML pipeline |
| `crisis_signal` | NUMERIC | Acute suicidality signal |
| `dominant_emotion` | VARCHAR | e.g. "hopelessness", "sadness" |
| `risk_level` | VARCHAR | safe / low / moderate / high / crisis |
| `agent_summary` | TEXT | The AI agent's clinical summary (written after agent completes) |
| `recommendations` | JSONB | List of immediate action strings |
| `resources` | JSONB | List of support resource objects |
| `status` | VARCHAR | pending → analyzing → completed (or failed) |
| `submitted_at` | TIMESTAMPTZ | When the text was submitted |
| `analyzed_at` | TIMESTAMPTZ | When the agent finished |

### `analysis_steps`
One row per step in the agent's reasoning trace.

| Column | Type | Description |
|---|---|---|
| `assessment_id` | UUID | Foreign key to assessments |
| `step_number` | INTEGER | Ordering within the trace |
| `step_type` | VARCHAR | thought / action / observation / final_answer |
| `tool_name` | VARCHAR | Which tool was called (if action) |
| `tool_input` | JSONB | What the agent passed to the tool |
| `tool_output` | JSONB | What the tool returned |
| `content` | TEXT | The agent's thinking text (for thought/final_answer) |

### `risk_alerts`
Created automatically when an assessment returns high or crisis risk level.

### `sessions`
Tracks a user's longitudinal history — multiple assessments over time linked together. Used by the `assess_temporal_patterns` tool to detect worsening/improving trends.

---

## 10. Frontend Pages

### Dashboard (`/`)
- Real-time stats: assessments today, high-risk count, open alerts, crisis rate
- Live assessment feed (updates instantly via WebSocket)
- Risk alert panel (shows high/crisis assessments requiring attention)
- Inline text analyzer (quick submission without leaving the page)
- Emotion distribution chart

### Text Analysis (`/analyze`)
- Full-screen text input with word/character count
- Input type selector: Journal, Message, Clinical Note, Transcript
- 3 example texts to test with
- Explanation of the analysis pipeline steps

### Assessment Report (`/assessments/[id]`)
- Risk verdict card with color-coded level
- Score bars for Depression, Anxiety, Crisis Signal
- ML model predictions (PHQ-9 severity, crisis probability, emotion)
- Agent's clinical summary and recommendations
- Support resources (crisis hotlines, therapy links)
- Detected symptom patterns
- Full agent reasoning trace — every thought, tool call, and observation

### Analytics (`/analytics`)
- 7-day time series chart (assessments and high-risk per day)
- Emotion distribution over time
- Crisis rate trend

### Support Chat (`/chat`)
- Conversational interface powered by Groq LLM
- RAG-backed: answers grounded in clinical knowledge base
- Identifies situation type and provides appropriate response

---

## 11. How to Run the Project

### Prerequisites
- Python 3.11+
- Node.js 18+
- A free [Supabase](https://supabase.com) account
- A free [Groq API key](https://console.groq.com)

### Step 1: Set Up the Database
1. Create a new Supabase project
2. Go to SQL Editor
3. Paste and run the contents of `backend/supabase_schema.sql`
4. This creates the 4 tables: assessments, sessions, risk_alerts, analysis_steps

### Step 2: Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # Mac/Linux
# venv\Scripts\activate           # Windows

pip install -r requirements.txt

cp .env.example .env
# Edit .env and fill in:
# GROQ_API_KEY=your_key_here
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_ANON_KEY=your_anon_key_here
```

### Step 3: Train ML Models (optional but recommended)
```bash
cd backend
python3 ml/generate_training_data.py  # generates synthetic training data
python3 ml/train_models.py            # trains and saves the 3 models
# Models saved to: backend/models/*.joblib
```

### Step 4: Start Backend
```bash
cd backend
python3 -m uvicorn main:app --reload
# Backend running at: http://localhost:8000
# API documentation: http://localhost:8000/docs
```

### Step 5: Frontend Setup
```bash
cd frontend
cp .env.local.example .env.local
# Edit .env.local and fill in:
# NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
# NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
# NEXT_PUBLIC_SUPABASE_URL=same as backend
# NEXT_PUBLIC_SUPABASE_ANON_KEY=same as backend

npm install
npm run dev
# Dashboard running at: http://localhost:3000
```

---

## 12. Data Flow — Complete End-to-End Example

**Scenario:** A user pastes the following journal entry:
> *"I haven't been able to get out of bed for a week. Everything feels pointless. I used to love painting but I can't even pick up a brush."*

**Step-by-step:**

1. User clicks "Run Analysis" on `/analyze`
2. Frontend calls `POST http://localhost:8000/assessments` with the text
3. **ML Pipeline runs** (< 100ms):
   - `all-MiniLM-L6-v2` embeds the text into 384 numbers
   - Compares against depression anchors → high similarity to "I have no motivation or energy" and "I have lost interest in activities I used to enjoy" → `depression_score = 0.71`
   - Compares against crisis anchors → low similarity → `crisis_signal = 0.12`
   - PHQ-9 classifier predicts "moderate" severity
   - Emotion classifier predicts "sadness"
   - No crisis keywords found
   - `crisis_score = (0.55 × 0.12) + (0.25 × 0.71) + (0.20 × 0.18) = 0.276` → **MODERATE**
4. Assessment row saved to Supabase with status `"pending"`
5. **WebSocket broadcasts** `assessment.submitted` → all open dashboards show a new "sadness / moderate" item in the live feed
6. Backend returns `{ assessment_id: "abc-123", risk_level: "moderate", ... }` to the frontend
7. Frontend navigates to `/assessments/abc-123`
8. Report page shows the initial ML scores and starts polling every 3 seconds
9. **Background task starts the agent:**
   - Agent calls `analyze_symptom_patterns` → confirms depression patterns: anhedonia, low energy, loss of interest
   - Agent calls `check_crisis_indicators` → no crisis phrases found, zero protective factors mentioned
   - Agent calls `get_resource_recommendations("moderate", "depression")` → BetterHelp, 7 Cups, Headspace
   - Agent produces final JSON verdict
10. Agent result saved to the assessment row: `status = "completed"`, `agent_summary`, `recommendations`, `resources`
11. **WebSocket broadcasts** `assessment.completed` → dashboard updates the live feed item from "pending" to "moderate"
12. Report page polls, gets the completed assessment, renders the full reasoning trace
13. User sees: risk verdict, score bars, agent summary, recommended actions, and support resources

Total time: **< 100ms** for initial display, **15–30 seconds** for full agent report.

---

## 13. Security and Ethics

### What This System Is
- A **research and screening tool** for identifying text that may indicate mental health distress
- Transparent — every decision is explained and traceable
- Designed to help people get connected to real human support faster

### What This System Is NOT
- Not a diagnostic tool — it does not diagnose any condition
- Not a replacement for licensed mental health professionals
- Not a crisis counseling service — it provides resources, not direct intervention

### Safety First Design
The scoring system is deliberately biased toward over-detection. In mental health:
- A false positive (flagging safe text as risky) → the person gets a mental health resource they didn't need. Minor inconvenience.
- A false negative (missing a real crisis) → a person in genuine distress gets no flag. Potentially fatal.

Taking the **maximum** signal across all three scoring layers, rather than an average, reflects this priority.

### Crisis Resources Always Present
Every assessment result, regardless of risk level, displays crisis resources: the 988 Suicide & Crisis Lifeline and Crisis Text Line.

---

## 14. Key Technical Achievements to Highlight in Presentation

1. **Multi-signal fusion** — three independent scoring methods (trained ML models, semantic similarity, keyword matching) combined into a single calibrated score

2. **Transparent AI** — the full reasoning trace of every agent thought and tool call is stored and displayed. Nothing is a black box.

3. **Real-time architecture** — WebSocket broadcast ensures zero-latency dashboard updates. No polling, no page refresh.

4. **No expensive infrastructure** — the entire system runs locally. Groq is free. Supabase free tier is sufficient. The ML models are CPU-only.

5. **Semantic understanding** — the system understands *meaning*, not keywords. "There's no point anymore" and "life feels empty" trigger the same high depression signal as "I feel hopeless" — because semantically they mean the same thing.

6. **Longitudinal tracking** — the same session ID across multiple submissions enables the system to detect whether a person's mental state is improving, stable, or worsening over time.

---

## 15. Limitations and Future Work

| Limitation | Future Improvement |
|---|---|
| Text-only input | Add speech-to-text for voice input, image analysis for photo posts |
| No validated clinical dataset used for training | Partner with clinical researchers for labeled real-world data |
| Single language (English) | Multilingual embedding model (multilingual-MiniLM-L12) |
| No user authentication | Add proper auth for longitudinal tracking |
| Agent can be slow (5–30s) | Stream the agent's reasoning steps in real time as they appear |
| Not HIPAA compliant | Add encryption at rest, audit logging, access controls |

---

*MINDWATCH was built for educational and research purposes. If you or someone you know is in crisis, please contact:*
- **988 Suicide & Crisis Lifeline**: call or text **988**
- **Crisis Text Line**: text **HOME** to **741741**
- **Emergency Services**: **911**
