import os
import logging
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# optional .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

import pandas as pd
try:
    import yaml
except Exception:
    yaml = None

from rag_agent import FVIRAG  # your cleaned agent

# ---------------- config helpers ----------------
def _safe_load_yaml(path: str) -> Dict[str, Any]:
    if not yaml:
        return {}
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Config load failed: {e}")
    return {}

def _cfg_get(cfg: Dict[str, Any], *keys, default=None):
    cur = cfg
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur

def _load_scores_df_from_config(cfg: Dict[str, Any]) -> Optional[pd.DataFrame]:
    # Optional. Add later under: data.scores_csv
    path = _cfg_get(cfg, "data", "scores_csv", default=None)
    if not path:
        return None
    if not os.path.exists(path):
        logging.getLogger("fvi-backend").warning(f"scores_csv not found at {path}")
        return None
    try:
        df = pd.read_csv(path)
        if "country" in df.columns:
            df = df.set_index("country")
        return df
    except Exception as e:
        logging.getLogger("fvi-backend").warning(f"Failed to load scores_df: {e}")
        return None

# ---------------- load config & logging ----------------
CONFIG_PATH = os.getenv("CONFIG_PATH", "config.yaml")
CFG = _safe_load_yaml(CONFIG_PATH)

log_level = (_cfg_get(CFG, "logging", "level", default="INFO") or "INFO").upper()
log_fmt   = _cfg_get(CFG, "logging", "format", default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logging.basicConfig(level=getattr(logging, log_level, logging.INFO), format=log_fmt)
logger = logging.getLogger("fvi-backend")

# ---------------- FastAPI init ----------------
app = FastAPI(title="FVI Backend", version=_cfg_get(CFG, "version", default="1.0.0"))

# CORS
if _cfg_get(CFG, "api", "enable_cors", default=True):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # tighten for prod
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# ---------------- models ----------------
class ChatRequest(BaseModel):
    message: str
    persona: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    text: str
    persona: str
    meta: Dict[str, Any] = {}

# ---------------- initialize agent ----------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY is NOT set — RAG will fail.")

# vectorstore_dir: prefer top-level key, fallback to rag.vectorstore_dir, default "vectorstore"
vectorstore_dir = (
    _cfg_get(CFG, "vectorstore_dir")
    or _cfg_get(CFG, "rag", "vectorstore_dir")
    or "vectorstore"
)

model_name = _cfg_get(CFG, "llm", "model_name")  # gpt-4o-mini from your config
retrieval_k = _cfg_get(CFG, "rag", "retrieval_k", default=5)

_scores_df = _load_scores_df_from_config(CFG)

_agent: Optional[FVIRAG] = None
try:
    _agent = FVIRAG(
        scores_df=_scores_df,
        config_path=CONFIG_PATH,
        vectorstore_dir=vectorstore_dir,
        model_name=model_name,
        retrieval_k=retrieval_k,
    )
    logger.info("FVIRAG initialized successfully.")
except Exception as e:
    logger.exception(f"Failed to initialize FVIRAG: {e}")

# ---------------- routes ----------------
@app.get("/healthz")
def healthz():
    return {
        "status": "ok",
        "rag_ready": bool(_agent),
        "has_openai_key": bool(OPENAI_API_KEY),
        "vectorstore_dir": vectorstore_dir,
        "model": model_name or "default",
    }

@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    logger.info(f"/api/chat | persona={req.persona} | msg_len={len(req.message)}")

    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="Server missing OPENAI_API_KEY")

    if _agent is None:
        raise HTTPException(status_code=500, detail="RAG agent not initialized")

    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="Empty message")

    try:
        result = _agent.answer(req.message, persona=req.persona, context=req.context)
        return ChatResponse(text=result["text"], persona=result["persona"], meta={"usage": result.get("usage", {})})
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"RAG error: {e}")
        raise HTTPException(status_code=500, detail=f"RAG error: {e}")

@app.get("/")
def root():
    return {
        "name": "FVI Backend",
        "version": _cfg_get(CFG, "version", default="1.0.0"),
        "last_updated": _cfg_get(CFG, "last_updated", default=None),
    }

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("main:app", host=host, port=port, reload=True)
