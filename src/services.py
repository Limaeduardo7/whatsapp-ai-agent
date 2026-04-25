from __future__ import annotations

import asyncio
import logging
import random
import re
from typing import Any

import httpx

from src.config import Settings
from src.repositories import ChatRepository

logger = logging.getLogger("whatsapp-ai-agent")


PRODUCT_LINKS = {
    "chave": "https://syncronix.co/ebook-a-chave-do-poder",
    "regra": "https://syncronix.co/ebook-a-regra-da-vida",
    "algoritmo": "https://syncronix.co/ebook-o-algoritmo-do-universo",
    "energy": "https://syncronix.co/energy-hack",
    "gestao": "https://syncronix.co/gestao-inteligente",
}


def closer_system_prompt() -> str:
    return f"""
Voce e closer comercial da Syncronix no WhatsApp.
Objetivo: converter com etica, clareza e foco em resultado.

Regras:
- Seja direto, humano, confiante e consultivo.
- Mensagens curtas (2-6 linhas), sem texto longo.
- Faca no maximo 1 pergunta por resposta.
- Conduza para proximo passo com CTA claro.
- Quando fizer sentido, ofereca o link correto do produto.

Produtos/links:
- Chave do Poder: {PRODUCT_LINKS['chave']}
- Regra da Vida: {PRODUCT_LINKS['regra']}
- Algoritmo do Universo: {PRODUCT_LINKS['algoritmo']}
- Energy Hack: {PRODUCT_LINKS['energy']}
- Gestao Inteligente: {PRODUCT_LINKS['gestao']}

Politica comercial:
- Nao inventar preco, prazo ou bonus nao confirmados.
- Se cliente pedir suporte humano, responda com handoff amigavel.
- Se cliente disser parar/sair/nao quero, respeite e encerre.
""".strip()


def extract_text_from_message(message_content: dict[str, Any]) -> str:
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

    for wrapper in ("ephemeralMessage", "viewOnceMessage", "viewOnceMessageV2", "documentWithCaptionMessage"):
        wrapped = message_content.get(wrapper)
        if isinstance(wrapped, dict):
            inner = wrapped.get("message") if isinstance(wrapped.get("message"), dict) else wrapped
            text = extract_text_from_message(inner)
            if text:
                return text
    return ""


def extract_message_id(message_data: dict[str, Any]) -> str:
    key = message_data.get("key", {}) if isinstance(message_data, dict) else {}
    message_id = key.get("id") if isinstance(key, dict) else None
    if message_id:
        return str(message_id)
    remote_jid = key.get("remoteJid", "") if isinstance(key, dict) else ""
    ts = message_data.get("messageTimestamp", "")
    text = extract_text_from_message(message_data.get("message", {}))
    return f"{remote_jid}:{ts}:{hash(text)}"


def _extract_llm_text(data: dict[str, Any]) -> str:
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


class LLMClient:
    def __init__(self, settings: Settings, chat_repository: ChatRepository) -> None:
        self.settings = settings
        self.chat_repository = chat_repository

    async def call(self, user_message: str, phone: str) -> str:
        if not self.settings.llm_api_key:
            raise RuntimeError("LLM_API_KEY is missing")

        thinking_enabled = self.settings.thinking_level.strip().lower() in {"true", "high", "1", "yes", "on"}
        messages: list[dict[str, str]] = []
        if self.settings.closer_enabled:
            messages.append({"role": "system", "content": closer_system_prompt()})
        summary = self.chat_repository.get_profile_summary(phone)
        if summary:
            messages.append({"role": "system", "content": f"Contexto resumido do cliente: {summary}"})
        messages.extend(self.chat_repository.get_history(phone))
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": self.settings.llm_model_id,
            "messages": messages,
            "max_tokens": 600,
            "temperature": 0.7,
            "top_p": 1,
            "stream": False,
            "chat_template_kwargs": {"thinking": bool(thinking_enabled)},
        }
        text = await self._post(payload)
        if text:
            return text

        retry_payload = dict(payload)
        retry_payload.pop("chat_template_kwargs", None)
        retry_payload["max_tokens"] = 400
        text = await self._post(retry_payload)
        if text:
            return text
        raise RuntimeError("LLM response without usable content")

    async def _post(self, payload: dict[str, Any]) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.settings.llm_api_key}",
            "Accept": "application/json",
        }
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(self.settings.llm_api_url, headers=headers, json=payload)
            response.raise_for_status()
            return _extract_llm_text(response.json())


class EvolutionClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def send_typing(self, number: str, delay_ms: int = 900) -> None:
        if not self.settings.evolution_api_key or not self.settings.typing_enabled:
            return
        headers = {"Content-Type": "application/json", "apikey": self.settings.evolution_api_key}
        candidates = [
            (f"{self.settings.evolution_base_url}/chat/sendPresence/{self.settings.evolution_instance}", {"number": number, "presence": "composing", "delay": delay_ms}),
            (f"{self.settings.evolution_base_url}/chat/presence/{self.settings.evolution_instance}", {"number": number, "presence": "composing", "delay": delay_ms}),
            (f"{self.settings.evolution_base_url}/presence/set/{self.settings.evolution_instance}", {"number": number, "presence": "composing", "delay": delay_ms}),
        ]
        async with httpx.AsyncClient(timeout=2.5) as client:
            for url, payload in candidates:
                try:
                    resp = await client.post(url, headers=headers, json=payload)
                    if resp.status_code < 500:
                        return
                except Exception:
                    continue

    async def send_text(self, number: str, text: str) -> tuple[str, str | None]:
        if not self.settings.evolution_api_key:
            raise RuntimeError("EVOLUTION_API_KEY is missing")

        url = f"{self.settings.evolution_base_url}/message/sendText/{self.settings.evolution_instance}"
        headers = {"Content-Type": "application/json", "apikey": self.settings.evolution_api_key}
        payload = {"number": number, "text": text}
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                    body = response.json()
                provider_status = str(body.get("status") or "UNKNOWN")
                provider_id = ((body.get("key") or {}).get("id") if isinstance(body.get("key"), dict) else None)
                return provider_status, provider_id
            except Exception as exc:
                last_error = exc
                if attempt < 2:
                    await asyncio.sleep(0.5 * (attempt + 1))
        raise RuntimeError(f"Failed to send Evolution message: {last_error}")

    async def send_bubbles(self, number: str, text: str) -> None:
        parts = re.split(r"\n+|(?<=[.!?])\s+", text)
        parts = [p.strip() for p in parts if p.strip()]
        for part in parts:
            typing_ms = max(500, min(1200, len(part) * 12))
            await self.send_typing(number, delay_ms=typing_ms)
            await asyncio.sleep(typing_ms / 1000)
            chunks = [part[i : i + 500] for i in range(0, len(part), 500)] if len(part) > 500 else [part]
            for chunk in chunks:
                await self.send_text(number, chunk)
                await asyncio.sleep(random.uniform(0.2, 0.6))
