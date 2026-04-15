"""
WhatsApp AI Agent - FastAPI Bridge
Integração entre Evolution API e LLMs para atendimento comercial no WhatsApp.

Modelo: Kimi K2.5 (NVIDIA/MoonshotAI)
API: Evolution API v2.3.6 (Baileys)
Framework: FastAPI + Uvicorn
"""

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import logging
import json
import asyncio
import re
import os
import glob as globmod
import base64
import sqlite3
import time
from fpdf import FPDF
from gtts import gTTS
import io
import random

# Configurações de log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("whatsapp-ai-bridge")

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


@app.post("/evolution/webhook")
async def evolution_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Endpoint para receber webhooks da Evolution API.
    Processa eventos de mensagens e dispara respostas automáticas.
    """
    try:
        data = await request.json()
        logger.info(f"Webhook received: {json.dumps(data, indent=2)}")

        # Normaliza o nome do evento (suporta -, _, case variations)
        event = data.get("event", "").lower().replace("-", "").replace("_", "")

        if "messagesupsert" in event or "messages.upsert" in data.get("event", ""):
            await handle_message(data)

        return {"status": "received"}, 200

    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return {"status": "error", "message": str(e)}, 500


async def handle_message(data: dict):
    """Processa mensagem recebida e gera resposta."""
    try:
        message_data = data.get("data", {})
        key = message_data.get("key", {})
        sender = key.get("remoteJid", "").split("@")[0]
        from_me = key.get("fromMe", False)

        if from_me:
            logger.info(f"Ignoring message from self: {sender}")
            return

        # Extrai texto da mensagem
        message_content = message_data.get("message", {})
        text = (
            message_content.get("conversation") or
            message_content.get("extendedTextMessage", {}).get("text") or
            ""
        )

        if not sender or not text:
            logger.warning("Missing sender or text")
            return

        logger.info(f"Message from {sender}: {text}")

        # TODO: Implement complete flow:
        # 1. Check blacklist
        # 2. Detect intent
        # 3. Load context/memory
        # 4. Call LLM (Kimi 2.5)
        # 5. Fragment response
        # 6. Send via Evolution API

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
