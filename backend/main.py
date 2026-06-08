"""
backend/main.py — MINDWATCH
FastAPI entry point. Same structure as fraud detection project — just different routers.
"""

import asyncio
import logging
import sys
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import check_db_connection
from websocket_manager import ws_manager
from routers import assessments, analytics
from routers import rag as rag_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MINDWATCH — Mental Health Crisis Detection Engine",
    description="Multi-modal AI platform for early mental health crisis detection using NLP, semantic analysis, and autonomous agent investigation.",
    version="1.0.0",
    docs_url="/docs",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    logger.info("🧠 Starting MINDWATCH API...")
    check_db_connection()

    # 1. Load the sentence-transformer embedding model eagerly.
    #    This avoids a 3-10s freeze on the FIRST request (lazy loading).
    #    We run it in a thread so the event loop isn't blocked during load.
    try:
        loop = asyncio.get_event_loop()
        from ml.embeddings import embeddings_service

        def _load_embedding_model():
            embeddings_service._load_model()
            logger.info("✅ Embedding model loaded (all-MiniLM-L6-v2)")

        await loop.run_in_executor(None, _load_embedding_model)
    except Exception as e:
        logger.warning(f"Embedding model pre-load failed: {e}")

    # 2. Warm the anchor embedding cache AFTER the model is loaded.
    #    This pre-computes all 26 DSM-5 anchor embeddings so the first
    #    analyze_symptom_patterns tool call is instant, not ~1.3s.
    try:
        from agent.tools import _warm_anchor_cache
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _warm_anchor_cache)
        logger.info("✅ Anchor embedding cache warmed")
    except Exception as e:
        logger.warning(f"Anchor cache warm-up failed: {e}")

    # 3. Load trained ML classifiers (PHQ-9, crisis, emotion).
    #    Optional — falls back to semantic similarity if not trained yet.
    try:
        from ml.crisis_scorer import ml_registry
        ml_registry.load(model_dir="models")
        if ml_registry._loaded:
            logger.info("✅ ML classifiers loaded (PHQ-9 + Crisis + Emotion)")
        else:
            logger.info("ℹ️  ML classifiers not found — using semantic similarity only.")
            logger.info("   To train: python3 ml/generate_training_data.py && python3 ml/train_models.py")
    except Exception as e:
        logger.warning(f"ML model load failed: {e}")

    asyncio.create_task(ws_manager.send_heartbeat())
    logger.info("✅ MINDWATCH API ready. Docs: http://localhost:8000/docs")


app.include_router(assessments.router, prefix="/assessments", tags=["Assessments"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(rag_router.router, prefix="/rag", tags=["Knowledge Base / RAG"])

# Consumer router (chat advisor — reused from fraud project, domain changed)
try:
    from routers import consumer
    app.include_router(consumer.router, prefix="/consumer", tags=["Consumer"])
except Exception:
    pass


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                import json
                msg = json.loads(data)
                if msg.get("event") == "pong":
                    ws_manager.record_pong(websocket)
            except Exception:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "mindwatch-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
