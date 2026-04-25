"""
WhatsApp AI Agent - FastAPI Bridge
Integração entre Evolution API e LLMs para atendimento comercial no WhatsApp.

Modelo: Kimi K2.5 (NVIDIA/MoonshotAI)
API: Evolution API v2.3.6 (Baileys)
Framework: FastAPI + Uvicorn
"""

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import logging
import json
import asyncio
import re
import os
import random
import sqlite3
import time
from dotenv import load_dotenv
from src.marketing_automation import router as marketing_router, start_scheduler, stop_scheduler

# Configurações de log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("whatsapp-ai-bridge")

# Carrega variáveis do .env local (quando existir)
load_dotenv()

# Evolution API config - use environment variables
EVOLUTION_BASE_URL = os.getenv("EVOLUTION_BASE_URL", "https://your-evolution-api.com")
EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE", "default")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "")

# LLM API config
OPENAI_API_URL = os.getenv("LLM_API_URL", "http://localhost:18789/v1/chat/completions")
OPENAI_API_KEY = os.getenv("LLM_API_KEY", "")
MODEL_ID = os.getenv("LLM_MODEL_ID", "nvidia-kimi/moonshotai/kimi-k2.5")
THINKING_LEVEL = os.getenv("THINKING_LEVEL", "high")

# Gemini STT/Vision
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
GEMINI_STT_MODEL = os.getenv("GEMINI_STT_MODEL", "gemini-1.5-flash")

# Notifications
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_IDS = os.getenv("TELEGRAM_CHAT_IDS", "").split(",") if os.getenv("TELEGRAM_CHAT_IDS") else []

# Paths
AGENTS_DIR = os.getenv("AGENTS_DIR", "/root/.openclaw/agents")
WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "/root/clawd")
CLIENTS_DIR = os.getenv("CLIENTS_DIR", "/root/clawd/clients")

# Arquivos de persistência
MEMORY_FILE = os.getenv("MEMORY_FILE", "./data/chat_memory.json")
BLACKLIST_FILE = os.getenv("BLACKLIST_FILE", "./data/ignored_numbers.json")
DB_PATH = os.getenv("DB_PATH", "./data/agent.db")
LOG_FILE = os.getenv("LOG_FILE", "./logs/app.log")

# Feature flags
MARKETING_AUTOMATION_ENABLED = str(os.getenv("MARKETING_AUTOMATION_ENABLED", "true")).strip().lower() in {"1", "true", "yes", "on"}
AI_AGENT_ENABLED = str(os.getenv("AI_AGENT_ENABLED", "true")).strip().lower() in {"1", "true", "yes", "on"}

# Modo comercial (closer)
CLOSER_ENABLED = str(os.getenv("CLOSER_ENABLED", "true")).strip().lower() in {"1", "true", "yes", "on"}
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "12"))
TYPING_ENABLED = str(os.getenv("TYPING_ENABLED", "true")).strip().lower() in {"1", "true", "yes", "on"}

PRODUCT_LINKS = {
    "chave": "https://syncronix.co/ebook-a-chave-do-poder",
    "regra": "https://syncronix.co/ebook-a-regra-da-vida",
    "algoritmo": "https://syncronix.co/ebook-o-algoritmo-do-universo",
    "energy": "https://syncronix.co/energy-hack",
    "gestao": "https://syncronix.co/gestao-inteligente",
}

CLOSER_SYSTEM_PROMPT = f"""
Você é closer comercial da Syncronix no WhatsApp.
Objetivo: converter com ética, clareza e foco em resultado.

Regras:
- Seja direto, humano, confiante e consultivo.
- Mensagens curtas (2-6 linhas), sem texto longo.
- Faça no máximo 1 pergunta por resposta.
- Conduza para próximo passo com CTA claro.
- Quando fizer sentido, ofereça o link correto do produto.

Produtos/links:
- Chave do Poder: {PRODUCT_LINKS['chave']}
- Regra da Vida: {PRODUCT_LINKS['regra']}
- Algoritmo do Universo: {PRODUCT_LINKS['algoritmo']}
- Energy Hack: {PRODUCT_LINKS['energy']}
- Gestão Inteligente: {PRODUCT_LINKS['gestao']}

Política comercial:
- Não inventar preço, prazo ou bônus não confirmados.
- Se cliente pedir suporte humano, responda com handoff amigável.
- Se cliente disser parar/sair/não quero, respeite e encerre.
""".strip()

app = FastAPI(title="WhatsApp AI Agent", version="1.0.0")
app.include_router(marketing_router)


@app.on_event("startup")
async def _on_startup():
    init_chat_db()
    if MARKETING_AUTOMATION_ENABLED:
        start_scheduler()


@app.on_event("shutdown")
async def _on_shutdown():
    if MARKETING_AUTOMATION_ENABLED:
        stop_scheduler()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "whatsapp-ai-bridge",
        "model": MODEL_ID,
        "version": "1.0.0"
    }


@app.get("/healthz")
async def healthz():
    """Readiness endpoint with minimal config validation."""
    required = {
        "EVOLUTION_BASE_URL": EVOLUTION_BASE_URL,
        "EVOLUTION_API_KEY": EVOLUTION_API_KEY,
        "LLM_API_URL": OPENAI_API_URL,
        "LLM_API_KEY": OPENAI_API_KEY,
        "LLM_MODEL_ID": MODEL_ID,
    }
    missing = [k for k, v in required.items() if not v or str(v).strip() == ""]
    status = "ok" if not missing else "degraded"
    return {
        "status": status,
        "missing": missing,
        "service": "whatsapp-ai-bridge",
        "model": MODEL_ID,
    }


async def _handle_evolution_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Endpoint para receber webhooks da Evolution API.
    Processa eventos de mensagens e dispara respostas automáticas.
    """
    try:
        data = await request.json()

        # Normaliza o nome do evento (suporta -, _, case variations)
        raw_event = data.get("event", "")
        event = raw_event.lower().replace("-", "").replace("_", "")

        if ("messagesupsert" in event or "messages.upsert" in raw_event) and AI_AGENT_ENABLED:
            background_tasks.add_task(handle_message, data)

        return JSONResponse({"status": "received"}, status_code=200)

    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.post("/evolution/webhook")
async def evolution_webhook(request: Request, background_tasks: BackgroundTasks):
    return await _handle_evolution_webhook(request, background_tasks)


@app.post("/evolution/webhook/messages-upsert")
async def evolution_webhook_messages_upsert(request: Request, background_tasks: BackgroundTasks):
    return await _handle_evolution_webhook(request, background_tasks)


def init_chat_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_profiles (
                phone TEXT PRIMARY KEY,
                name TEXT,
                language TEXT,
                summary_text TEXT,
                last_seen_at TEXT,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_chat_messages_phone_created
            ON chat_messages(phone, id)
            """
        )

        # Migração simples para bancos antigos
        cols = [r[1] for r in conn.execute("PRAGMA table_info(chat_profiles)").fetchall()]
        if "summary_text" not in cols:
            conn.execute("ALTER TABLE chat_profiles ADD COLUMN summary_text TEXT")

        conn.commit()


def _build_summary(conn: sqlite3.Connection, phone: str) -> str:
    rows = conn.execute(
        "SELECT role, content FROM chat_messages WHERE phone = ? ORDER BY id DESC LIMIT 16",
        (phone,),
    ).fetchall()
    rows = list(reversed(rows))

    user_points = []
    assistant_points = []
    for role, content in rows:
        c = (content or "").strip().replace("\n", " ")
        if not c:
            continue
        if role == "user" and len(user_points) < 8:
            user_points.append(c[:140])
        if role == "assistant" and len(assistant_points) < 4:
            assistant_points.append(c[:140])

    parts = []
    if user_points:
        parts.append("Cliente disse: " + " | ".join(user_points))
    if assistant_points:
        parts.append("Bot respondeu: " + " | ".join(assistant_points))
    return " || ".join(parts)[:1200]


def append_memory(phone: str, role: str, content: str) -> None:
    ts = str(time.time())
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO chat_messages (phone, role, content, created_at) VALUES (?, ?, ?, ?)",
            (phone, role, content, ts),
        )
        conn.execute(
            """
            INSERT INTO chat_profiles (phone, updated_at, last_seen_at)
            VALUES (?, ?, ?)
            ON CONFLICT(phone) DO UPDATE SET
              updated_at=excluded.updated_at,
              last_seen_at=excluded.last_seen_at
            """,
            (phone, ts, ts),
        )

        # Mantém histórico curto no banco por usuário
        conn.execute(
            """
            DELETE FROM chat_messages
            WHERE phone = ?
              AND id NOT IN (
                SELECT id FROM chat_messages WHERE phone = ? ORDER BY id DESC LIMIT ?
              )
            """,
            (phone, phone, MAX_HISTORY_MESSAGES * 4),
        )

        summary = _build_summary(conn, phone)
        conn.execute(
            "UPDATE chat_profiles SET summary_text=?, updated_at=? WHERE phone=?",
            (summary, ts, phone),
        )

        conn.commit()


def get_profile_summary(phone: str) -> str:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT summary_text FROM chat_profiles WHERE phone=?", (phone,)).fetchone()
    if not row:
        return ""
    return (row[0] or "").strip()


def get_history(phone: str) -> list:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT role, content FROM chat_messages WHERE phone = ? ORDER BY id DESC LIMIT ?",
            (phone, MAX_HISTORY_MESSAGES),
        ).fetchall()

    # retorna em ordem cronológica
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


def extract_text_from_message(message_content: dict) -> str:
    """Extrai texto de formatos comuns do Baileys/Evolution."""
    if not isinstance(message_content, dict):
        return ""

    direct_keys = [
        ("conversation", None),
        ("extendedTextMessage", "text"),
        ("imageMessage", "caption"),
        ("videoMessage", "caption"),
        ("documentMessage", "caption"),
    ]

    for key, sub in direct_keys:
        obj = message_content.get(key)
        if sub is None and isinstance(obj, str) and obj.strip():
            return obj.strip()
        if sub and isinstance(obj, dict):
            val = obj.get(sub)
            if isinstance(val, str) and val.strip():
                return val.strip()

    # Wrappers comuns
    for wrapper in ("ephemeralMessage", "viewOnceMessage", "viewOnceMessageV2", "documentWithCaptionMessage"):
        wrapped = message_content.get(wrapper)
        if isinstance(wrapped, dict):
            inner = wrapped.get("message") if isinstance(wrapped.get("message"), dict) else wrapped
            text = extract_text_from_message(inner)
            if text:
                return text

    return ""


def _extract_llm_text(data: dict) -> str:
    choice = (data.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    content = message.get("content")

    if isinstance(content, str) and content.strip():
        return content.strip()

    if isinstance(content, list):
        parts = [part.get("text", "") for part in content if isinstance(part, dict)]
        joined = " ".join([p for p in parts if p]).strip()
        if joined:
            return joined

    for fallback_key in ("output_text", "output", "text"):
        fallback = message.get(fallback_key) or choice.get(fallback_key) or data.get(fallback_key)
        if isinstance(fallback, str) and fallback.strip():
            return fallback.strip()

    return ""


async def call_llm(user_message: str, phone: str) -> str:
    """Chama o modelo configurado via endpoint OpenAI-compatible."""
    if not OPENAI_API_KEY:
        raise RuntimeError("LLM_API_KEY is missing")

    thinking_enabled = str(THINKING_LEVEL).strip().lower() in {"true", "high", "1", "yes", "on"}

    messages = []
    if CLOSER_ENABLED:
        messages.append({"role": "system", "content": CLOSER_SYSTEM_PROMPT})

    summary = get_profile_summary(phone)
    if summary:
        messages.append({"role": "system", "content": f"Contexto resumido do cliente: {summary}"})

    messages.extend(get_history(phone))
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": MODEL_ID,
        "messages": messages,
        "max_tokens": 600,
        "temperature": 0.7,
        "top_p": 1,
        "stream": False,
        "chat_template_kwargs": {"thinking": bool(thinking_enabled)},
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Accept": "application/json",
    }

    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post(OPENAI_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    text = _extract_llm_text(data)
    if text:
        return text

    # Retry sem thinking para evitar respostas com content=null
    retry_payload = dict(payload)
    retry_payload.pop("chat_template_kwargs", None)
    retry_payload["max_tokens"] = 400

    async with httpx.AsyncClient(timeout=45) as client:
        response2 = await client.post(OPENAI_API_URL, headers=headers, json=retry_payload)
        response2.raise_for_status()
        data2 = response2.json()

    text2 = _extract_llm_text(data2)
    if text2:
        return text2

    raise RuntimeError("LLM response without usable content")


async def handle_message(data: dict):
    """Processa mensagem recebida e gera resposta."""
    sender = ""
    try:
        message_data = data.get("data", {})
        key = message_data.get("key", {})
        remote_jid = key.get("remoteJid", "")
        sender = remote_jid.split("@")[0]
        from_me = key.get("fromMe", False)

        # Ignora mensagens próprias, grupos, status e broadcast
        if from_me or remote_jid.endswith("@g.us") or "status@broadcast" in remote_jid or "broadcast" in remote_jid:
            return

        # Extrai texto da mensagem
        message_content = message_data.get("message", {})
        text = extract_text_from_message(message_content)

        if not sender or not text:
            logger.info(f"Ignoring non-text or empty message from {sender}")
            return

        logger.info(f"Incoming message from {sender}")

        lower_text = text.lower()
        if any(x in lower_text for x in ["parar", "sair", "não quero", "nao quero", "stop"]):
            await send_text(sender, "Perfeito. Vou encerrar as mensagens por aqui. Se quiser retomar depois, é só me chamar. 🤝")
            return

        append_memory(sender, "user", text)

        llm_reply = await call_llm(text, sender)
        if not llm_reply:
            logger.warning("LLM returned empty reply")
            return

        append_memory(sender, "assistant", llm_reply)
        await send_bubbles(sender, llm_reply)

    except Exception as e:
        logger.exception(f"Error handling message: {e}")
        if sender:
            await send_text(sender, "Tive uma instabilidade rápida aqui. Me chama de novo com sua dúvida que eu já te respondo. 🤝")


async def send_typing(number: str, delay_ms: int = 900) -> None:
    """Dispara presença 'composing' (digitando) com best-effort."""
    if not EVOLUTION_API_KEY or not TYPING_ENABLED:
        return

    headers = {
        "Content-Type": "application/json",
        "apikey": EVOLUTION_API_KEY,
    }

    candidates = [
        (f"{EVOLUTION_BASE_URL}/chat/sendPresence/{EVOLUTION_INSTANCE}", {"number": number, "presence": "composing", "delay": delay_ms}),
        (f"{EVOLUTION_BASE_URL}/chat/presence/{EVOLUTION_INSTANCE}", {"number": number, "presence": "composing", "delay": delay_ms}),
        (f"{EVOLUTION_BASE_URL}/presence/set/{EVOLUTION_INSTANCE}", {"number": number, "presence": "composing", "delay": delay_ms}),
    ]

    async with httpx.AsyncClient(timeout=2.5) as client:
        for url, payload in candidates:
            try:
                resp = await client.post(url, headers=headers, json=payload)
                # qualquer resposta indica endpoint alcançado; não travar fluxo
                if resp.status_code < 500:
                    return
            except Exception:
                continue


async def send_text(number: str, text: str) -> bool:
    """Envia mensagem de texto via Evolution API."""
    try:
        url = f"{EVOLUTION_BASE_URL}/message/sendText/{EVOLUTION_INSTANCE}"
        headers = {
            "Content-Type": "application/json",
            "apikey": EVOLUTION_API_KEY
        }
        payload = {
            "number": number,
            "text": text
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            logger.info(f"Message sent to {number}: {response.status_code}")
            return True

    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        return False


async def send_bubbles(number: str, text: str):
    """Quebra mensagem em balões para parecer mais humano."""
    # Separa por parágrafos ou sentenças
    parts = re.split(r'\n+|(?<=[.!?])\s+', text)
    parts = [p.strip() for p in parts if p.strip()]

    for part in parts:
        # Simula digitação curta para não atrasar resposta
        typing_ms = max(500, min(1200, len(part) * 12))
        await send_typing(number, delay_ms=typing_ms)
        await asyncio.sleep(typing_ms / 1000)

        if len(part) > 500:
            # Quebra mensagens longas
            for i in range(0, len(part), 500):
                chunk = part[i:i+500]
                chunk_typing_ms = max(400, min(1000, len(chunk) * 10))
                await send_typing(number, delay_ms=chunk_typing_ms)
                await asyncio.sleep(chunk_typing_ms / 1000)
                await send_text(number, chunk)
                await asyncio.sleep(0.4)
        else:
            await send_text(number, part)
            await asyncio.sleep(random.uniform(0.2, 0.6))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
