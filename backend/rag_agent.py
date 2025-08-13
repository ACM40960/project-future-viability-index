# This is fixed version of rag_agent.py 

import os
import logging
from typing import Optional, Dict, Any, List

# logging 
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger("rag-agent")

#  optional deps 
try:
    from openai import OpenAI  # official OpenAI >= 1.x client
except Exception:
    OpenAI = None

try:
    import yaml
except Exception:
    yaml = None

# FVI aggregator is optional but recommended (kept lightweight)
try:
    from fvi_aggregator import FVI_Aggregator
except Exception:
    FVI_Aggregator = None

# FAISS retriever to enrich context if present
try:
    from langchain_community.vectorstores import FAISS
    from langchain_community.embeddings import HuggingFaceEmbeddings
    FAISS_AVAILABLE = True
except Exception:
    FAISS_AVAILABLE = False

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Prompt generation

SYSTEM_PROMPT = """You are the FVI assistant for coal-industry assessment.
Be concise, structured, and data-grounded. Use the provided CONTEXT faithfully.
If something is missing or uncertain, say so explicitly. Tailor tone slightly to the persona.
"""

USER_PROMPT = """Persona: {persona}

User Question:
{question}

CONTEXT (FVI + retrieved docs):
{context}
"""

def _safe_load_yaml(path: str) -> Dict[str, Any]:
    if not yaml:
        return {}
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning(f"Config load failed: {e}")
    return {}

def _truncate(s: str, limit: int = 3000) -> str:
    if s is None:
        return ""
    s = str(s)
    return s if len(s) <= limit else s[:limit] + " ... [truncated]"

class _CompatChain:
    """Compatibility shim to support get_chain().invoke({'question': ...})."""
    def __init__(self, agent: "FVIRAG", persona: Optional[str], extra_context: Optional[Dict[str, Any]]):
        self._agent = agent
        self._persona = persona
        self._extra_context = extra_context

    def invoke(self, inputs: Dict[str, Any]):
        q = inputs.get("question") or inputs.get("query") or ""
        return {"text": self._agent.answer(q, persona=self._persona, context=self._extra_context)["text"]}

class FVIRAG:
    """
    Clean RAG Agent:
    - Always calls OpenAI if OPENAI_API_KEY is set.
    - Optionally enriches with FAISS docs (if vectorstore exists).
    - Optionally augments with FVI_Aggregator persona-weighted summaries (if available & scores provided).
    """
    def __init__(
        self,
        scores_df=None,
        config_path: str = "config.yaml",
        vectorstore_dir: str = None,
        embedding_model: str = "all-MiniLM-L6-v2",
        retrieval_k: int = 4,
        model_name: Optional[str] = None,
    ):
        self.config = _safe_load_yaml(config_path)
        self.model_name = model_name or self.config.get("llm", {}).get("model_name", DEFAULT_MODEL)
        self.retrieval_k = retrieval_k or self.config.get("rag", {}).get("retrieval_k", 4)

        # OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set. RAG cannot run.")
        if OpenAI is None:
            raise RuntimeError("openai Python client not installed. `pip install openai`")
        self.client = OpenAI(api_key=api_key)
        logger.info(f"FVIRAG initialized with model='{self.model_name}'")

        # FVI
        self.scores_df = scores_df
        self.aggregator = FVI_Aggregator(self.config) if (FVI_Aggregator and self.config) else None
        self.current_persona = "analyst"

        # Retriever
        self.retriever = None
        vs_dir = vectorstore_dir or self.config.get("rag", {}).get("vectorstore_dir", "vectorstore")
        if FAISS_AVAILABLE and os.path.isdir(vs_dir) and os.listdir(vs_dir):
            try:
                embeddings = HuggingFaceEmbeddings(model_name=self.config.get("rag", {}).get("embedding_model", embedding_model))
                self.vectorstore = FAISS.load_local(vs_dir, embeddings, allow_dangerous_deserialization=True)
                self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": self.retrieval_k})
                logger.info(f"Retriever ready from '{vs_dir}', k={self.retrieval_k}")
            except Exception as e:
                logger.warning(f"Failed to initialize retriever: {e}")
        else:
            logger.info("No vectorstore found; proceeding without retrieval.")

    #  public API 
    def answer(self, query: str, persona: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not query or not query.strip():
            raise ValueError("Empty query provided.")

        persona = persona or self._detect_persona(query)
        self.current_persona = persona

        ctx = self._build_context(query=query, persona=persona, extra_context=context)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT.format(persona=persona, question=query.strip(), context=_truncate(ctx, 12000))},
        ]

        try:
            logger.info(f"[RAG] calling OpenAI | persona={persona} | qlen={len(query)}")
            resp = self.client.chat.completions.create(model=self.model_name, messages=messages, temperature=0.2)
            text = (resp.choices[0].message.content if resp.choices else "") or ""
            usage = {
                "prompt_tokens": getattr(resp.usage, "prompt_tokens", None),
                "completion_tokens": getattr(resp.usage, "completion_tokens", None),
                "total_tokens": getattr(resp.usage, "total_tokens", None),
            }
            logger.info(f"[RAG] OK | chars={len(text)} | usage={usage}")
            return {"text": text, "persona": persona, "usage": usage}
        except Exception as e:
            logger.exception(f"[RAG] OpenAI call failed: {e}")
            # hard fail so you notice (no silent static text)
            raise

    def get_chain(self, persona: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        return _CompatChain(self, persona=persona, extra_context=context)

    #  helpers
    def _detect_persona(self, query: str) -> str:
        q = query.lower()
        buckets = {
            "investor": ["invest", "roi", "risk", "return", "valuation", "profit", "market"],
            "policy_maker": ["policy", "regulation", "government", "subsidy", "taxonomy", "legislation"],
            "ngo": ["climate", "emission", "pollution, eco", "environment", "sustainab", "carbon"],
            "citizen": ["job", "cost", "bills", "household", "community", "local", "price"],
        }
        score = {k: sum(1 for w in ws if w in q) for k, ws in buckets.items()}
        winner = max(score, key=score.get)
        return winner if score[winner] > 0 else "analyst"

    def _build_context(self, query: str, persona: str, extra_context: Optional[Dict[str, Any]]) -> str:
        parts: List[str] = [f"PERSONA: {persona.upper()}"]

        # FVI augmentation
        if self.aggregator and self.scores_df is not None and len(self.scores_df) > 0:
            try:
                self.aggregator.set_persona(persona)
                fvi_scores = self.aggregator.compute_fvi(self.scores_df)
                top = fvi_scores.nsmallest(5)
                bottom = fvi_scores.nlargest(5)

                parts.append("\nFVI SUMMARY (Lower = more viable):")
                parts.append("Top 5:")
                for c, s in top.items():
                    parts.append(f"  {c}: {s:.1f}")
                parts.append("Bottom 5:")
                for c, s in bottom.items():
                    parts.append(f"  {c}: {s:.1f}")

                # if a country is mentioned, add dimension contributions (up to 2)
                mentioned = [c for c in self.scores_df.index if c.lower() in query.lower()][:2]
                for c in mentioned:
                    try:
                        contrib = self.aggregator.get_dimension_contribution(self.scores_df, c)
                        parts.append(f"\n{c} contributions:")
                        if contrib:
                            for k, v in contrib.items():
                                if k == "_summary": 
                                    continue
                                parts.append(f"  {k}: raw={v.get('raw_score'):.2f}, weight={v.get('weight'):.2%}")
                    except Exception:
                        pass
            except Exception as e:
                logger.warning(f"FVI augmentation failed: {e}")
        else:
            parts.append("\nNo FVI data available in context.")

        # Retriever augmentation
        if self.retriever:
            try:
                docs = self.retriever.get_relevant_documents(query)
                if docs:
                    parts.append("\nRetrieved snippets:")
                    for d in docs[: self.retrieval_k]:
                        parts.append(f"- { _truncate(getattr(d, 'page_content', ''), 600) }")
            except Exception as e:
                logger.warning(f"Retriever failed: {e}")
        else:
            parts.append("\nNo vectorstore retrieval.")

        # Extra context 
        if extra_context:
            parts.append("\nExtra context:")
            for k, v in extra_context.items():
                parts.append(f"- {k}: {_truncate(v, 1000)}")

        parts.append(f"\nUSER QUESTION: {_truncate(query, 1500)}")
        return "\n".join(parts)
