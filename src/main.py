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
from dotenv import load_dotenv

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

app = FastAPI(title="WhatsApp AI Agent", version="1.0.0")

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


@app.post("/evolution/webhook")
async def evolution_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Endpoint para receber webhooks da Evolution API.
    Processa eventos de mensagens e dispara respostas automáticas.
    """
    try:
        data = await request.json()

        # Normaliza o nome do evento (suporta -, _, case variations)
        raw_event = data.get("event", "")
        event = raw_event.lower().replace("-", "").replace("_", "")

        if "messagesupsert" in event or "messages.upsert" in raw_event:
            background_tasks.add_task(handle_message, data)

        return JSONResponse({"status": "received"}, status_code=200)

    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


async def call_llm(user_message: str) -> str:
    """Chama o modelo configurado via endpoint OpenAI-compatible."""
    if not OPENAI_API_KEY:
        raise RuntimeError("LLM_API_KEY is missing")

    thinking_enabled = str(THINKING_LEVEL).strip().lower() in {"true", "high", "1", "yes", "on"}

    payload = {
        "model": MODEL_ID,
        "messages": [{"role": "user", "content": user_message}],
        "max_tokens": 1024,
        "temperature": 0.7,
        "top_p": 1,
        "stream": False,
    }

    if thinking_enabled:
        payload["chat_template_kwargs"] = {"thinking": True}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Accept": "application/json",
    }

    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post(OPENAI_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

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

    for fallback_key in ("reasoning_content", "output_text", "output"):
        fallback = message.get(fallback_key) or choice.get(fallback_key) or data.get(fallback_key)
        if isinstance(fallback, str) and fallback.strip():
            return fallback.strip()

    raise RuntimeError("LLM response without usable content")


async def handle_message(data: dict):
    """Processa mensagem recebida e gera resposta."""
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
        text = (
            message_content.get("conversation") or
            message_content.get("extendedTextMessage", {}).get("text") or
            ""
        ).strip()

        if not sender or not text:
            return

        logger.info(f"Incoming message from {sender}")

        llm_reply = await call_llm(text)
        if not llm_reply:
            logger.warning("LLM returned empty reply")
            return

        await send_bubbles(sender, llm_reply)

    except Exception as e:
        logger.error(f"Error handling message: {e}")


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
        if len(part) > 500:
            # Quebra mensagens longas
            for i in range(0, len(part), 500):
                await send_text(number, part[i:i+500])
                await asyncio.sleep(1)
        else:
            await send_text(number, part)
            await asyncio.sleep(random.uniform(0.5, 1.5))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
