"""
@file llm_controller.py
@author naflashDev
@brief FastAPI routes to interact with the remote LLM.
@details Provides HTTP endpoints for programmatic and UI-based queries to the LLM service, including prompt submission and periodic training triggers.
"""


from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel
from loguru import logger
from app.services.llm.llm_client import query_llm
from app.services.llm.llm_trainer import run_periodic_training
from typing import Optional, List
import threading
import hashlib
import os
import json

from sqlalchemy.orm import Session
from app.models.conversation_db import get_conv_db
from app.models.conversation import Conversation, Message

# Optional Chroma client (scaffold). If chromadb not installed, operations will be skipped.
try:
    import app.services.vectorstore.chroma_client as chroma_mod
    if getattr(chroma_mod, "CHROMA_AVAILABLE", False):
        try:
            # Initialize embed model adapter if Ollama is available so queries return context
            embed_model = None
            try:
                from app.services.vectorstore.ollama_adapter import OllamaEmbeddingAdapter
                import shutil, os
                if shutil.which('ollama'):
                    embed_name = os.getenv('EMBED_MODEL_NAME', 'nomic-embed-text:latest')
                    try:
                        embed_model = OllamaEmbeddingAdapter(model_name=embed_name)
                    except Exception:
                        embed_model = None
            except Exception:
                embed_model = None
            _chroma_client = chroma_mod.ChromaClient(embed_model=embed_model)
        except Exception:
            _chroma_client = None
    else:
        _chroma_client = None
except Exception:
    _chroma_client = None


class UpdaterToggle(BaseModel):
    enabled: bool

router = APIRouter(prefix="/llm", tags=["llm"])


class LLMQuery(BaseModel):
    """
    @brief Request model for LLM query endpoint.
    """
    prompt: str
    conversation_id: Optional[int] = None
    top_k: int = 5


class ConversationCreate(BaseModel):
    title: Optional[str] = None


class MessageCreate(BaseModel):
    role: str
    text: str


class MessageOut(BaseModel):
    id: int
    role: str
    text: str
    timestamp: str
    vector_id: Optional[str]


class ConversationOut(BaseModel):
    id: int
    title: Optional[str]
    created_at: str
    messages: List[MessageOut] = []


@router.post("/query")
async def llm_query(payload: LLMQuery, db: Session = Depends(get_conv_db)):
    """
    @brief Receives a prompt, retrieves context via vectorstore, persists turns and returns the LLM response.
    @param payload JSON body with 'prompt', optional 'conversation_id' and 'top_k'.
    @return JSON object containing 'response' string and optional 'retrieved' list.
    """
    retrieved = []

    # Persist user message if conversation provided
    user_msg = None
    if payload.conversation_id is not None:
        try:
            user_msg = Message(conversation_id=payload.conversation_id, role='user', text=payload.prompt)
            db.add(user_msg)
            db.commit()
            db.refresh(user_msg)
            # optionally upsert the user message as a vector (handled in add_message route normally)
        except Exception:
            logger.exception("[LLM] Could not persist user message")

    # If conversation_id provided, load conversation history (as ordered messages)
    conv_history_text = ''
    conversation_messages = []
    if payload.conversation_id is not None:
        try:
            msgs = db.query(Message).filter(Message.conversation_id == payload.conversation_id).order_by(Message.timestamp.asc()).all()
            # keep last N messages to avoid huge prompts
            N = 30
            msgs = msgs[-N:]
            for m in msgs:
                # map DB role directly to chat role (expect 'user'/'assistant')
                conversation_messages.append({
                    "role": m.role if m.role in ('user', 'assistant', 'system') else 'user',
                    "content": m.text
                })
            # also keep a compact text version for logging/debugging
            if conversation_messages:
                parts = [f"[{c['role'].capitalize()}] {c['content']}" for c in conversation_messages]
                conv_history_text = "\n---\n".join(parts)
        except Exception:
            logger.exception("[LLM] Could not load conversation history")

    # Retrieve context from Chroma if available and assemble chat messages
    messages = []
    # If we have retrieved documents, add them as an initial system message to provide grounding
    if _chroma_client is not None:
        try:
            docs = _chroma_client.query_retriever(payload.prompt, k=payload.top_k)
            retrieved = docs
            if docs:
                parts = []
                for i, d in enumerate(docs, start=1):
                    md = d.get('metadata') or {}
                    src = md.get('source') or md.get('conversation_id') or md.get('id') or 'unknown'
                    parts.append(f"[{i}] Source: {src}\n{d.get('text')}\n")
                context_text = "\n---\n".join(parts)
                # Add retrieved docs as a system-level context message
                messages.append({"role": "system", "content": f"Retrieved context:\n{context_text}"})
        except Exception:
            logger.exception("[LLM] Error querying retriever; continuing without context")

    # Append conversation history messages (if any)
    if conversation_messages:
        messages.extend(conversation_messages)

    # Finally append the current user prompt as the last message
    messages.append({"role": "user", "content": payload.prompt})

    # Call the LLM with the assembled messages (chat format)
    try:
        response = query_llm(messages=messages)
    except Exception:
        logger.exception("[LLM] Error calling LLM")
        raise HTTPException(status_code=500, detail="LLM generation failed")

    # Persist assistant message
    if payload.conversation_id is not None:
        try:
            assistant_msg = Message(conversation_id=payload.conversation_id, role='assistant', text=response)
            db.add(assistant_msg)
            db.commit()
            db.refresh(assistant_msg)
        except Exception:
            logger.exception("[LLM] Could not persist assistant message")

    logger.debug(f"[LLM Client] Sending response to the user.")
    return {"response": response, "retrieved": retrieved}


@router.post("/conversations", response_model=ConversationOut)
def create_conversation(payload: ConversationCreate, db: Session = Depends(get_conv_db)):
    conv = Conversation(title=payload.title)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return ConversationOut(id=conv.id, title=conv.title, created_at=conv.created_at.isoformat(), messages=[])


@router.get("/conversations", response_model=List[ConversationOut])
def list_conversations(db: Session = Depends(get_conv_db)):
    convs = db.query(Conversation).order_by(Conversation.created_at.desc()).all()
    out = []
    for c in convs:
        out.append(ConversationOut(id=c.id, title=c.title, created_at=c.created_at.isoformat(), messages=[]))
    return out


@router.get("/conversations/{conv_id}", response_model=ConversationOut)
def get_conversation(conv_id: int, db: Session = Depends(get_conv_db)):
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    msgs = []
    for m in conv.messages:
        msgs.append(MessageOut(id=m.id, role=m.role, text=m.text, timestamp=m.timestamp.isoformat(), vector_id=m.vector_id))
    return ConversationOut(id=conv.id, title=conv.title, created_at=conv.created_at.isoformat(), messages=msgs)


@router.post("/conversations/{conv_id}/messages", response_model=MessageOut)
def add_message(conv_id: int, payload: MessageCreate, db: Session = Depends(get_conv_db)):
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    msg = Message(conversation_id=conv.id, role=payload.role, text=payload.text)
    db.add(msg)
    db.commit()
    db.refresh(msg)

    # If Chroma client available, upsert the message text as a vector and persist vector_id
    if _chroma_client is not None:
        try:
            doc_id = f"conv-{conv.id}-msg-{msg.id}"
            _chroma_client.upsert_document(doc_id=doc_id, text=msg.text, metadata={
                "timestamp": msg.timestamp.isoformat(),
                "conversation_id": conv.id,
                "role": msg.role,
            })
            msg.vector_id = doc_id
            db.add(msg)
            db.commit()
            db.refresh(msg)
        except Exception:
            logger.exception("Failed to upsert message to Chroma (continuing)")

    return MessageOut(id=msg.id, role=msg.role, text=msg.text, timestamp=msg.timestamp.isoformat(), vector_id=msg.vector_id)


@router.delete('/conversations/{conv_id}')
def delete_conversation(conv_id: int, db: Session = Depends(get_conv_db)):
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    try:
        db.delete(conv)
        db.commit()
        return {"deleted": True}
    except Exception:
        logger.exception("[LLM] Could not delete conversation")
        raise HTTPException(status_code=500, detail="Could not delete conversation")

def background_cve_and_finetune_loop(stop_event: Optional[threading.Event] = None) -> None:
    """
    @brief Background loop to update CVE repo and rebuild LLM dataset every 7 days.
    @details
        - Calls run_periodic_training() once per cycle.
        - Sleeps for 7 days (7 * 24 * 60 * 60 seconds) between executions.
    """
    import time
    from loguru import logger

    interval = 7 * 24 * 60 * 60  # 7 days
    # If no stop_event provided, create a dummy one to keep compatibility
    if stop_event is None:
        stop_event = threading.Event()

    while not stop_event.is_set():
        try:
            logger.info("[LLM Trainer] Starting 7-day CVE update + dataset build cycle...")
            run_periodic_training(stop_event=stop_event)
            logger.info("[LLM Trainer] 7-day CVE + dataset cycle finished.")
            # After the dataset is rebuilt, ingest generated finetune JSONL into
            # the vectorstore so documents become available for retrieval.
            try:
                ingest_finetune_to_chroma("./outputs/finetune_data.jsonl")
            except Exception:
                logger.exception("[LLM Trainer] Failed to ingest finetune file into vectorstore")
        except Exception as e:
            logger.error(f"[LLM Trainer] Error in 7-day loop: {e}")
            # No UI error here, but if hay endpoints que devuelven error, deben ser genéricos
        # Wait in an interruptible way so shutdown can proceed quickly
        try:
            stop_event.wait(interval)
        except Exception:
            # If wait fails for any reason, fallback to sleep a short time then re-check
            time.sleep(5)


def ingest_finetune_to_chroma(output_path: str = "./outputs/finetune_data.jsonl") -> None:
    """
    @brief Read a JSONL finetune file and upsert each record into the Chromadb collection.

    Each record is given a stable id derived from the instruction+input hash so
    repeated ingestions won't create duplicate entries (upsert overwrites).
    """
    try:
        if _chroma_client is None:
            logger.warning("[LLM] No Chroma client available; skipping finetune ingestion.")
            return
        if not os.path.exists(output_path):
            logger.warning(f"[LLM] Finetune file not found: {output_path}")
            return
        with open(output_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    instr = rec.get("instruction", "") or ""
                    inp = rec.get("input", "") or ""
                    outp = rec.get("output", "") or ""
                    text = instr + "\n\n" + inp + "\n\n" + outp
                    h = hashlib.sha256()
                    h.update((instr + "||" + inp).encode("utf-8"))
                    doc_id = "finetune-" + h.hexdigest()
                    metadata = {"source": rec.get("source", "finetune")}
                    _chroma_client.upsert_document(doc_id=doc_id, text=text, metadata=metadata)
                except Exception:
                    logger.exception("[LLM] Error ingesting finetune record into Chroma; continuing.")
    except Exception:
        logger.exception("[LLM] Unexpected error during finetune ingestion")



@router.get('/updater')
async def updater_get(request: Request):
    """Start the LLM updater background loop via GET (compatible with other GET starters)."""
    # ensure app.state dicts
    if getattr(request.app.state, 'worker_stop_events', None) is None:
        request.app.state.worker_stop_events = {}
    if getattr(request.app.state, 'worker_timers', None) is None:
        request.app.state.worker_timers = {}
    if getattr(request.app.state, 'worker_status', None) is None:
        request.app.state.worker_status = {}

    name = 'llm_updater'
    if request.app.state.worker_status.get(name):
        return {"message": f"Worker {name} already running"}

    evt = threading.Event()
    request.app.state.worker_stop_events[name] = evt
    th = threading.Thread(target=background_cve_and_finetune_loop, args=(evt,), daemon=True)
    th.start()
    request.app.state.worker_timers[name] = th
    request.app.state.worker_status[name] = True
    logger.info(f"[LLM] Updater started via /llm/updater")
    return {"message": "LLM updater started"}


@router.get('/stop-updater')
async def stop_updater(request: Request):
    """Stop the LLM updater background loop (GET endpoint)."""
    name = 'llm_updater'
    if getattr(request.app.state, 'worker_stop_events', None) is None:
        request.app.state.worker_stop_events = {}
    if getattr(request.app.state, 'worker_timers', None) is None:
        request.app.state.worker_timers = {}
    if getattr(request.app.state, 'worker_status', None) is None:
        request.app.state.worker_status = {}

    evt = request.app.state.worker_stop_events.get(name)
    if evt is not None:
        try:
            evt.set()
        except Exception:
            pass

    timer = request.app.state.worker_timers.get(name)
    if timer is not None:
        try:
            if hasattr(timer, 'cancel'):
                timer.cancel()
        except Exception:
            pass

    request.app.state.worker_status[name] = False
    logger.info(f"[LLM] Updater stopped via /llm/stop-updater")
    return {"message": "LLM updater stopped"}
