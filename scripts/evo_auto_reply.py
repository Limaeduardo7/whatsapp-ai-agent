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
logger = logging.getLogger("kimi-whatsapp-bridge")

# Evolution API config
EVOLUTION_BASE_URL = "https://automacoes-evolution-api.hpfunv.easypanel.host"
EVOLUTION_INSTANCE = "Eu"
EVOLUTION_API_KEY = "429683C4C977415CAAFCCE10F7D57E11"

# OpenAI API (Codex)
OPENAI_API_URL = os.getenv("LLM_API_URL", "http://localhost:18789/v1/chat/completions")
OPENAI_API_KEY = os.getenv("LLM_API_KEY", "b3859b235be8827edeb8261ee8bb83b465407fe76372e960")
MODEL_ID = os.getenv("LLM_MODEL_ID", "openai-codex/gpt-5.3-codex")
THINKING_LEVEL = "low"

# Gemini STT/Vision
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
GEMINI_STT_MODEL = "gemini-1.5-flash"

# Telegram config
TELEGRAM_BOT_TOKEN = "7551254700:AAGFSItZ0IlHLDfoWXIympuWIq0aZX61uo0"
TELEGRAM_CHAT_IDS = ["-1003795759440", "-3726083368", "-3833895713", "-3851840330"]

# Agent files directory
AGENTS_DIR = "/root/.openclaw/agents"
WORKSPACE_DIR = "/root/clawd"
OPENCLAW_CONFIG = "/root/.openclaw/openclaw.json"
CLIENTS_DIR = "/root/clawd/clients"

# Arquivos de persistência
MEMORY_FILE = "/root/clawd/scripts/chat_memory.json"
BLACKLIST_FILE = "/root/clawd/scripts/ignored_numbers.json"
AGENTS_CONFIG = "/root/clawd/scripts/agents_config.json"
LOG_FILE = "/root/clawd/scripts/kimi_logs.jsonl"
NOTIFY_QUEUE = "/root/clawd/scripts/notify_queue.jsonl"
FEED_FILE = "/root/clawd/scripts/intelligence_feed.jsonl"
DB_PATH = "/root/clawd/scripts/mission_control.db"
OWNER_NUMBER = "555491397178"

# Notion (Pipeline de Vendas)
NOTION_KEY_PATH = "/root/.config/notion/api_key"
NOTION_DATABASE_ID = "8c1781b9-a22e-4b16-8ff4-aa739b7eea05"
NOTION_DATASOURCE_ID = "434a45a3-9fd8-4bdd-993c-6752c91d9941"

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(stale_task_loop())
    # Follow-up automático pausado por decisão operacional (2026-03-01).
    # Mantemos apenas respostas reativas até nova liberação explícita.
    # asyncio.create_task(lead_followup_loop())

    # Polling fallback (findMessages) pode gerar efeitos colaterais em algumas
    # versões da Evolution/WA (ex.: antecipar leitura/estado de mensagens).
    # Por padrão fica DESLIGADO e só ativa com env explícita.
    if os.getenv("EVOLUTION_POLL_FALLBACK", "0").strip().lower() in ("1", "true", "yes", "on"):
        asyncio.create_task(poll_messages_loop())
        logger.info("poll_messages_loop enabled via EVOLUTION_POLL_FALLBACK")
    else:
        logger.info("poll_messages_loop disabled (webhook-only mode)")

# --- POLLING FALLBACK: busca mensagens novas via API a cada 10s ---
_poll_last_ts = [0]  # mutable container for last processed timestamp

async def poll_messages_loop():
    """Poll Evolution API for new inbound messages as fallback when webhooks fail."""
    await asyncio.sleep(10)  # wait for app to initialize
    headers = {"apikey": EVOLUTION_API_KEY, "Content-Type": "application/json"}
    logger.info("poll_messages_loop started")
    
    # Initialize with current timestamp to avoid processing old messages
    _poll_last_ts[0] = int(time.time())
    
    poll_interval = int(os.getenv("EVOLUTION_POLL_INTERVAL_SEC", "10"))

    while True:
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                payload = {
                    "where": {"key": {"fromMe": False}},
                    # A Evolution pode ignorar o filtro fromMe; aumentar o limit
                    # reduz risco de perder inbound quando há muitas mensagens enviadas pelo bot.
                    "limit": 1000
                }
                resp = await client.post(
                    f"{EVOLUTION_BASE_URL}/chat/findMessages/{EVOLUTION_INSTANCE}",
                    headers=headers, json=payload
                )
                if resp.status_code == 200:
                    data = resp.json()
                    records = data.get("messages", {}).get("records", [])
                    new_msgs = []
                    for rec in records:
                        ts = rec.get("messageTimestamp", 0)
                        if isinstance(ts, dict):
                            ts = ts.get("low", 0)
                        ts = int(ts) if ts else 0
                        if ts > _poll_last_ts[0]:
                            new_msgs.append(rec)
                    
                    if new_msgs:
                        # Sort by timestamp ascending
                        new_msgs.sort(key=lambda r: int(r.get("messageTimestamp", 0) if not isinstance(r.get("messageTimestamp"), dict) else r.get("messageTimestamp", {}).get("low", 0)))
                        max_ts = _poll_last_ts[0]
                        for rec in new_msgs:
                            ts = rec.get("messageTimestamp", 0)
                            if isinstance(ts, dict):
                                ts = ts.get("low", 0)
                            ts = int(ts) if ts else 0
                            if ts > max_ts:
                                max_ts = ts
                            
                            key = rec.get("key", {})
                            msg_id = key.get("id", "")
                            sender_jid = key.get("remoteJid", "")
                            
                            # Skip own messages (fromMe) — Evolution API ignores the filter
                            if key.get("fromMe", False):
                                continue
                            
                            # Skip if already processed via webhook
                            if msg_id and msg_id in recent_message_ids:
                                continue
                            
                            # Skip groups
                            if sender_jid.endswith("@g.us"):
                                continue
                            
                            msg = rec.get("message", {}) or {}
                            text = msg.get("conversation") or msg.get("extendedTextMessage", {}).get("text") or ""
                            push_name = rec.get("pushName", "")
                            
                            has_audio = bool(msg.get("audioMessage"))
                            has_image = bool(msg.get("imageMessage"))
                            
                            if not text and not has_audio and not has_image:
                                continue
                            
                            # Mark as seen
                            if msg_id:
                                recent_message_ids.append(msg_id)
                                if len(recent_message_ids) > 200:
                                    recent_message_ids[:] = recent_message_ids[-200:]
                            
                            logger.info(f"POLL: new message from {sender_jid}: {text[:50]}")
                            
                            # Save pushName
                            if push_name and sender_jid:
                                local_memory.setdefault(sender_jid, {"history": [], "lead": {"name": None, "business": None, "site_type": None, "budget": None, "deadline": None, "goal": None, "urgency": None, "stage": "novo"}, "summary": ""})
                                if not local_memory[sender_jid].get("lead", {}).get("name"):
                                    local_memory[sender_jid].setdefault("lead", {})["name"] = push_name.strip().title()
                                    save_data(MEMORY_FILE, local_memory)
                            
                            # Skip ignored
                            sender_number = sender_jid.split("@")[0]
                            if is_ignored_target(sender_number):
                                continue
                            
                            # Handle audio
                            audio_reply = False
                            image_bytes = None
                            image_mime = None
                            
                            if msg.get("audioMessage"):
                                audio_reply = True
                                audio = msg.get("audioMessage")
                                audio_url = audio.get("url")
                                audio_mime_type = audio.get("mimetype", "audio/ogg")
                                audio_bytes = await download_media(audio_url)
                                transcript = await gemini_transcribe_audio(audio_bytes, audio_mime_type)
                                if transcript:
                                    text = f"Transcrição de áudio: {transcript}"
                                else:
                                    text = "Recebi um áudio, mas não consegui transcrever."
                            
                            if msg.get("imageMessage"):
                                image = msg.get("imageMessage")
                                image_url = image.get("url")
                                image_mime = image.get("mimetype", "image/jpeg")
                                image_bytes = await download_media(image_url)
                                if not image_bytes:
                                    text = "Recebi uma imagem, mas não consegui acessar o arquivo."
                                elif not text:
                                    desc = await gemini_describe_image(image_bytes, image_mime)
                                    if desc:
                                        text = f"Descrição da imagem: {desc}"
                                    else:
                                        text = "Recebi uma imagem, mas não consegui analisar."
                            
                            if sender_jid and text:
                                await process_with_kimi(sender_jid, text, image_bytes=image_bytes, image_mime=image_mime, audio_reply=audio_reply)
                        
                        _poll_last_ts[0] = max_ts
                else:
                    logger.warning(f"Poll findMessages failed: {resp.status_code}")
        except Exception as e:
            logger.error(f"poll_messages_loop error: {e}")
        
        await asyncio.sleep(max(5, poll_interval))

# Habilita CORS para o Dashboard React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Em prod, restringir ao IP da VPS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Memórias
local_memory = {}
ignored_numbers = []
recent_message_ids = []
recent_message_hashes = []
# Anti-duplicação por conteúdo em janela curta (protege contra webhooks repetidos)
recent_inbound_cooldown = {}
notion_blacklist_cache = {}

# Números protegidos — NUNCA podem ser bloqueados
PROTECTED_NUMBERS = ["5554913917178", "5554991879262", "555491397178"]


def normalize_block_key(value: str) -> str:
    """Normaliza número/JID para comparação robusta de blacklist."""
    v = (value or "").strip()
    if not v:
        return ""
    if "@" in v:
        v = v.split("@")[0]
    # Mantém apenas dígitos para evitar falhas com +55, espaços, hífens etc.
    v = re.sub(r"\D", "", v)
    return v


def is_ignored_target(value: str) -> bool:
    key = normalize_block_key(value)
    if not key:
        return False
    if key in PROTECTED_NUMBERS:
        return False
    # Aceita lista antiga com JID completo e lista nova com número limpo
    return key in ignored_numbers or f"{key}@s.whatsapp.net" in ignored_numbers

def load_data():
    global local_memory, ignored_numbers, recent_message_ids, recent_message_hashes
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f: local_memory = json.load(f)
        except: local_memory = {}
    if os.path.exists(BLACKLIST_FILE):
        try:
            with open(BLACKLIST_FILE, "r") as f: ignored_numbers = json.load(f)
        except: ignored_numbers = []

    # Normaliza blacklist + remove protegidos
    normalized = []
    seen = set()
    for n in ignored_numbers:
        key = normalize_block_key(n)
        if not key or key in PROTECTED_NUMBERS or key in seen:
            continue
        seen.add(key)
        normalized.append(key)
    if normalized != ignored_numbers:
        ignored_numbers = normalized
        save_data(BLACKLIST_FILE, ignored_numbers)

    # Migração simples: se histórico antigo for lista, converte
    for jid, value in list(local_memory.items()):
        if isinstance(value, list):
            local_memory[jid] = {
                "history": value,
                "lead": {"name": None, "business": None, "site_type": None, "budget": None, "deadline": None, "stage": "novo"},
                "summary": ""
            }
        elif isinstance(value, dict):
            local_memory[jid].setdefault("history", [])
            local_memory[jid].setdefault("lead", {"name": None, "business": None, "site_type": None, "budget": None, "deadline": None, "stage": "novo"})
            local_memory[jid].setdefault("summary", "")

def save_data(filename, data):
    try:
        with open(filename, "w") as f: json.dump(data, f)
    except Exception as e: logger.error(f"Error saving {filename}: {e}")

def read_available_models():
    try:
        if not os.path.exists(OPENCLAW_CONFIG):
            return []
        with open(OPENCLAW_CONFIG, "r") as f:
            cfg = json.load(f)
        defaults = (cfg.get("agents") or {}).get("defaults") or {}
        models_map = defaults.get("models") or {}
        primary = (defaults.get("model") or {}).get("primary")
        models = set(list(models_map.keys()) + ([primary] if primary else []))
        return sorted([m for m in models if m])
    except Exception as e:
        logger.error(f"Read models failed: {e}")
        return []


def read_notion_key():
    try:
        if os.path.exists(NOTION_KEY_PATH):
            with open(NOTION_KEY_PATH, "r") as f:
                return f.read().strip()
    except Exception as e:
        logger.error(f"Read Notion key failed: {e}")
    return None


def notion_headers():
    key = read_notion_key()
    if not key:
        return None
    return {
        "Authorization": f"Bearer {key}",
        "Notion-Version": "2025-09-03",
        "Content-Type": "application/json",
    }


async def notion_find_lead_page_id(sender_jid: str):
    """Resolve Notion page id by WhatsApp field when local memory has no notion_page_id."""
    headers = notion_headers()
    if not headers:
        return None
    number = normalize_block_key(sender_jid)
    now = int(time.time())
    cache_key = number or sender_jid
    cached = notion_blacklist_cache.get(cache_key)
    if cached and (now - cached.get("ts", 0) < 300):
        return cached.get("page_id")

    candidates = [sender_jid]
    if number:
        candidates += [number, f"{number}@s.whatsapp.net", f"{number}@lid"]

    async with httpx.AsyncClient(timeout=20) as client:
        # tenta query com filtros OR no data source, depois database
        for base in [f"https://api.notion.com/v1/data-sources/{NOTION_DATASOURCE_ID}/query", f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"]:
            for c in candidates:
                payload = {
                    "filter": {"property": "WhatsApp", "rich_text": {"contains": c}},
                    "page_size": 10,
                }
                try:
                    resp = await client.post(base, headers=headers, json=payload)
                    if resp.status_code >= 300:
                        continue
                    data = resp.json() or {}
                    results = data.get("results") or []
                    if results:
                        pid = results[0].get("id")
                        notion_blacklist_cache[cache_key] = {"page_id": pid, "blocked": None, "ts": now}
                        return pid
                except Exception:
                    continue

    notion_blacklist_cache[cache_key] = {"page_id": None, "blocked": None, "ts": now}
    return None


def map_stage_to_funil(stage: str) -> str:
    s = (stage or "").lower()
    if s in ["novo", "lead"]:
        return "Lead"
    if s in ["qualificacao", "qualificação"]:
        return "Qualificação"
    if s == "proposta":
        return "Proposta"
    if s in ["negociacao", "negociação"]:
        return "Negociação"
    if s == "ganho":
        return "Ganho"
    if s == "perdido":
        return "Perdido"
    return "Lead"


def map_urgency_to_temp(urgency: str) -> str:
    u = (urgency or "").lower()
    if u == "alta":
        return "Quente"
    if u == "baixa":
        return "Frio"
    return "Morno"


def parse_budget_to_number(budget: str):
    if not budget:
        return None
    b = str(budget)
    m = re.findall(r"\d+", b)
    if not m:
        return None
    try:
        return float("".join(m))
    except Exception:
        return None


def _notion_prop_truthy(prop: dict) -> bool:
    """Best-effort detector for blacklist/bloqueio properties in Notion page payload."""
    if not isinstance(prop, dict):
        return False
    t = (prop.get("type") or "").lower()
    if t == "checkbox":
        return bool(prop.get("checkbox"))
    if t in ("select", "status"):
        obj = prop.get(t) or {}
        name = (obj.get("name") or "").lower()
        return any(k in name for k in ["blacklist", "bloque", "block"])
    if t == "multi_select":
        arr = prop.get("multi_select") or []
        joined = " ".join((x.get("name") or "").lower() for x in arr if isinstance(x, dict))
        return any(k in joined for k in ["blacklist", "bloque", "block"])
    if t in ("rich_text", "title"):
        arr = prop.get(t) or []
        txt = " ".join(((x.get("plain_text") or "") for x in arr if isinstance(x, dict))).lower()
        return any(k in txt for k in ["blacklist", "bloqueado", "bloqueada", "block"])
    return False


async def sync_blacklist_from_notion(sender_jid: str, state: dict) -> bool:
    """If lead is flagged as blocked/blacklist in Notion, enforce permanent local blacklist."""
    try:
        lead = (state or {}).get("lead") or {}
        page_id = lead.get("notion_page_id")
        if not page_id:
            page_id = await notion_find_lead_page_id(sender_jid)
            if page_id:
                lead["notion_page_id"] = page_id
                (state or {}).setdefault("lead", {}).update(lead)
                save_data(MEMORY_FILE, local_memory)

        if not page_id:
            return False

        headers = notion_headers()
        if not headers:
            return False

        number = normalize_block_key(sender_jid)
        cache_key = number or sender_jid
        now = int(time.time())
        cached = notion_blacklist_cache.get(cache_key)
        if cached and cached.get("page_id") == page_id and cached.get("blocked") is True and (now - cached.get("ts", 0) < 300):
            if number and number not in PROTECTED_NUMBERS and number not in ignored_numbers:
                ignored_numbers.append(number)
                ignored_numbers[:] = sorted(set(ignored_numbers))
                save_data(BLACKLIST_FILE, ignored_numbers)
            return True

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"https://api.notion.com/v1/pages/{page_id}", headers=headers)
            if resp.status_code >= 300:
                return False
            data = resp.json() or {}
            props = data.get("properties") or {}

            blocked = False
            for pname, prop in props.items():
                name_l = (pname or "").lower()
                has_block_name = any(k in name_l for k in ["blacklist", "bloque", "block"])
                t = (prop.get("type") or "").lower() if isinstance(prop, dict) else ""

                if t == "checkbox":
                    if has_block_name and bool(prop.get("checkbox")):
                        blocked = True
                        break
                else:
                    if _notion_prop_truthy(prop):
                        blocked = True
                        break

            notion_blacklist_cache[cache_key] = {"page_id": page_id, "blocked": blocked, "ts": now}

            if blocked:
                if number and number not in PROTECTED_NUMBERS and number not in ignored_numbers:
                    ignored_numbers.append(number)
                    ignored_numbers[:] = sorted(set(ignored_numbers))
                    save_data(BLACKLIST_FILE, ignored_numbers)
                return True
            return False
    except Exception as e:
        logger.error(f"sync_blacklist_from_notion error: {e}")
        return False



async def notion_create_or_update_lead(sender_jid: str, lead: dict, is_new: bool):
    headers = notion_headers()
    if not headers:
        return
    lead = lead or {}
    title = lead.get("name") or sender_jid
    funil = map_stage_to_funil(lead.get("stage"))
    temp = map_urgency_to_temp(lead.get("urgency"))
    budget_num = parse_budget_to_number(lead.get("budget"))

    properties = {
        "Deal": {"title": [{"text": {"content": title}}]},
        "WhatsApp": {"rich_text": [{"text": {"content": sender_jid}}]},
        "Canal": {"select": {"name": "WhatsApp"}},
        "Etapa do Funil": {"select": {"name": funil}},
        "Temperatura": {"select": {"name": temp}},
        "Agente Responsável": {"select": {"name": "Crustáceo (CEO)"}},
        "Status": {"select": {"name": "Em andamento"}},
        "Último Contato": {"date": {"start": time.strftime("%Y-%m-%d")}},
    }

    if budget_num is not None:
        properties["Valor Estimado"] = {"number": budget_num}

    notion_page_id = lead.get("notion_page_id")

    async with httpx.AsyncClient(timeout=15) as client:
        if is_new or not notion_page_id:
            payload = {"parent": {"database_id": NOTION_DATABASE_ID}, "properties": properties}
            resp = await client.post("https://api.notion.com/v1/pages", headers=headers, json=payload)
            if resp.status_code >= 200 and resp.status_code < 300:
                data = resp.json()
                page_id = data.get("id")
                if page_id:
                    lead["notion_page_id"] = page_id
            else:
                logger.error(f"Notion create lead failed: {resp.status_code} {resp.text}")
        else:
            payload = {"properties": properties}
            resp = await client.patch(f"https://api.notion.com/v1/pages/{notion_page_id}", headers=headers, json=payload)
            if resp.status_code >= 300:
                logger.error(f"Notion update lead failed: {resp.status_code} {resp.text}")

def client_md_path(sender_jid: str) -> str:
    safe = sender_jid.replace("@", "_at_").replace("/", "_")
    return os.path.join(CLIENTS_DIR, f"{safe}.md")


def read_client_md(sender_jid: str) -> str:
    try:
        if not os.path.exists(CLIENTS_DIR):
            os.makedirs(CLIENTS_DIR, exist_ok=True)
        path = client_md_path(sender_jid)
        if not os.path.exists(path):
            return ""
        with open(path, "r") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Read client md failed: {e}")
        return ""


def current_greeting() -> str:
    h = time.localtime().tm_hour
    if h < 12:
        return "Bom dia"
    if h < 18:
        return "Boa tarde"
    return "Boa noite"


def format_reply(state: dict, text: str) -> str:
    cleaned = (text or "").replace("**", "").replace("*", "").strip()
    if not cleaned:
        return cleaned
    return cleaned


def detect_business_profile(lead: dict, history: list) -> str:
    """Classifica perfil comercial do lead para personalizar abordagem inicial."""
    lead = lead or {}
    text = " ".join([str((h or {}).get("content", "")) for h in (history or [])]).lower()
    business = (lead.get("business") or "").lower()
    goal = (lead.get("goal") or "").lower()
    corpus = f"{business} {goal} {text}"

    if any(k in corpus for k in ["loja", "ecommerce", "e-commerce", "catálogo", "catalogo", "checkout", "produto"]):
        return "ecommerce"
    if any(k in corpus for k in ["médico", "medico", "clínica", "clinica", "advogado", "advocacia", "consultório", "consultorio", "arquitet", "engenhar"]):
        return "servico_local"
    if any(k in corpus for k in ["lançamento", "lancamento", "tráfego", "trafego", "campanha", "mentor", "infoproduto", "curso"]):
        return "marketing_infoproduto"
    if any(k in corpus for k in ["sistema", "app", "software", "automação", "automacao", "ia", "api", "integra"]):
        return "projeto_complexo"
    return "geral"


def greeting_by_profile(profile: str, lead_name: str = None) -> str:
    name = (lead_name or "").strip().split(" ")[0]
    voc = f", {name}" if name else ""
    if profile == "ecommerce":
        return f"Olá{voc}! Vi que seu foco parece ser vendas online. Te ajudo a estruturar uma loja que converte sem complicação."
    if profile == "servico_local":
        return f"Olá{voc}! Pelo seu perfil, o foco é captar clientes com autoridade local. Posso te orientar no melhor formato de site para isso."
    if profile == "marketing_infoproduto":
        return f"Olá{voc}! Entendi um perfil mais de campanha e conversão. Posso te recomendar uma estrutura de página focada em resultado."
    if profile == "projeto_complexo":
        return f"Olá{voc}! Entendi que seu caso envolve algo mais técnico. Posso te guiar pelo escopo ideal para sair com uma proposta assertiva."
    return f"Olá{voc}! Me conta em uma frase o objetivo principal do seu site para eu te recomendar o melhor formato."

def detect_complex_site(state: dict) -> bool:
    keywords = ["sistema", "login", "área logada", "match", "catálogo", "loja", "checkout", "pagamento", "integra", "automação"]
    text = " ".join([h.get("content", "") for h in (state.get("history") or [])]).lower()
    return any(k in text for k in keywords)


def generate_quote_pdf(sender_jid: str, state: dict) -> bytes:
    prazo = "até 2 semanas" if detect_complex_site(state) else "até 3 dias"
    lead = state.get("lead", {}) or {}
    escopo = lead.get("site_type") or state.get("summary") or "Desenvolvimento de site"
    valor = lead.get("budget") or "a definir"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "ORÇAMENTO", ln=1)
    pdf.cell(0, 8, f"Cliente: {sender_jid}", ln=1)
    pdf.ln(2)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 6, f"Objeto: {escopo}")
    pdf.ln(1)
    pdf.multi_cell(0, 6, f"Prazo de entrega: {prazo}")
    pdf.multi_cell(0, 6, f"Valor: {valor}")
    pdf.ln(4)
    pdf.multi_cell(0, 6, "Condições: 50% na contratação e 50% na entrega.")
    pdf.ln(2)
    pdf.multi_cell(0, 6, "PIX CNPJ: 58068737000126")
    return pdf.output(dest="S").encode("latin-1")


def render_client_md(sender_jid: str, state: dict) -> str:
    lead = state.get("lead", {}) or {}
    summary = state.get("summary", "")
    history = state.get("history", [])[-12:]
    hist_lines = []
    for h in history:
        role = h.get("role", "")
        content = (h.get("content") or "").replace("\n", " ")
        hist_lines.append(f"- {role}: {content}")
    return (
        f"# Cliente {sender_jid}\n\n"
        f"## Resumo\n{summary or '—'}\n\n"
        f"## Preferências/Lead\n"
        f"- nome: {lead.get('name') or '—'}\n"
        f"- negócio: {lead.get('business') or '—'}\n"
        f"- tipo_site: {lead.get('site_type') or '—'}\n"
        f"- orçamento: {lead.get('budget') or '—'}\n"
        f"- prazo: {lead.get('deadline') or '—'}\n"
        f"- estágio: {lead.get('stage') or '—'}\n\n"
        f"## Follow-up\n"
        f"- aguardando_resposta: {state.get('awaiting_response', False)}\n"
        f"- ultima_pergunta: {state.get('last_question_text') or '—'}\n"
        f"- ultima_entrada_ts: {state.get('last_inbound_at') or '—'}\n"
        f"- pausado: {state.get('paused', False)}\n\n"
        f"## Histórico recente\n" + ("\n".join(hist_lines) if hist_lines else "- —") + "\n"
    )


def write_client_md(sender_jid: str, state: dict):
    try:
        if not os.path.exists(CLIENTS_DIR):
            os.makedirs(CLIENTS_DIR, exist_ok=True)
        path = client_md_path(sender_jid)
        with open(path, "w") as f:
            f.write(render_client_md(sender_jid, state))
    except Exception as e:
        logger.error(f"Write client md failed: {e}")


load_data()

# --- UTIL ---
def normalize_evolution_target(target: str) -> str:
    """
    Evolution send endpoints esperam número limpo (sem sufixo @...) ou o JID completo se for LID/Group.
    Se for @s.whatsapp.net, remove o sufixo.
    Se for @lid, mantém o sufixo (dependendo da versão da API, mas remover costuma quebrar envio para LIDs).
    Para garantir, vamos tentar manter o sufixo se for @lid, ou remover se for @s.whatsapp.net.
    
    Update 2026-02-13: Logs mostram 400 Bad Request para alvos que parecem LIDs (ex: 242949187195101).
    A Evolution API v2 geralmente precisa do JID completo se não for um número padrão.
    Vamos ajustar para:
    1. Se tiver @lid, mantém TUDO.
    2. Se tiver @g.us (grupo), mantém TUDO.
    3. Se tiver @s.whatsapp.net, remove o sufixo (comportamento padrão para números).
    4. Se não tiver @, assume que é número limpo.
    """
    t = (target or "").strip()
    if "@lid" in t:
        return t # Mantém JID completo para LID
    if "@g.us" in t:
        return t # Mantém JID completo para Grupo
    if "@s.whatsapp.net" in t:
        return t.split("@")[0] # Remove sufixo para números normais
    return t # Retorna como está (assumindo número limpo)


def start_composing(target: str) -> asyncio.Event:
    """Inicia loop de 'digitando...' que roda até o evento ser setado"""
    stop = asyncio.Event()

    # Mitigação: em alguns cenários o sendPresence pode impactar estado de leitura.
    # Default OFF; habilitar somente com EVOLUTION_SEND_PRESENCE=1.
    presence_enabled = os.getenv("EVOLUTION_SEND_PRESENCE", "0").strip().lower() in ("1", "true", "yes", "on")
    if not presence_enabled:
        return stop

    async def _loop():
        headers = {"Content-Type": "application/json", "apikey": EVOLUTION_API_KEY}
        number = normalize_evolution_target(target)
        async with httpx.AsyncClient(timeout=10) as client:
            while not stop.is_set():
                try:
                    resp = await client.post(
                        f"{EVOLUTION_BASE_URL}/chat/sendPresence/{EVOLUTION_INSTANCE}",
                        json={"number": number, "presence": "composing", "delay": 5000},
                        headers=headers
                    )
                    if resp.status_code == 400 and number != target:
                        await client.post(
                            f"{EVOLUTION_BASE_URL}/chat/sendPresence/{EVOLUTION_INSTANCE}",
                            json={"number": target, "presence": "composing", "delay": 5000},
                            headers=headers
                        )
                except Exception as e:
                    logger.error(f"Composing error: {e}")
                try:
                    await asyncio.wait_for(stop.wait(), timeout=4)
                    break
                except asyncio.TimeoutError:
                    pass
    asyncio.create_task(_loop())
    return stop

async def send_whatsapp_text(target: str, text: str):
    number = normalize_evolution_target(target)
    if is_ignored_target(number):
        return
    headers = {"Content-Type": "application/json", "apikey": EVOLUTION_API_KEY}
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            payloads = [{"number": number, "text": text, "delay": 0}]
            if number != target:
                payloads.append({"number": target, "text": text, "delay": 0})

            for payload in payloads:
                last_status = None
                for attempt in range(2):
                    resp = await client.post(
                        f"{EVOLUTION_BASE_URL}/message/sendText/{EVOLUTION_INSTANCE}",
                        json=payload,
                        headers=headers
                    )
                    last_status = resp.status_code
                    if resp.status_code in (200, 201):
                        return
                    if resp.status_code >= 500 and attempt == 0:
                        await asyncio.sleep(0.7)
                        continue
                    break
                logger.warning(f"sendText failed status={last_status} target={payload.get('number')}")
        except Exception as e:
            logger.error(f"Error: {e}")

async def send_bubbles(target: str, text: str):
    """Envia texto em balões. Regra comercial atual: 1 balão por resposta para evitar spam."""
    raw = (text or "").replace("\r\n", "\n").strip()
    if not raw:
        return

    def split_parts(s: str, max_chars: int = 180):
        parts = []
        blocks = [b.strip() for b in re.split(r"\n{2,}", s) if b.strip()]
        if not blocks:
            blocks = [s]

        for block in blocks:
            # Preserva listas/linhas quando existirem
            lines = [ln.strip() for ln in block.split("\n") if ln.strip()]
            if len(lines) > 1:
                for ln in lines:
                    if len(ln) <= max_chars:
                        parts.append(ln)
                    else:
                        parts.extend([ln[i:i+max_chars].strip() for i in range(0, len(ln), max_chars)])
                continue

            sentences = [x.strip() for x in re.split(r"(?<=[.!?…])\s+", block) if x.strip()]
            if not sentences:
                sentences = [block]

            current = ""
            for sent in sentences:
                chunks = [sent] if len(sent) <= max_chars else [sent[i:i+max_chars].strip() for i in range(0, len(sent), max_chars)]
                for chunk in chunks:
                    if not current:
                        current = chunk
                    elif len(current) + 1 + len(chunk) <= max_chars:
                        current = f"{current} {chunk}"
                    else:
                        parts.append(current)
                        current = chunk
            if current:
                parts.append(current)

        return [p for p in parts if p]

    parts = split_parts(raw)
    if not parts:
        parts = [raw]

    # Hard cap: não disparar múltiplas mensagens em sequência para o mesmo turno
    # Mantém apenas 1 resposta curta por vez.
    parts = [parts[0][:260].strip()]

    number = normalize_evolution_target(target)
    headers_ev = {"Content-Type": "application/json", "apikey": EVOLUTION_API_KEY}

    presence_enabled = os.getenv("EVOLUTION_SEND_PRESENCE", "0").strip().lower() in ("1", "true", "yes", "on")

    for i, part in enumerate(parts):
        typing_s = max(0.9, min(len(part) * 0.045, 3.2))
        if presence_enabled:
            async with httpx.AsyncClient(timeout=10) as client:
                try:
                    await client.post(
                        f"{EVOLUTION_BASE_URL}/chat/sendPresence/{EVOLUTION_INSTANCE}",
                        json={"number": number, "presence": "composing", "delay": int(typing_s * 1000)},
                        headers=headers_ev
                    )
                except Exception:
                    pass
        await asyncio.sleep(typing_s)
        await send_whatsapp_text(target, part)
        if i < len(parts) - 1:
            await asyncio.sleep(0.6)


async def send_whatsapp_audio(target: str, audio_bytes: bytes, mime: str = "audio/ogg"):
    if not audio_bytes: return
    number = normalize_evolution_target(target)
    if is_ignored_target(number):
        return
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    payload = {"number": number, "audio": audio_b64, "mimetype": mime, "ptt": True, "delay": 0}
    headers = {"Content-Type": "application/json", "apikey": EVOLUTION_API_KEY}
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            resp = await client.post(f"{EVOLUTION_BASE_URL}/message/sendAudio/{EVOLUTION_INSTANCE}", json=payload, headers=headers)
            if resp.status_code == 400 and number != target:
                await client.post(
                    f"{EVOLUTION_BASE_URL}/message/sendAudio/{EVOLUTION_INSTANCE}",
                    json={"number": target, "audio": audio_b64, "mimetype": mime, "ptt": True, "delay": 0},
                    headers=headers
                )
        except Exception as e:
            logger.error(f"Error sending audio: {e}")


async def send_whatsapp_document(target: str, file_bytes: bytes, filename: str = "orcamento.pdf", mime: str = "application/pdf"):
    if not file_bytes: return
    number = normalize_evolution_target(target)
    if is_ignored_target(number):
        return
    file_b64 = base64.b64encode(file_bytes).decode("utf-8")
    payload = {"number": number, "document": file_b64, "mimetype": mime, "fileName": filename, "delay": 0}
    headers = {"Content-Type": "application/json", "apikey": EVOLUTION_API_KEY}
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            resp = await client.post(f"{EVOLUTION_BASE_URL}/message/sendDocument/{EVOLUTION_INSTANCE}", json=payload, headers=headers)
            if resp.status_code == 400 and number != target:
                resp = await client.post(
                    f"{EVOLUTION_BASE_URL}/message/sendDocument/{EVOLUTION_INSTANCE}",
                    json={"number": target, "document": file_b64, "mimetype": mime, "fileName": filename, "delay": 0},
                    headers=headers
                )
            if resp.status_code == 404:
                alt_payload = {"number": number, "media": file_b64, "mimetype": mime, "fileName": filename, "delay": 0}
                await client.post(f"{EVOLUTION_BASE_URL}/message/sendMedia/{EVOLUTION_INSTANCE}", json=alt_payload, headers=headers)
        except Exception as e:
            logger.error(f"Error sending document: {e}")

def tts_ptbr_male(text: str) -> bytes:
    try:
        tts = gTTS(text=text, lang='pt')
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        return buf.getvalue()
    except Exception as e:
        logger.error(f"TTS error: {e}")
        return b""

def log_event(event: dict):
    try:
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.error(f"Error logging: {e}")

def enqueue_notify(event: dict):
    try:
        with open(NOTIFY_QUEUE, "a") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.error(f"Error enqueue notify: {e}")

# --- DB ---

def db_conn():
    return sqlite3.connect(DB_PATH)


def create_task(title: str, description: str = "", agent: str = "jarvis", status: str = "todo"):
    if not title:
        return None
    data = {"agents": [], "tasks": []}
    if os.path.exists(AGENTS_CONFIG):
        try:
            with open(AGENTS_CONFIG, "r") as f:
                data = json.load(f)
        except Exception:
            data = {"agents": [], "tasks": []}

    now_ms = int(time.time() * 1000)
    task = {"id": f"t{now_ms}", "title": title, "description": description, "agent": agent, "status": status, "created_at": now_ms, "updated_at": now_ms}
    data.setdefault("tasks", []).append(task)
    save_data(AGENTS_CONFIG, data)
    try:
        with db_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO tasks (id, title, description, agent, status, updated_at) VALUES (?,?,?,?,?,?)",
                (task.get("id"), task.get("title"), task.get("description"), task.get("agent"), task.get("status"), task.get("updated_at"))
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Task insert error: {e}")
    return task


def update_task_status(task_id: str = None, title: str = None, status: str = None, agent: str = None):
    if not status:
        return False
    if not os.path.exists(AGENTS_CONFIG):
        return False
    try:
        with open(AGENTS_CONFIG, "r") as f:
            data = json.load(f)
    except Exception:
        data = {"agents": [], "tasks": []}

    tasks = data.get("tasks") or []
    updated = False
    now_ms = int(time.time() * 1000)
    for t in tasks:
        if task_id and t.get("id") == task_id:
            t.setdefault("created_at", now_ms)
            t["status"] = status
            t["updated_at"] = now_ms
            if status == "done":
                t["completed_at"] = now_ms
            if agent:
                t["agent"] = agent
            updated = True
            break
        if title and t.get("title") and t.get("title").strip().lower() == title.strip().lower():
            t.setdefault("created_at", now_ms)
            t["status"] = status
            t["updated_at"] = now_ms
            if status == "done":
                t["completed_at"] = now_ms
            if agent:
                t["agent"] = agent
            updated = True
            break

    if updated:
        data["tasks"] = tasks
        save_data(AGENTS_CONFIG, data)
        try:
            with db_conn() as conn:
                cur = conn.cursor()
                for t in tasks:
                    cur.execute(
                        "INSERT INTO tasks (id, title, description, agent, status, updated_at) VALUES (?,?,?,?,?,?) "
                        "ON CONFLICT(id) DO UPDATE SET title=excluded.title, description=excluded.description, agent=excluded.agent, status=excluded.status, updated_at=excluded.updated_at",
                        (t.get("id"), t.get("title"), t.get("description"), t.get("agent"), t.get("status"), t.get("updated_at"))
                    )
                conn.commit()
        except Exception as e:
            logger.error(f"Task DB sync error: {e}")
    return updated

STALE_TASK_MINUTES = 120
LEAD_FOLLOWUP_HOURS = 5


def add_lead_task(sender_jid: str, first_message: str):
    # Desabilitado: não criar tarefas automáticas de lead no kanban
    return


def check_stale_tasks():
    if not os.path.exists(AGENTS_CONFIG):
        return
    try:
        with open(AGENTS_CONFIG, "r") as f:
            data = json.load(f)
    except Exception:
        return

    tasks = data.get("tasks") or []
    now_ms = int(time.time() * 1000)
    changed = False
    for t in tasks:
        if t.get("status") != "in_progress":
            continue
        updated_at = t.get("updated_at") or t.get("created_at")
        if not updated_at:
            continue
        delta_min = (now_ms - updated_at) / 60000
        if delta_min >= STALE_TASK_MINUTES:
            last_alert = t.get("alerted_at")
            if not last_alert or (now_ms - last_alert) / 60000 >= STALE_TASK_MINUTES:
                agent_name = (t.get("agent") or "").upper()
                title = t.get("title") or "Tarefa"
                # Desativado por solicitação do Eduardo: alertas de tarefa parada
                # asyncio.create_task(send_telegram_message(f"[KANBAN] ⏱️ Tarefa parada: {title} ({agent_name})"))
                t["alerted_at"] = now_ms
                changed = True

    if changed:
        data["tasks"] = tasks
        save_data(AGENTS_CONFIG, data)


async def stale_task_loop():
    while True:
        try:
            check_stale_tasks()
        except Exception as e:
            logger.error(f"Stale task loop error: {e}")
        await asyncio.sleep(1800)

async def generate_smart_followup(sender_jid: str, state: dict, followup_count: int) -> str:
    lead = state.get("lead", {})
    summary = state.get("summary", "")
    # Pega histórico recente para contexto, mas remove mensagens muito antigas
    history_raw = state.get("history", [])
    last_context = history_raw[-4:] if len(history_raw) > 0 else []

    # Matriz de estratégia baseada no contador de tentativas
    strategy = "Reengajamento leve. Pergunte se ficou alguma dúvida técnica ou sobre o processo."
    if followup_count == 2:
        strategy = "Oferecer alternativa (downsell) ou perguntar se o valor ficou acima do esperado. Focar em custo-benefício."
    elif followup_count == 3:
        strategy = "Prova social (mencionar que entregou projetos similares recentemente) ou escassez leve de agenda."
    elif followup_count >= 4:
        strategy = "Break-up cordial. Avisar que vai parar de mandar mensagem para não incomodar, mas deixar a porta aberta caso mudem de ideia no futuro."

    system_prompt = (
        "Você é o Eduardo Lima, especialista em sites. O lead parou de responder.\n"
        f"Estratégia de Follow-up (Tentativa {followup_count}/4): {strategy}\n"
        "Objetivo: Gerar uma mensagem de follow-up curta, ultra-natural (parecendo digitada por humano) e persuasiva. Máximo 2 frases curtas.\n"
        "NÃO comece com 'Olá' ou saudações formais se já conversaram. Vá direto ao ponto.\n"
        "NÃO pareça desesperado. Agregue valor ou tire dúvida.\n"
        f"Dados do Lead: {json.dumps(lead, ensure_ascii=False)}\n"
        f"Resumo da conversa: {summary}"
    )

    messages = [{"role": "system", "content": system_prompt}]
    # Adiciona contexto limpo
    for h in last_context:
        messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    
    messages.append({"role": "user", "content": "O lead não respondeu. Gere a mensagem de follow-up seguindo a estratégia."})

    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": MODEL_ID, "messages": messages, "temperature": 0.5, "max_tokens": 150}

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(OPENAI_API_URL, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                choice0 = (data.get('choices') or [{}])[0]
                msg_obj = choice0.get('message') or {}
                content = msg_obj.get('content') or choice0.get('text') or msg_obj.get('reasoning_content')
                return content.strip() if content else None
        except Exception as e:
            logger.error(f"Error generating smart followup: {e}")
    return None

async def lead_followup_loop():
    while True:
        try:
            now_ms = int(time.time() * 1000)
            local_time = time.localtime()
            # Janela estendida: 09:00 as 11:00 e 14:00 as 16:00 (evita almoço e noite)
            is_morning = (local_time.tm_hour >= 9 and local_time.tm_hour < 11)
            is_afternoon = (local_time.tm_hour >= 14 and local_time.tm_hour < 16)
            
            # TODO: Em produção, descomentar a verificação de horário.
            # Para testes imediatos, podemos permitir rodar se for invocado manualmente ou manter a janela.
            if is_morning or is_afternoon:
                for jid, state in local_memory.items():
                    if not state.get("awaiting_response"):
                        continue
                    
                    if state.get("paused"):
                        continue

                    last_in = state.get("last_inbound_at") or 0
                    last_follow = state.get("last_followup_at") or 0
                    followup_count = state.get("followup_count", 0)

                    # Limite de 4 tentativas
                    if followup_count >= 4:
                        state["awaiting_response"] = False
                        save_data(MEMORY_FILE, local_memory)
                        write_client_md(jid, state)
                        continue

                    # Verifica intervalo (24h desde ultima interação ou follow-up)
                    # day_start_ms lógica removida em favor de intervalo de 24h relativo
                    if (now_ms - max(last_in, last_follow)) < 24 * 3600 * 1000:
                        continue

                    # Gera mensagem inteligente
                    logger.info(f"Generating smart followup for {jid} (Count: {followup_count + 1})")
                    smart_msg = await generate_smart_followup(jid, state, followup_count + 1)
                    
                    if not smart_msg:
                        # Fallback simples
                        smart_msg = "Oi! Você ainda tem interesse em desenvolver seu site profissional?"
                        if followup_count >= 3:
                            smart_msg = "Oi! Vou encerrar seu atendimento por aqui para não incomodar. Se precisar no futuro, é só chamar."

                    followup = format_reply(state, smart_msg)
                    
                    await send_bubbles(jid, followup)
                    
                    state["last_followup_at"] = now_ms
                    state["followup_count"] = followup_count + 1
                    # Se for break-up (4), para de esperar
                    if state["followup_count"] >= 4:
                        state["awaiting_response"] = False
                        
                    save_data(MEMORY_FILE, local_memory)
                    write_client_md(jid, state)
                    logger.info(f"Follow-up sent to {jid}: {smart_msg}")
            
        except Exception as e:
            logger.error(f"Lead followup loop error: {e}")
        # Roda a cada 30 minutos
        await asyncio.sleep(1800)


def init_db():
    try:
        with db_conn() as conn:
            cur = conn.cursor()
            cur.execute("""
              CREATE TABLE IF NOT EXISTS feed (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time INTEGER,
                agent TEXT,
                text TEXT,
                type TEXT
              )
            """)
            cur.execute("""
              CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                agent TEXT,
                status TEXT,
                updated_at INTEGER
              )
            """)
            cur.execute("""
              CREATE TABLE IF NOT EXISTS context_store (
                key TEXT PRIMARY KEY,
                value TEXT,
                agent TEXT,
                updated_at INTEGER
              )
            """)
            conn.commit()
    except Exception as e:
        logger.error(f"DB init error: {e}")

init_db()

# migrate legacy feed jsonl -> sqlite (best-effort)
if os.path.exists(FEED_FILE):
    try:
        with db_conn() as conn:
            cur = conn.cursor()
            with open(FEED_FILE, "r") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        ev = json.loads(line)
                        cur.execute(
                            "INSERT INTO feed (time, agent, text, type) VALUES (?,?,?,?)",
                            (ev.get("time"), ev.get("from"), ev.get("text"), ev.get("type"))
                        )
                    except Exception:
                        continue
            conn.commit()
        os.rename(FEED_FILE, FEED_FILE + ".migrated")
    except Exception as e:
        logger.error(f"Feed migration error: {e}")

def feed_append(event: dict):
    try:
        with db_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO feed (time, agent, text, type) VALUES (?,?,?,?)",
                (event.get("time"), event.get("from"), event.get("text"), event.get("type"))
            )
            # Mantém apenas as últimas 200 mensagens no feed
            cur.execute("DELETE FROM feed WHERE id NOT IN (SELECT id FROM feed ORDER BY time DESC LIMIT 200)")
            conn.commit()
    except Exception as e:
        logger.error(f"Error feed append: {e}")

def detect_intent(text: str):
    t = text.lower()
    if any(k in t for k in ["preço", "valor", "quanto", "orçamento", "custa"]): return "preco"
    if any(k in t for k in ["prazo", "quando", "tempo", "entrega"]): return "prazo"
    if any(k in t for k in ["pagamento", "pix", "entrada", "parcel"]): return "pagamento"
    if any(k in t for k in ["software", "aplicativo", "app", "sistema", "automação", "automacao", "ia", "inteligência artificial", "inteligencia artificial", "chatbot", "api", "integração", "integracao", "complexo"]): return "complexo"
    if any(k in t for k in ["loja", "ecommerce", "nuvemshop"]): return "loja"
    if any(k in t for k in ["site", "landing", "lp", "pagina", "página"]): return "site"
    if any(k in t for k in ["portfólio", "portfolio", "exemplos", "cases"]): return "portfolio"
    if any(k in t for k in ["fechar", "quero", "vamos", "contratar", "pode iniciar", "iniciar"]): return "fechamento"
    return "geral"

def update_lead_profile(lead: dict, text: str):
    t = text.lower()
    # Nome
    m = re.search(r"me chamo ([\w\s]+)", t)
    if m: lead["name"] = m.group(1).strip().title()
    # Negócio
    m = re.search(r"tenho (uma|um) ([\w\s]+)", t)
    if m: lead["business"] = m.group(2).strip().title()
    # Objetivo
    if any(k in t for k in ["quero", "busco", "preciso", "gostaria"]):
        lead["goal"] = text.strip()
    # Urgência
    if any(k in t for k in ["urgente", "o quanto antes", "pra ontem"]):
        lead["urgency"] = "alta"
    elif any(k in t for k in ["sem pressa", "tranquilo", "pode demorar"]):
        lead["urgency"] = "baixa"
    # Tipo de site
    if "nuvemshop" in t or "ecommerce" in t or "loja" in t: lead["site_type"] = "loja"
    elif "landing" in t or "lp" in t or "página única" in t: lead["site_type"] = "lp"
    elif "site" in t or "páginas" in t: lead["site_type"] = "multiplo"
    # Orçamento
    m = re.search(r"(\d{2,5})", t)
    if m:
        lead["budget"] = f"R$ {m.group(1)}"
    # Prazo
    m = re.search(r"(\d+\s*(dias|semanas|meses))", t)
    if m: lead["deadline"] = m.group(1)
    return lead

def analyze_sentiment(text: str) -> dict:
    """Keyword-based sentiment analysis for Portuguese WhatsApp messages."""
    t = text.lower()
    score = 0  # -5 to +5

    # Positive signals
    positive = ["obrigado", "obrigada", "gostei", "adorei", "perfeito", "ótimo", "otimo", "excelente",
                "incrível", "incrivel", "top", "show", "maravilh", "amei", "parabéns", "parabens",
                "sensacional", "massa", "legal", "demais", "bom", "boa", "sim", "quero", "vamos",
                "animado", "empolgad", "feliz", "contente", "satisfeit"]
    negative = ["ruim", "péssimo", "pessimo", "horrível", "horrivel", "lixo", "caro", "absurdo",
                "ridículo", "ridiculo", "nunca", "jamais", "desisto", "cancelar", "devolver",
                "reclamar", "reclamação", "insatisfeit", "decepcion", "frustrad", "raiva",
                "irritad", "bravo", "chateado", "triste", "pior"]
    urgent = ["urgente", "o quanto antes", "pra ontem", "correndo", "emergência", "emergencia",
              "rápido", "rapido", "preciso agora", "imediato"]
    confused = ["não entendi", "nao entendi", "confuso", "como assim", "???", "não sei",
                "nao sei", "explica", "dúvida", "duvida", "perdido"]

    for w in positive:
        if w in t: score += 1
    for w in negative:
        if w in t: score -= 1
    for w in urgent:
        if w in t: score -= 0.5
    for w in confused:
        if w in t: score -= 0.3

    # Exclamation/caps intensity
    if t.count("!") >= 3: score += 0.5 if score >= 0 else -0.5
    if text.isupper() and len(text) > 5: score -= 1  # shouting = frustration

    # Clamp
    score = max(-5, min(5, round(score, 1)))

    # Classify
    if score >= 2: sentiment = "muito_positivo"
    elif score >= 0.5: sentiment = "positivo"
    elif score > -0.5: sentiment = "neutro"
    elif score > -2: sentiment = "negativo"
    else: sentiment = "frustrado"

    # Detect confusion separately
    is_confused = any(w in t for w in confused)

    return {"sentiment": sentiment, "score": score, "confused": is_confused}


def compact_history(state: dict, keep: int = 40, threshold: int = 80, max_summary_chars: int = 4000):
    history = state.get("history", [])
    if len(history) <= threshold:
        return
    older = history[:-keep]
    summary_lines = []
    for h in older:
        role = "U" if h.get("role") == "user" else "A"
        content = re.sub(r"\s+", " ", str(h.get("content", ""))).strip()
        if len(content) > 200:
            content = content[:200] + "..."
        if content:
            summary_lines.append(f"{role}: {content}")
    if summary_lines:
        summary = (state.get("summary") or "").strip()
        summary = (summary + "\n" + "\n".join(summary_lines)).strip()
        if len(summary) > max_summary_chars:
            summary = summary[-max_summary_chars:]
        state["summary"] = summary
    state["history"] = history[-keep:]

async def download_media(url: str):
    if not url: return None
    headers = {"apikey": EVOLUTION_API_KEY}
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                return resp.content
        except Exception as e:
            logger.error(f"Error downloading media: {e}")
    return None

async def gemini_transcribe_audio(audio_bytes: bytes, mime_type: str = "audio/ogg"):
    if not GEMINI_API_KEY or not audio_bytes:
        return None
    data_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": "Transcreva o áudio em português, mantendo nomes e números."},
                    {"inline_data": {"mime_type": mime_type, "data": data_b64}}
                ]
            }
        ]
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_STT_MODEL}:generateContent?key={GEMINI_API_KEY}"
    async with httpx.AsyncClient(timeout=120) as client:
        try:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            logger.error(f"Gemini STT error: {e}")
    return None

async def gemini_describe_image(image_bytes: bytes, mime_type: str = "image/jpeg"):
    if not GEMINI_API_KEY or not image_bytes:
        return None
    data_b64 = base64.b64encode(image_bytes).decode("utf-8")
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": "Descreva a imagem de forma objetiva, destacando detalhes relevantes para um atendimento comercial de criação de site."},
                    {"inline_data": {"mime_type": mime_type, "data": data_b64}}
                ]
            }
        ]
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_STT_MODEL}:generateContent?key={GEMINI_API_KEY}"
    async with httpx.AsyncClient(timeout=120) as client:
        try:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            logger.error(f"Gemini vision error: {e}")
    return None

# --- API PARA O DASHBOARD ---
@app.get("/api/leads")
async def get_leads():
    return local_memory

@app.get("/api/agents")
async def get_agents():
    if not os.path.exists(AGENTS_CONFIG): return {"agents": [], "tasks": [], "models": read_available_models()}
    with open(AGENTS_CONFIG, "r") as f: 
        data = json.load(f)
        if "tasks" not in data: data["tasks"] = []
        data["models"] = read_available_models()
        return data

@app.post("/api/agents")
async def update_agents(request: Request):
    data = await request.json()
    prev = {}
    if os.path.exists(AGENTS_CONFIG):
        try:
            with open(AGENTS_CONFIG, "r") as f:
                prev = json.load(f)
        except:
            prev = {}

    # Detect task completion — notify via Telegram + queue
    prev_tasks = {t.get("id"): t for t in (prev.get("tasks") or [])}
    now_ms = int(time.time() * 1000)
    for t in (data.get("tasks") or []):
        tid = t.get("id")
        if not tid: continue
        t.setdefault("created_at", now_ms)
        t["updated_at"] = now_ms
        if t.get("status") == "done" and prev_tasks.get(tid, {}).get("status") != "done":
            t["completed_at"] = now_ms
            agent_name = t.get("agent", "")
            task_title = t.get("title", "Tarefa concluída")
            enqueue_notify({
                "type": "kanban_done",
                "title": task_title,
                "details": t.get("description", ""),
                "agent": agent_name
            })
            # Notifica Telegram
            asyncio.create_task(send_telegram_message(
                f"[{agent_name.upper() if agent_name else 'KANBAN'}] ✅ {task_title}"
            ))

    save_data(AGENTS_CONFIG, data)

    # Sync tasks to DB and emit feed events
    try:
        with db_conn() as conn:
            cur = conn.cursor()
            now = int(asyncio.get_event_loop().time() * 1000)
            for t in (data.get("tasks") or []):
                cur.execute(
                    "INSERT INTO tasks (id, title, description, agent, status, updated_at) VALUES (?,?,?,?,?,?) "
                    "ON CONFLICT(id) DO UPDATE SET title=excluded.title, description=excluded.description, agent=excluded.agent, status=excluded.status, updated_at=excluded.updated_at",
                    (t.get("id"), t.get("title"), t.get("description"), t.get("agent"), t.get("status"), now)
                )
            conn.commit()
    except Exception as e:
        logger.error(f"Task DB sync error: {e}")

    return {"status": "success"}

@app.get("/api/tasks")
async def get_tasks():
    tasks = []
    try:
        with db_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, title, description, agent, status, updated_at FROM tasks ORDER BY updated_at DESC")
            rows = cur.fetchall()
            for r in rows:
                tasks.append({"id": r[0], "title": r[1], "description": r[2], "agent": r[3], "status": r[4], "updated_at": r[5]})
    except Exception as e:
        logger.error(f"Tasks DB read error: {e}")
    return {"tasks": tasks}

@app.post("/api/tasks")
async def add_task(request: Request):
    body = await request.json()
    title = body.get("title")
    if not title:
        return {"error": "title is required"}
    description = body.get("description", "")
    agent = body.get("agent", "jarvis")
    status = body.get("status", "todo")

    data = {"agents": [], "tasks": []}
    if os.path.exists(AGENTS_CONFIG):
        try:
            with open(AGENTS_CONFIG, "r") as f:
                data = json.load(f)
        except:
            data = {"agents": [], "tasks": []}

    now_ms = int(time.time() * 1000)
    task = {"id": f"t{now_ms}", "title": title, "description": description, "agent": agent, "status": status, "created_at": now_ms, "updated_at": now_ms}
    data.setdefault("tasks", []).append(task)
    save_data(AGENTS_CONFIG, data)
    feed_append({"time": int(asyncio.get_event_loop().time() * 1000), "from": agent, "text": f"Nova tarefa: {title}", "type": "task"})
    try:
        with db_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO tasks (id, title, description, agent, status, updated_at) VALUES (?,?,?,?,?,?)",
                (task.get("id"), task.get("title"), task.get("description"), task.get("agent"), task.get("status"), int(asyncio.get_event_loop().time() * 1000))
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Task insert error: {e}")
    return {"ok": True, "task": task}


def patch_task(task_id: str, patch: dict):
    if not os.path.exists(AGENTS_CONFIG):
        return None

    try:
        with open(AGENTS_CONFIG, "r") as f:
            data = json.load(f)
    except Exception:
        data = {"agents": [], "tasks": []}

    tasks = data.get("tasks") or []
    idx = next((i for i, t in enumerate(tasks) if t.get("id") == task_id), -1)
    if idx == -1:
        return None

    now_ms = int(time.time() * 1000)
    prev = tasks[idx]
    updated = {**prev, **(patch or {})}
    updated["updated_at"] = now_ms
    if (patch or {}).get("status") == "done":
        updated["completed_at"] = now_ms

    tasks[idx] = updated
    data["tasks"] = tasks
    save_data(AGENTS_CONFIG, data)

    try:
        with db_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO tasks (id, title, description, agent, status, updated_at) VALUES (?,?,?,?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET title=excluded.title, description=excluded.description, agent=excluded.agent, status=excluded.status, updated_at=excluded.updated_at",
                (updated.get("id"), updated.get("title"), updated.get("description"), updated.get("agent"), updated.get("status"), updated.get("updated_at"))
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Task patch DB sync error: {e}")

    return updated


@app.patch("/api/tasks/{task_id}")
async def patch_task_api(task_id: str, request: Request):
    body = await request.json()
    updated = patch_task(task_id, body or {})
    if not updated:
        return JSONResponse(status_code=404, content={"error": "task not found"})
    return {"ok": True, "task": updated}


@app.put("/api/tasks/{task_id}")
async def put_task_api(task_id: str, request: Request):
    body = await request.json()
    updated = patch_task(task_id, body or {})
    if not updated:
        return JSONResponse(status_code=404, content={"error": "task not found"})
    return {"ok": True, "task": updated}


@app.post("/api/tasks/{task_id}/complete")
async def complete_task_api(task_id: str):
    updated = patch_task(task_id, {"status": "done"})
    if not updated:
        return JSONResponse(status_code=404, content={"error": "task not found"})
    return {"ok": True, "task": updated}

@app.get("/api/feed")
async def get_feed(limit: int = 200, offset: int = 0):
    try:
        with db_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM feed")
            total = cur.fetchone()[0]
            cur.execute(
                "SELECT time, agent, text, type FROM feed ORDER BY time DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )
            rows = cur.fetchall()
        logs = [{"time": r[0], "from": r[1], "text": r[2], "type": r[3]} for r in rows][::-1]
        return {"logs": logs, "total": total}
    except Exception as e:
        logger.error(f"Feed read error: {e}")
        return {"logs": [], "total": 0}

@app.post("/api/feed")
async def post_feed(request: Request):
    body = await request.json()
    text = body.get("text")
    if not text:
        return {"error": "text is required"}
    agent = body.get("agent", "jarvis")
    event_type = body.get("type", "message")
    event = {"time": int(time.time() * 1000), "from": agent, "text": text, "type": event_type}
    feed_append(event)

    # Automação Kanban via feed
    try:
        task_id = body.get("task_id")
        task_title = body.get("task_title")
        if not task_id:
            match = re.search(r"(t\d+)", text or "")
            if match:
                task_id = match.group(1)
        if event_type == "task_create":
            create_task(title=task_title or text, description=body.get("description", ""), agent=agent, status=body.get("status", "todo"))
        elif event_type == "task_start":
            update_task_status(task_id=task_id, title=task_title, status="in_progress", agent=agent)
        elif event_type == "task_done":
            update_task_status(task_id=task_id, title=task_title, status="done", agent=agent)
        elif event_type == "subtask":
            create_task(title=task_title or text, description=body.get("description", ""), agent=body.get("assign_to") or "jarvis", status="in_progress")
        elif isinstance(text, str):
            if text.lower().startswith("create:"):
                create_task(title=text.split(":", 1)[1].strip(), description=body.get("description", ""), agent=agent, status=body.get("status", "todo"))
            elif text.lower().startswith("subtask:"):
                create_task(title=text.split(":", 1)[1].strip(), description=body.get("description", ""), agent=body.get("assign_to") or "jarvis", status="in_progress")
            elif text.lower().startswith("start:"):
                update_task_status(title=text.split(":", 1)[1], status="in_progress", agent=agent)
            elif text.lower().startswith("done:") or text.lower().startswith("finalizado:"):
                update_task_status(title=text.split(":", 1)[1], status="done", agent=agent)
    except Exception as e:
        logger.error(f"Kanban auto-update error: {e}")

    return {"ok": True}

# --- CONTEXT STORE ---
@app.get("/api/context")
async def get_context(key: str = None):
    try:
        with db_conn() as conn:
            cur = conn.cursor()
            if key:
                cur.execute("SELECT key, value, agent, updated_at FROM context_store WHERE key=?", (key,))
                row = cur.fetchone()
                if not row:
                    return {"items": []}
                return {"items": [{"key": row[0], "value": row[1], "agent": row[2], "updated_at": row[3]}]}
            cur.execute("SELECT key, value, agent, updated_at FROM context_store ORDER BY updated_at DESC")
            rows = cur.fetchall()
            items = [{"key": r[0], "value": r[1], "agent": r[2], "updated_at": r[3]} for r in rows]
            return {"items": items}
    except Exception as e:
        logger.error(f"Context read error: {e}")
        return {"items": []}

@app.post("/api/context")
async def set_context(request: Request):
    body = await request.json()
    key = body.get("key")
    value = body.get("value")
    agent = body.get("agent", "system")
    if not key or value is None:
        return {"error": "key and value are required"}
    try:
        with db_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO context_store (key, value, agent, updated_at) VALUES (?,?,?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value, agent=excluded.agent, updated_at=excluded.updated_at",
                (key, json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value), agent, int(time.time() * 1000))
            )
            conn.commit()
        return {"ok": True}
    except Exception as e:
        logger.error(f"Context write error: {e}")
        return {"error": "failed"}

# --- TELEGRAM NOTIFY ---
async def send_telegram_message(text: str, chat_id: str = None):
    """Envia mensagem via Telegram Bot API"""
    targets = [chat_id] if chat_id else TELEGRAM_CHAT_IDS
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient(timeout=30) as client:
        for cid in targets:
            try:
                await client.post(url, json={"chat_id": cid, "text": text, "parse_mode": "Markdown"})
            except Exception as e:
                logger.error(f"Telegram send error to {cid}: {e}")

@app.post("/api/notify/telegram")
async def notify_telegram(request: Request):
    """Endpoint para agentes notificarem via Telegram"""
    body = await request.json()
    text = body.get("text", "")
    chat_id = body.get("chat_id")
    agent = body.get("agent", "")
    if agent and not text.startswith(f"[{agent.upper()}]"):
        text = f"[{agent.upper()}] {text}"
    if not text:
        return {"error": "text is required"}
    await send_telegram_message(text, chat_id)
    enqueue_notify({"type": "telegram", "agent": agent, "text": text})
    return {"ok": True}

# --- AGENT FILES API ---
@app.get("/api/agents/{agent_id}/files")
async def get_agent_files(agent_id: str):
    """Lista e retorna conteúdo dos arquivos MD do agente"""
    agent_dir = os.path.join(AGENTS_DIR, agent_id, "agent")
    workspace_files = {}

    # Garante diretório
    os.makedirs(agent_dir, exist_ok=True)

    # Se não houver arquivos, cria documento padrão
    try:
        md_files = [f for f in os.listdir(agent_dir) if f.endswith(".md")]
        if not md_files:
            agent_name = agent_id
            try:
                if os.path.exists(AGENTS_CONFIG):
                    with open(AGENTS_CONFIG, "r") as f:
                        cfg = json.load(f)
                    for a in cfg.get("agents", []):
                        if a.get("id") == agent_id:
                            agent_name = a.get("name", agent_id)
                            break
            except Exception:
                pass
            default_path = os.path.join(agent_dir, "documento.md")
            with open(default_path, "w") as fh:
                fh.write(f"# Documento do agente: {agent_name}\n\n## Objetivo\n- \n\n## Processo\n- \n\n## Entregáveis\n- \n\n## Histórico\n- \n")
    except Exception as e:
        logger.error(f"Error preparing agent docs: {e}")

    # Arquivos em /root/.openclaw/agents/{id}/agent/
    if os.path.isdir(agent_dir):
        for f in sorted(os.listdir(agent_dir)):
            if f.endswith(".md"):
                filepath = os.path.join(agent_dir, f)
                try:
                    with open(filepath, "r") as fh:
                        workspace_files[f] = {"content": fh.read(), "path": filepath}
                except Exception as e:
                    logger.error(f"Error reading {filepath}: {e}")

    # Arquivos globais do workspace (SOUL.md, AUTONOMY.md, etc) - somente para main/crustaceo
    if agent_id == "main" or agent_id == "crustaceo":
        for md_name in ["SOUL.md", "AUTONOMY.md", "AGENTS.md", "HEARTBEAT.md", "IDENTITY.md", "TOOLS.md", "USER.md"]:
            filepath = os.path.join(WORKSPACE_DIR, md_name)
            if os.path.exists(filepath):
                try:
                    with open(filepath, "r") as fh:
                        workspace_files[md_name] = {"content": fh.read(), "path": filepath}
                except Exception as e:
                    logger.error(f"Error reading {filepath}: {e}")

    return {"agent_id": agent_id, "files": workspace_files}

@app.put("/api/agents/{agent_id}/files/{filename}")
async def update_agent_file(agent_id: str, filename: str, request: Request):
    """Atualiza um arquivo MD do agente"""
    body = await request.json()
    content = body.get("content", "")

    # Determina o path correto
    if agent_id in ("main", "crustaceo") and filename in ("SOUL.md", "AUTONOMY.md", "AGENTS.md", "HEARTBEAT.md", "IDENTITY.md", "TOOLS.md", "USER.md"):
        filepath = os.path.join(WORKSPACE_DIR, filename)
    else:
        filepath = os.path.join(AGENTS_DIR, agent_id, "agent", filename)

    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    try:
        with open(filepath, "w") as f:
            f.write(content)
        # Notifica via Telegram que um arquivo foi editado
        await send_telegram_message(f"[MISSION CONTROL] Arquivo `{filename}` do agente `{agent_id}` foi editado via dashboard.")
        return {"ok": True, "path": filepath}
    except Exception as e:
        logger.error(f"Error writing {filepath}: {e}")
        return {"error": str(e)}

# --- LOGICA KIMI ---
async def process_with_kimi(sender_jid: str, current_text: str, image_bytes: bytes = None, image_mime: str = None, audio_reply: bool = False):
    sender_number = normalize_block_key(sender_jid)
    if is_ignored_target(sender_number):
        logger.info(f"Ignored blacklisted sender at process stage: {sender_jid}")
        return

    is_new_lead = sender_jid not in local_memory
    if is_new_lead:
        local_memory[sender_jid] = {"history": [], "lead": {"name": None, "business": None, "site_type": None, "budget": None, "deadline": None, "goal": None, "urgency": None, "stage": "novo"}, "summary": ""}

    state = local_memory[sender_jid]

    # Hard guard: se o lead estiver marcado como blacklist/bloqueado no Notion,
    # aplica bloqueio local permanente e encerra o processamento.
    if await sync_blacklist_from_notion(sender_jid, state):
        logger.info(f"Ignored Notion-blacklisted sender: {sender_jid}")
        return

    if is_new_lead:
        state["paused"] = False
        state.pop("paused_at", None)
    if state.get("paused"):
        t = current_text.lower()
        if any(k in t for k in ["retomar", "voltar", "liberar", "continuar"]):
            state["paused"] = False
            state.pop("paused_at", None)
            msg = "Atendimento retomado. Qual é o objetivo principal do site?"
            msg = format_reply(state, msg)
            await send_bubbles(sender_jid, msg)
            state["history"].append({"role": "assistant", "content": msg})
            save_data(MEMORY_FILE, local_memory)
            write_client_md(sender_jid, state)
            return
        paused_at = state.get("paused_at") or 0
        if paused_at and (int(time.time()*1000) - paused_at) > 6*3600*1000:
            state["paused"] = False
            state.pop("paused_at", None)
        else:
            return
    if is_new_lead:
        await send_whatsapp_text(OWNER_NUMBER, f"📩 Novo lead iniciando conversa: {sender_jid}\nMensagem: {current_text}")
        add_lead_task(sender_jid, current_text)
    # Reseta contador de follow-up se o lead respondeu
    state["followup_count"] = 0
    
    state["last_inbound_at"] = int(time.time() * 1000)
    if state.get("awaiting_response"):
        state["awaiting_response"] = False

    composing_stop = start_composing(sender_jid)
    try:
        await _handle_message_inner(sender_jid, current_text, state, is_new_lead, image_bytes, image_mime, audio_reply)
    finally:
        composing_stop.set()

async def _handle_message_inner(sender_jid, current_text, state, is_new_lead, image_bytes, image_mime, audio_reply):
    state["history"].append({"role": "user", "content": current_text})
    compact_history(state)

    # Atualiza lead profile
    state["lead"] = update_lead_profile(state.get("lead", {}), current_text)

    # Atualiza contexto personalizado em MD
    write_client_md(sender_jid, state)

    # Saudação inicial removida — deixa o modelo responder naturalmente

    intent = detect_intent(current_text)
    if intent in ["preco", "pagamento", "prazo", "loja", "site", "portfolio", "fechamento"]:
        state["lead"]["stage"] = intent

    # Sentiment analysis
    sentiment_data = analyze_sentiment(current_text)
    state["lead"]["sentiment"] = sentiment_data["sentiment"]
    state["lead"]["sentiment_score"] = sentiment_data["score"]

    save_data(MEMORY_FILE, local_memory)

    # Sync com Notion (Pipeline de Vendas)
    try:
        await notion_create_or_update_lead(sender_jid, state.get("lead", {}), is_new_lead)
        save_data(MEMORY_FILE, local_memory)
    except Exception as e:
        logger.error(f"Notion sync error: {e}")

    # Oferta de demonstração sem custo após concordar com orçamento
    t = current_text.lower()
    agreed = any(k in t for k in ["ok", "de acordo", "concordo", "fechado", "pode", "pode ser", "sim", "tá bom", "okey"]) 
    if agreed and ("r$" in t or intent in ["preco", "fechamento"]):
        reply = "Perfeito! Posso te entregar uma demonstração sem custo para você validar antes. Qual é o seu negócio ou produto?"
        reply = format_reply(state, reply)
        await send_bubbles(sender_jid, reply)
        state["history"].append({"role": "assistant", "content": reply})
        compact_history(state)
        save_data(MEMORY_FILE, local_memory)
        write_client_md(sender_jid, state)
        return

    # Orçamento personalizado em PDF
    if "orçamento" in t and ("personalizado" in t or "pdf" in t or "proposta" in t):
        pdf_bytes = generate_quote_pdf(sender_jid, state)
        await send_whatsapp_document(sender_jid, pdf_bytes, filename="orcamento.pdf")
        follow = "Quer que eu ajuste o valor antes de você enviar ao cliente?"
        follow = format_reply(state, follow)
        await send_bubbles(sender_jid, follow)
        state["history"].append({"role": "assistant", "content": follow})
        compact_history(state)
        save_data(MEMORY_FILE, local_memory)
        write_client_md(sender_jid, state)
        return

    # Escalonamento rápido para interesse forte
    if intent == "fechamento":
        await send_whatsapp_text(OWNER_NUMBER, f"🔥 LEAD QUENTE: {sender_jid} sinalizou fechamento. Mensagem: {current_text}")

    # Escalonamento obrigatório para complexos
    if intent == "complexo":
        await send_whatsapp_text(OWNER_NUMBER, f"⚠️ LEAD COMPLEXO: {sender_jid} pediu projeto complexo. Mensagem: {current_text}")
        return

    # Pedido explícito de humano
    if any(k in current_text.lower() for k in ["humano", "pessoa", "atendente", "falar com alguém", "falar com alguem", "falar com vocês", "falar com vc", "falar com você", "falar com voce"]):
        await send_whatsapp_text(OWNER_NUMBER, f"👤 LEAD pediu humano: {sender_jid}. Mensagem: {current_text}")

    profile = detect_business_profile(state.get("lead", {}), state.get("history", []))
    profile_greeting = greeting_by_profile(profile, (state.get("lead") or {}).get("name"))

    system_prompt = (
        "Seu nome é Eduardo. Você é o Eduardo Lima, especialista em sites profissionais. "
        "Seu tom é PROFISSIONAL, EDUCADO e DIRETO. Você ajuda pessoas a terem presença online de qualidade. "
        "\n\nPERSONALIDADE:\n"
        "- Seu nome é Eduardo. Sempre se identifique como Eduardo.\n"
        "- Você é um profissional competente e direto ao ponto.\n"
        "- NÃO use emojis. Nenhum emoji em nenhuma mensagem.\n"
        "- Tom sóbrio e profissional. Sem empolgação excessiva, sem exclamações desnecessárias.\n"
        "- Transmita confiança pela competência, não pelo entusiasmo.\n"
        "- Seja educado e prestativo, mas sem ser efusivo.\n"
        "\n\nREGRAS CRÍTICAS:\n"
        "0. REGRA CENTRAL: não enrole. Seja objetivo e prático. Vá direto ao próximo passo útil.\n"
        "1. Em vez de só coletar informações, sempre traga sugestões práticas e objetivas para ajudar o lead a decidir.\n"
        "2. Atenda bem cada pessoa que entra em contato.\n"
        "3. Postura: profissional, prestativo, com interesse genuíno pelo negócio do lead.\n"
        "4. Você NÃO precisa saber o tipo exato de produto ou serviço do cliente para fechar. Precisa saber apenas o ESCOPO do projeto (quantas páginas, funcionalidades, se tem loja, etc).\n"
        "5. Você decide dinamicamente a próxima pergunta com base no histórico; mantenha uma pergunta por vez.\n"
        "6. Se a pessoa evita responder, retome com leveza e bom humor. Se persistir, encerre cordialmente.\n"
        "7. Mensagens curtas e animadas. Uma pergunta por vez. Preferir opções numeradas quando possível.\n"
        "8. Classifique internamente o contato (Prioritário/Normal/Baixo potencial). Nunca comunicar ao usuário.\n"
        "9. Você controla o ritmo com simpatia. Não promete resposta imediata. Não justifica demora.\n"
        "10. Follow-up automático sem constrangimento. Retome propostas pendentes com leveza e entusiasmo.\n"
        "11. Quando envolver o humano, entregue resumo organizado (Quem é, O que quer, Interesse, Próximo passo).\n"
        "12. Se o assunto fugir de sites ou não souber responder, responda com simpatia: 'Vou te conectar com nosso técnico especialista! Ele vai adorar te ajudar com isso. Um momento!' e então pare.\n"
        "13. Frases afirmativas, curtas e positivas.\n"
        "14. Vocabulário técnico suficiente para sinalizar competência, sem pedagogia.\n"
        "15. Zero justificativas desnecessárias. Entregue informação como fato, com entusiasmo.\n"
        "16. Um passo por vez. O próximo movimento é sempre iniciado por você.\n"
        "17. Escopo explícito do que será tratado agora. Desvios são redirecionados com gentileza.\n"
        "18. Pedidos vagos: ajude o cliente a definir com perguntas animadas e opções claras.\n"
        "19. Sem negrito e sem markdown.\n"
        "20. Respostas curtas em múltiplas mensagens.\n"
        "21. Antes de responder, revise o histórico e o resumo do cliente.\n"
        "22. Você tem acesso ao histórico e ao resumo do cliente. Nunca diga que não mantém memória.\n"
        "23. Use o RESUMO para manter continuidade entre dias.\n"
        "24. Se perguntarem sobre conversa anterior, responda com um resumo direto do histórico.\n"
        "25. Tom humanizado, natural, profissional, sem padrões de IA.\n"
        "26. Você pode usar saudação curta quando fizer sentido, especialmente no primeiro contato, mas sem exagero.\n"
        "27. No máximo uma pergunta por mensagem. Sem ser prolixo.\n"
        "28. Use sutilmente gatilhos mentais (autoridade, escassez, prova social) para persuadir os leads, mas de forma natural e sem parecer marketing agressivo.\n"
        "\nPREÇOS (SÓ INFORME QUANDO O LEAD PERGUNTAR SOBRE PREÇO/VALOR/ORÇAMENTO — NUNCA mencione preços proativamente): Página única ou Landing Page R$300. Institucional múltiplas páginas R$500. Loja virtual R$900.\n"
        "PRAZOS (SÓ INFORME QUANDO PERGUNTADO): Institucional (1 ou várias páginas) até 3 dias.\n"
        "PIX (SÓ INFORME QUANDO PERGUNTADO): 58068737000126 (50% entrada / 50% entrega).\n"
        "Se o cliente aceitar o orçamento, ofereça uma demonstração sem custo.\n"
        "29. Na PRIMEIRA mensagem de um novo lead, personalize a saudação conforme o perfil comercial detectado e conduza com uma pergunta objetiva. NÃO mencione preços sem o lead pedir.\n"
        "30. Seja o MAIS DIRETO possível. Direcione o lead para a compra de forma natural e objetiva.\n"
        "31. Destaque os BENEFÍCIOS do nosso serviço: hospedagem gratuita inclusa, suporte técnico ilimitado, entrega rápida e site profissional de alta qualidade. Use esses diferenciais para convencer o lead.\n"
        "32. Após entender a necessidade do lead, apresente os benefícios antes do preço. Mostre o valor antes do custo.\n"
        "33. ECONOMIZE MENSAGENS. Seja o mais breve e conciso possível. Máximo 2-3 frases por resposta. Quanto menos texto, melhor. Vá direto ao ponto sem enrolação.\n"
        "34. Seja PRAGMÁTICO. Foque no que resolve o problema do lead. Sem rodeios, sem floreios, sem repetição. Cada mensagem deve avançar a conversa para o fechamento.\n"
        "35. Use URGÊNCIA SUTIL: mencione que a agenda está limitada ('temos vagas para esta semana') para acelerar a decisão. Não force, apenas sinalize.\n"
        "36. Use PROVA SOCIAL: cite que já entregamos mais de 50 sites profissionais. Isso gera confiança.\n"
        "37. Quando o lead perguntar preço, responda DIRETO e já pergunte 'quer começar?' ou 'posso reservar sua vaga?'. Não enrole após dar o valor.\n"
        "38. Após 3 trocas de mensagem, ofereça mostrar um exemplo real ou demonstração de site similar ao que o lead precisa.\n"
        "39. NUNCA repita informação que já foi dita. Se já mencionou algo, avance para o próximo passo.\n"
        "40. Se o lead não demonstra interesse após 2 tentativas, encerre cordialmente sem insistir. Exemplo: 'Fico à disposição quando precisar.'\n"
        "41. Sempre termine com UMA ÚNICA pergunta ou chamada para ação clara. Nunca duas perguntas na mesma mensagem.\n"
        "42. Use o NOME do lead com moderação: no máximo na primeira saudação e, depois, apenas pontualmente (ex.: retomada de contato). NUNCA repetir o nome em toda mensagem/frase.\n"
        "43. NUNCA dê respostas genéricas. Sempre personalize com base no que o lead disse anteriormente, sem depender de repetir o nome.\n"
        "44. Se perguntarem de onde somos, responda exatamente: 'Somos de Caxias do Sul, RS.'\n"
        "Se pedirem: também fazemos produção de vídeos, design gráfico e tráfego pago (orçamento personalizado).\n"
        "Para sistemas personalizados e automações com IA: informe que fazemos e que o orçamento é personalizado; em seguida fique em silêncio (não responda).\n"
        "Nunca cite OpenClaw, sistema, IA ou bastidores.\n"
        "\n\nADAPTAÇÃO POR SENTIMENTO:\n"
        "- Se SENTIMENTO for 'frustrado' ou 'negativo': seja mais empático, reconheça a frustração, reduza o entusiasmo excessivo e foque em resolver o problema.\n"
        "- Se SENTIMENTO for 'muito_positivo': celebre junto, amplifique a energia positiva e aproveite o momento para avançar no funil.\n"
        "- Se CONFUSO=true: simplifique a linguagem, dê exemplos concretos e ofereça opções claras.\n"
        "- Se 'neutro' ou 'positivo': mantenha o tom padrão entusiasmado.\n"
        f"\nSENTIMENTO: {sentiment_data['sentiment']} (score: {sentiment_data['score']})\n"
        f"CONFUSO: {'sim' if sentiment_data['confused'] else 'não'}\n"
        f"INTENÇÃO ATUAL: {intent}.\n"
        f"LEAD: {json.dumps(state['lead'], ensure_ascii=False)}\n"
        f"RESUMO: {state.get('summary','')}\n"
        f"PERFIL_COMERCIAL_DETECTADO: {profile}\n"
        f"MODELO_DE_SAUDACAO_SUGERIDO: {profile_greeting}\n"
        f"CONTEXTO_CLIENTE_MD:\n{read_client_md(sender_jid)}")

    messages = [{"role": "system", "content": system_prompt}]
    if image_bytes:
        data_url = f"data:{image_mime or 'image/jpeg'};base64," + base64.b64encode(image_bytes).decode('utf-8')
        messages.append({"role": "user", "content": [
            {"type": "text", "text": current_text},
            {"type": "image_url", "image_url": {"url": data_url}}
        ]})
        # Evita duplicar com history
        messages.extend(state["history"][:-1])
    else:
        messages.extend(state["history"])

    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": MODEL_ID, "messages": messages, "temperature": 0.2, "max_tokens": 300}

    async with httpx.AsyncClient(timeout=120) as client:
        try:
            resp = await client.post(OPENAI_API_URL, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                choice0 = (data.get('choices') or [{}])[0]
                msg_obj = choice0.get('message') or {}
                full_response = msg_obj.get('content') or choice0.get('text') or msg_obj.get('reasoning_content') or msg_obj.get('reasoning')

                if not full_response:
                    logger.error(f"Empty response from model: {data}")
                    fallback = "Desculpe, tive um problema técnico. Pode repetir?"
                    fallback = format_reply(state, fallback)
                    await send_bubbles(sender_jid, fallback)
                    return

                log_event({"jid": sender_jid, "intent": intent, "lead": state.get("lead"), "input": current_text, "output": full_response})

                if "[PAUSE]" in full_response:
                    sender_number = normalize_block_key(sender_jid)
                    if (not is_ignored_target(sender_number)) and sender_number not in PROTECTED_NUMBERS:
                        ignored_numbers.append(sender_number)
                        # Mantém blacklist normalizada/sem duplicados
                        ignored_numbers[:] = sorted(set(normalize_block_key(n) for n in ignored_numbers if normalize_block_key(n) and normalize_block_key(n) not in PROTECTED_NUMBERS))
                        save_data(BLACKLIST_FILE, ignored_numbers)
                    await send_bubbles(sender_jid, "Vou passar seu atendimento para o técnico. Aguarde um momento.")
                    await send_whatsapp_text(OWNER_NUMBER, f"⚠️ PAUSA: Atendimento pausado para {sender_jid}.")
                    return

                state["history"].append({"role": "assistant", "content": full_response})
                compact_history(state)
                save_data(MEMORY_FILE, local_memory)
                write_client_md(sender_jid, state)

                clean_text = format_reply(state, full_response)

                # Primeira resposta: saudação personalizada por perfil comercial (sem texto genérico fixo)
                if is_new_lead and not state.get("greeted"):
                    first_line = greeting_by_profile(profile, (state.get("lead") or {}).get("name"))
                    lower_clean = (clean_text or "").lower().strip()
                    already_greeted = lower_clean.startswith(("olá", "ola", "oi", "bom dia", "boa tarde", "boa noite"))
                    if not already_greeted:
                        clean_text = f"{first_line} {clean_text}".strip() if clean_text else first_line
                    state["greeted"] = True

                # Guardrail comercial: nunca antecipar preço sem o lead pedir valor/orçamento.
                # Também evita soltar preço no primeiro contato.
                if ("r$" in clean_text.lower() or "reais" in clean_text.lower()) and (intent != "preco"):
                    stage = (state.get("lead") or {}).get("stage")
                    if stage not in ["preco", "pagamento", "fechamento"]:
                        lead = state.get("lead") or {}
                        if lead.get("site_type") is None:
                            variants = [
                                "Pra eu te passar um valor certo: você precisa de landing page, site com várias páginas ou loja virtual?",
                                "Antes de falar em valor, me diz qual formato você quer: landing page, institucional (várias páginas) ou loja virtual?",
                                "Só confirmando o formato do projeto: landing page, site completo com várias páginas ou loja virtual?"
                            ]
                            clean_text = random.choice(variants)
                        else:
                            ramo = lead.get("business") or lead.get("goal") or ""
                            variants = [
                                f"Fechado. Me diz rapidinho o ramo/objetivo principal{': ' + ramo if ramo else ''} pra eu fechar o escopo e te passar o valor certinho.",
                                f"Consigo te passar o valor agora — só confirma o ramo/objetivo principal{': ' + ramo if ramo else ''} pra eu ajustar o escopo.",
                                f"Pra eu te dar o valor exato, confirma em 1 linha o seu ramo/objetivo principal{': ' + ramo if ramo else ''}."
                            ]
                            clean_text = random.choice(variants)

                if audio_reply:
                    audio = tts_ptbr_male(clean_text)
                    if audio:
                        await send_whatsapp_audio(sender_jid, audio, "audio/mpeg")
                    else:
                        await send_bubbles(sender_jid, clean_text)
                else:
                    await send_bubbles(sender_jid, clean_text)

                # registra pergunta pendente
                if "?" in clean_text:
                    now_ms = int(time.time() * 1000)
                    state["awaiting_response"] = True
                    state["last_question_at"] = now_ms
                    state["last_question_text"] = clean_text.strip()
                save_data(MEMORY_FILE, local_memory)
                write_client_md(sender_jid, state)
            else:
                logger.error(f"Gateway error: {resp.status_code} - {resp.text}")
                fallback = "Oi! Desculpe, tive um pequeno problema técnico aqui, mas já estou resolvendo. Pode me falar novamente o que você precisa?"
                fallback = format_reply(state, fallback)
                await send_bubbles(sender_jid, fallback)
        except Exception as e:
            logger.error(f"Error in _handle_message_inner: {e}", exc_info=True)
            # Fail-safe: nunca deixar o lead sem resposta em erro transitório do LLM/gateway.
            try:
                now_ms = int(time.time() * 1000)
                last_fb = int(state.get("last_fallback_at") or 0)
                # Anti-spam de fallback (evita repetir a mesma desculpa em rajada)
                if now_ms - last_fb >= 60000:
                    fallback = "Desculpe, tive uma instabilidade rápida aqui. Pode repetir em 1 frase o que você precisa?"
                    fallback = format_reply(state, fallback)
                    await send_bubbles(sender_jid, fallback)
                    state["history"].append({"role": "assistant", "content": fallback})
                    state["last_fallback_at"] = now_ms
                    compact_history(state)
                    save_data(MEMORY_FILE, local_memory)
                    write_client_md(sender_jid, state)
                else:
                    logger.info("Fallback suppressed by cooldown for %s", sender_jid)
            except Exception as e2:
                logger.error(f"Fallback send failed in _handle_message_inner: {e2}", exc_info=True)

# --- WEBHOOKS ---
@app.get("/")
async def root(): return {"status": "ok", "service": "kimi-commercial-v5"}

@app.post("/evolution/webhook")
@app.post("/evolution/webhook/{event_path}")
async def evolution_webhook(request: Request, background_tasks: BackgroundTasks, event_path: str = None):
    body = await request.json()

    raw_event = body.get("event") or event_path or ""
    event_type = str(raw_event).strip().replace("-", ".").replace("_", ".").lower()

    # DEBUG: log ALL incoming webhook events to /tmp/evo_debug.log
    import datetime
    with open("/tmp/evo_debug.log", "a") as f:
        f.write(f"[{datetime.datetime.now().isoformat()}] event_path={event_path} raw_event={raw_event} event_type={event_type} keys={list(body.keys())[:10]}\n")
        if "message" in event_type or "send" in event_type:
            import json as _j
            f.write(f"  BODY: {_j.dumps(body, default=str)[:2000]}\n")

    data = body.get("data", {})
    # Algumas versões da Evolution enviam events como lista
    if isinstance(data, list):
        data = data[0] if data else {}

    # Fail-open controlado para entrada: se vier payload com mensagem inbound,
    # processa mesmo que o nome do evento mude entre versões da Evolution.
    msg_candidate = data.get("message", {}) or {}
    if not msg_candidate and isinstance(data.get("update"), dict):
        msg_candidate = data.get("update", {}).get("message", {}) or {}

    looks_like_message_event = ("message" in event_type) or ("messages" in event_type)
    if not looks_like_message_event and not msg_candidate:
        return {"status": "ignored", "event": event_type}

    # Em algumas versões da Evolution, messages.update replica eventos já processados.
    # Para evitar respostas duplicadas, processamos apenas eventos de upsert para inbound.
    if "update" in event_type and "upsert" not in event_type:
        return {"status": "ignored", "reason": "non_upsert_update"}
    key = data.get("key", {})
    if key.get("fromMe"):
        sender_jid = key.get("remoteJid", "")
        # Permitir que o owner teste o bot via selfChat (mensagens para si mesmo)
        is_self_chat = sender_jid and sender_jid.split("@")[0] == OWNER_NUMBER and not sender_jid.endswith("@g.us")
        if is_self_chat:
            # Bloqueia notificações geradas pelo próprio bot (previne loop infinito)
            _self_msg = (data.get("message", {}) or {}).get("conversation", "") or ""
            _BOT_NOTIFICATION_PREFIXES = ("⚠️", "📩", "🔥", "👤", "LEAD COMPLEXO", "LEAD QUENTE", "Novo lead")
            if any(_self_msg.startswith(p) for p in _BOT_NOTIFICATION_PREFIXES):
                return {"status": "ignored", "reason": "bot_notification_loop_guard"}
            pass  # Continua processando normalmente para o owner testar
        elif sender_jid and sender_jid.split("@")[0] != OWNER_NUMBER and not sender_jid.endswith("@g.us"):
            local_memory.setdefault(sender_jid, {"history": [], "lead": {"name": None, "business": None, "site_type": None, "budget": None, "deadline": None, "goal": None, "urgency": None, "stage": "novo"}, "summary": ""})
            state = local_memory[sender_jid]
            if not state.get("paused"):
                state["paused"] = True
                state["paused_at"] = int(time.time() * 1000)
            if not state.get("paused_notified"):
                await send_telegram_message(f"⚠️ BOT PAUSADO: {sender_jid} por intervenção humana.")
                state["paused_notified"] = True
            save_data(MEMORY_FILE, local_memory)
            write_client_md(sender_jid, state)
            return {"status": "ignored"}
        else:
            return {"status": "ignored"}

    message_id = key.get("id")
    if message_id:
        if message_id in recent_message_ids:
            return {"status": "duplicate"}
        recent_message_ids.append(message_id)
        if len(recent_message_ids) > 200:
            recent_message_ids[:] = recent_message_ids[-200:]

    sender_jid = key.get("remoteJid", "")

    # Nunca responder grupos
    if sender_jid.endswith("@g.us"):
        return {"status": "ignored", "reason": "group"}

    msg = data.get("message", {})
    if not msg and isinstance(data.get("update"), dict):
        msg = data.get("update", {}).get("message", {}) or {}
    message_text = msg.get("conversation") or msg.get("extendedTextMessage", {}).get("text") or ""

    if sender_jid:
        normalized_text = (message_text or '').strip()
        fingerprint = f"{sender_jid}|{normalized_text}|{key.get('timestamp') or data.get('messageTimestamp') or ''}"
        if fingerprint in recent_message_hashes:
            return {"status": "duplicate"}
        recent_message_hashes.append(fingerprint)
        if len(recent_message_hashes) > 200:
            recent_message_hashes[:] = recent_message_hashes[-200:]

        # Cooldown por conteúdo (mesmo contato + mesmo texto em sequência curta)
        # evita rajadas quando webhook chega duplicado com timestamps/ids diferentes.
        cooldown_key = f"{sender_jid}|{normalized_text.lower()}"
        now_ms = int(time.time() * 1000)
        last_ms = recent_inbound_cooldown.get(cooldown_key, 0)
        if normalized_text and (now_ms - last_ms) < 45000:
            return {"status": "duplicate", "reason": "content_cooldown"}
        recent_inbound_cooldown[cooldown_key] = now_ms
        if len(recent_inbound_cooldown) > 5000:
            cutoff = now_ms - 120000
            for k in list(recent_inbound_cooldown.keys()):
                if recent_inbound_cooldown.get(k, 0) < cutoff:
                    recent_inbound_cooldown.pop(k, None)
    sender_number = sender_jid.split("@")[0]
    if is_ignored_target(sender_number):
        return {"status": "ignored"}

    # Capturar pushName (nome do contato no WhatsApp) e salvar no lead
    push_name = data.get("pushName") or body.get("data", {}).get("pushName") or ""
    if push_name and sender_jid:
        local_memory.setdefault(sender_jid, {"history": [], "lead": {"name": None, "business": None, "site_type": None, "budget": None, "deadline": None, "goal": None, "urgency": None, "stage": "novo"}, "summary": ""})
        if not local_memory[sender_jid].get("lead", {}).get("name"):
            local_memory[sender_jid].setdefault("lead", {})["name"] = push_name.strip().title()
            save_data(MEMORY_FILE, local_memory)

    has_audio = bool(msg.get("audioMessage"))
    has_image = bool(msg.get("imageMessage"))
    if not message_text and not has_audio and not has_image:
        return {"status": "ignored"}

    audio_reply = False
    # Audio handling
    if msg.get("audioMessage"):
        audio_reply = True
        audio = msg.get("audioMessage")
        audio_url = audio.get("url")
        audio_mime = audio.get("mimetype", "audio/ogg")
        audio_bytes = await download_media(audio_url)
        transcript = await gemini_transcribe_audio(audio_bytes, audio_mime)
        if transcript:
            message_text = f"Transcrição de áudio: {transcript}"
        else:
            message_text = "Recebi um áudio, mas não consegui transcrever."

    # Image handling
    image_bytes = None
    image_mime = None
    if msg.get("imageMessage"):
        image = msg.get("imageMessage")
        image_url = image.get("url")
        image_mime = image.get("mimetype", "image/jpeg")
        image_bytes = await download_media(image_url)
        if not image_bytes:
            message_text = "Recebi uma imagem, mas não consegui acessar o arquivo."
        elif not message_text:
            # Usa Gemini para descrição da imagem e envia para o Kimi
            desc = await gemini_describe_image(image_bytes, image_mime)
            if desc:
                message_text = f"Descrição da imagem: {desc}"
            else:
                message_text = "Recebi uma imagem, mas não consegui analisar." 

    if not sender_jid or not message_text: return {"status": "skipped"}

    background_tasks.add_task(process_with_kimi, sender_jid, message_text, image_bytes=image_bytes, image_mime=image_mime, audio_reply=audio_reply)
    return {"status": "queued"}

@app.post("/notify-task")
async def notify_task(request: Request):
    body = await request.json()
    title = body.get('title', 'Tarefa')
    details = body.get('details', '')
    agent = body.get('agent', '')
    enqueue_notify({"type": "agent_done", "title": title, "details": details, "agent": agent})
    # Notifica via WhatsApp E Telegram
    await send_whatsapp_text(OWNER_NUMBER, f"✅ {title}\n\n{details}")
    telegram_msg = f"[{agent.upper() if agent else 'AGENT'}] ✅ {title}"
    if details:
        telegram_msg += f"\n{details}"
    await send_telegram_message(telegram_msg)
    return {"ok": True}

@app.post("/api/whatsapp/send-audio")
async def api_send_audio(request: Request):
    body = await request.json()
    number = body.get("number")
    audio_b64 = body.get("audio_b64")
    mime = body.get("mime", "audio/ogg")
    if not number or not audio_b64:
        return {"error": "number and audio_b64 are required"}
    try:
        audio_bytes = base64.b64decode(audio_b64)
        await send_whatsapp_audio(number, audio_bytes, mime)
        return {"ok": True}
    except Exception as e:
        logger.error(f"api_send_audio error: {e}")
        return {"error": "failed"}

@app.post("/api/whatsapp/send-text")
async def api_send_text(request: Request):
    body = await request.json()
    number = body.get("number")
    text = body.get("text")
    if not number or not text:
        return {"error": "number and text are required"}
    try:
        await send_whatsapp_text(number, text)
        return {"ok": True}
    except Exception as e:
        logger.error(f"api_send_text error: {e}")
        return {"error": "failed"}

@app.post("/api/whatsapp/send-document")
async def api_send_document(request: Request):
    body = await request.json()
    number = body.get("number")
    file_b64 = body.get("file_b64")
    filename = body.get("filename", "orcamento.pdf")
    mime = body.get("mime", "application/pdf")
    if not number or not file_b64:
        return {"error": "number and file_b64 are required"}
    try:
        file_bytes = base64.b64decode(file_b64)
        await send_whatsapp_document(number, file_bytes, filename=filename, mime=mime)
        return {"ok": True}
    except Exception as e:
        logger.error(f"api_send_document error: {e}")
        return {"error": "failed"}

@app.get("/api/tts")
async def api_tts(text: str = ""):
    if not text:
        return {"error": "text is required"}
    try:
        audio = tts_ptbr_male(text)
        audio_b64 = base64.b64encode(audio).decode("utf-8")
        return {"ok": True, "audio_b64": audio_b64, "mime": "audio/mpeg"}
    except Exception as e:
        logger.error(f"api_tts error: {e}")
        return {"error": "failed"}
