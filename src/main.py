from __future__ import annotations

import logging
import unicodedata
from contextlib import asynccontextmanager
from typing import Any

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import get_settings
from src.domain import mask_phone
from src.marketing_automation import router as marketing_router
from src.marketing_automation import start_scheduler, stop_scheduler
from src.repositories import ChatRepository
from src.security import validate_shared_secret
from src.services import EvolutionClient, LLMClient, extract_message_id, extract_text_from_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("whatsapp-ai-bridge")


settings = get_settings()
chat_repository = ChatRepository(settings)
evolution_client = EvolutionClient(settings)
llm_client = LLMClient(settings, chat_repository)


@asynccontextmanager
async def lifespan(app: FastAPI):
    chat_repository.init()
    if settings.marketing_automation_enabled:
        start_scheduler()
    yield
    if settings.marketing_automation_enabled:
        stop_scheduler()


app = FastAPI(title="WhatsApp AI Agent", version="1.1.0", lifespan=lifespan)
app.include_router(marketing_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_origins != ["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/")
async def health_check():
    return {
        "status": "ok",
        "service": "whatsapp-ai-bridge",
        "model": settings.llm_model_id,
        "version": "1.1.0",
    }


@app.get("/healthz")
async def healthz():
    required = {
        "EVOLUTION_BASE_URL": settings.evolution_base_url,
        "EVOLUTION_API_KEY": settings.evolution_api_key,
        "LLM_API_URL": settings.llm_api_url,
        "LLM_API_KEY": settings.llm_api_key,
        "LLM_MODEL_ID": settings.llm_model_id,
    }
    missing = [k for k, v in required.items() if not v or str(v).strip() == ""]
    return {
        "status": "ok" if not missing else "degraded",
        "missing": missing,
        "service": "whatsapp-ai-bridge",
        "model": settings.llm_model_id,
    }


async def _handle_evolution_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_evolution_webhook_secret: str | None = Header(default=None),
):
    try:
        validate_shared_secret(
            x_evolution_webhook_secret,
            settings.evolution_webhook_secret,
            "invalid_evolution_webhook_secret",
        )
        data = await request.json()
        raw_event = str(data.get("event", ""))
        event = raw_event.lower().replace("-", "").replace("_", "")

        if ("messagesupsert" in event or "messages.upsert" in raw_event) and settings.ai_agent_enabled:
            background_tasks.add_task(handle_message, data)

        return JSONResponse({"status": "received"}, status_code=200)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error processing webhook: %s", exc)
        return JSONResponse({"status": "error", "message": str(exc)}, status_code=500)


@app.post("/evolution/webhook")
async def evolution_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_evolution_webhook_secret: str | None = Header(default=None),
):
    return await _handle_evolution_webhook(request, background_tasks, x_evolution_webhook_secret)


@app.post("/evolution/webhook/messages-upsert")
async def evolution_webhook_messages_upsert(
    request: Request,
    background_tasks: BackgroundTasks,
    x_evolution_webhook_secret: str | None = Header(default=None),
):
    return await _handle_evolution_webhook(request, background_tasks, x_evolution_webhook_secret)


async def handle_message(data: dict[str, Any]) -> None:
    sender = ""
    try:
        message_data = data.get("data", {})
        key = message_data.get("key", {}) if isinstance(message_data, dict) else {}
        remote_jid = str(key.get("remoteJid", "")) if isinstance(key, dict) else ""
        sender = remote_jid.split("@")[0]
        from_me = bool(key.get("fromMe", False)) if isinstance(key, dict) else False

        if from_me or remote_jid.endswith("@g.us") or "status@broadcast" in remote_jid or "broadcast" in remote_jid:
            return

        message_content = message_data.get("message", {}) if isinstance(message_data, dict) else {}
        text = extract_text_from_message(message_content)
        if not sender or not text:
            logger.info("Ignoring non-text or empty message from %s", mask_phone(sender) if sender else "unknown")
            return

        message_id = extract_message_id(message_data)
        if not chat_repository.mark_message_processed(message_id, sender):
            logger.info("Ignoring duplicate message from %s", mask_phone(sender))
            return

        if chat_repository.is_opted_out(sender):
            logger.info("Ignoring opted-out contact %s", mask_phone(sender))
            return

        logger.info("Incoming message from %s", mask_phone(sender))
        lower_text = text.lower()
        normalized_text = unicodedata.normalize("NFKD", lower_text).encode("ascii", "ignore").decode("ascii")
        if any(marker in normalized_text for marker in ["parar", "sair", "nao quero", "stop"]):
            chat_repository.set_opted_out(sender)
            await evolution_client.send_text(
                sender,
                "Perfeito. Vou encerrar as mensagens por aqui. Se quiser retomar depois, e so me chamar.",
            )
            return

        chat_repository.append_memory(sender, "user", text)
        llm_reply = await llm_client.call(text, sender)
        if not llm_reply:
            logger.warning("LLM returned empty reply")
            return

        chat_repository.append_memory(sender, "assistant", llm_reply)
        await evolution_client.send_bubbles(sender, llm_reply)
    except Exception as exc:
        logger.exception("Error handling message: %s", exc)
        if sender:
            await evolution_client.send_text(
                sender,
                "Tive uma instabilidade rapida aqui. Me chama de novo com sua duvida que eu ja te respondo.",
            )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
