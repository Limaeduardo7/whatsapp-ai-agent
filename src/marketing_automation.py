import asyncio
import json
import logging
import os
import sqlite3
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import HTMLResponse

from src.config import get_settings
from src.marketing_dashboard import render_marketing_dashboard
from src.repositories import MarketingRepository
from src.security import require_admin_api_key, validate_shared_secret
from src.services import EvolutionClient

logger = logging.getLogger("marketing-automation")

router = APIRouter(prefix="/marketing", tags=["marketing"])

settings = get_settings()
marketing_repository = MarketingRepository(settings)
evolution_client = EvolutionClient(settings)
DB_PATH = settings.db_path
EVOLUTION_BASE_URL = settings.evolution_base_url
EVOLUTION_INSTANCE = settings.evolution_instance
EVOLUTION_API_KEY = settings.evolution_api_key
HOTMART_WEBHOOK_SECRET = settings.hotmart_webhook_secret
SCHEDULER_INTERVAL_SECONDS = settings.scheduler_interval_seconds
HOTMART_CLIENT_ID = settings.hotmart_client_id
HOTMART_CLIENT_SECRET = settings.hotmart_client_secret
HOTMART_BASIC_TOKEN = settings.hotmart_basic_token
HOTMART_AUTH_URL = settings.hotmart_auth_url
HOTMART_API_BASE = settings.hotmart_api_base

HOTMART_TOKEN_CACHE: dict[str, Any] = {"access_token": None, "expires_at": 0}

_scheduler_task: asyncio.Task | None = None


def now_utc() -> datetime:
    return datetime.now(UTC)


def to_iso(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat()


def from_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def normalize_phone(raw: str | None) -> str | None:
    if raw is None:
        return None

    # evita interpretar números não telefônicos (ids/timestamps)
    s = str(raw).strip()
    if not s:
        return None

    # se contém letras, normalmente é id/transação (não telefone)
    if any(ch.isalpha() for ch in s):
        return None

    digits = "".join(ch for ch in s if ch.isdigit())
    if not digits:
        return None

    # rejeita epoch em ms (13 dígitos típicos de data)
    if len(digits) == 13:
        try:
            n = int(digits)
            if 1500000000000 <= n <= 2500000000000:
                return None
        except Exception:
            pass

    # rejeita sequências óbvias inválidas
    if len(set(digits)) == 1:
        return None

    # Se vier sem DDI e com padrão BR local (10/11), assume Brasil
    if len(digits) in (10, 11):
        digits = f"55{digits}"

    # E.164 básico
    if not (12 <= len(digits) <= 15):
        return None

    # validação mais rígida para Brasil
    if digits.startswith("55"):
        national = digits[2:]
        # BR deve ter DDD (2) + número (8 ou 9)
        if len(national) not in (10, 11):
            return None

        ddd = national[:2]
        if not ddd.isdigit() or ddd in {"00", "01", "02", "03", "04", "05", "06", "07", "08", "09"}:
            return None

        subscriber = national[2:]
        if len(subscriber) == 9 and subscriber[0] != "9":
            return None

    return digits


def _init_db() -> None:
    marketing_repository.init()


def _load_sequences() -> list[dict[str, Any]]:
    if not os.path.exists(settings.sequences_file):
        return []
    with open(settings.sequences_file, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return data.get("sequences", [])
    return data if isinstance(data, list) else []


def _normalize_language(value: Any) -> str | None:
    if value is None:
        return None
    lang = str(value).strip().lower().replace("_", "-")
    if not lang:
        return None
    if lang.startswith("pt") or lang in {"br", "brazil", "brasil"}:
        return "pt-BR"
    if lang.startswith("en") or lang in {"us", "usa", "gb", "uk", "english"}:
        return "en"
    if lang.startswith("es") or lang in {"spanish", "espanol", "español"}:
        return "es"
    return None


def _find_value_deep(obj: Any, names: set[str]) -> Any:
    if isinstance(obj, dict):
        for key, value in obj.items():
            normalized_key = str(key).lower()
            if normalized_key in names:
                return value
        for value in obj.values():
            found = _find_value_deep(value, names)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = _find_value_deep(value, names)
            if found is not None:
                return found
    return None


def _detect_language(payload: dict[str, Any], product_name: str | None) -> str | None:
    explicit = _find_value_deep(payload, {"language", "lang", "locale", "country", "currency"})
    language = _normalize_language(explicit)
    if language:
        return language

    product_l = (product_name or "").lower()
    if any(token in product_l for token in ["the ", "chameleon", "rule of life", "algorithm of the universe", "master state", "quantum leap"]):
        return "en"
    if any(token in product_l for token in ["la ", "el ", "clave", "regla", "algoritmo del", "camaleón", "camaleon", "maestro", "cuántico", "cuantico"]):
        return "es"
    if any(token in product_l for token in ["chave", "regra", "algoritmo do", "estado mestre", "salto quântico", "salto quantico"]):
        return "pt-BR"
    return None


def _find_sequence_for_product(product_name: str, language: str | None = None) -> dict[str, Any] | None:
    product_name_l = product_name.lower().strip()
    candidates = []
    for seq in _load_sequences():
        triggers = [p.lower().strip() for p in seq.get("trigger_products", [])]
        if any(tp in product_name_l or product_name_l in tp for tp in triggers):
            candidates.append(seq)
    if language:
        for seq in candidates:
            if seq.get("language") == language:
                return seq
    if candidates:
        return candidates[0]
    return None


def _find_phone_deep(obj: Any) -> str | None:
    """Procura telefone em qualquer nível do payload (phone/cell/whatsapp/mobile)."""
    if isinstance(obj, dict):
        # prioridade por chaves conhecidas
        preferred_keys = [
            "checkout_phone", "phone", "phone_number", "mobile_phone",
            "mobile", "cellphone", "cell_phone", "whatsapp", "whatsapp_phone",
        ]
        for k in preferred_keys:
            if k in obj:
                n = normalize_phone(obj.get(k))
                if n:
                    return n

        # varre todas as chaves com nomes relacionados
        for k, v in obj.items():
            lk = str(k).lower()
            if any(t in lk for t in ["phone", "cell", "mobile", "whatsapp", "tel"]):
                n = normalize_phone(v)
                if n:
                    return n

        # desce recursivamente
        for v in obj.values():
            n = _find_phone_deep(v)
            if n:
                return n

    elif isinstance(obj, list):
        for v in obj:
            n = _find_phone_deep(v)
            if n:
                return n

    else:
        n = normalize_phone(obj)
        if n:
            return n

    return None


def _extract_hotmart_fields(payload: dict[str, Any]) -> tuple[str | None, str | None, str | None, str | None, str, str | None]:
    event = str(payload.get("event") or payload.get("event_name") or payload.get("type") or "").lower()

    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload

    # Buyer block
    buyer = data.get("buyer", {}) if isinstance(data, dict) else {}

    phone_candidates = [
        buyer.get("phone"),
        buyer.get("checkout_phone"),
        buyer.get("phone_number"),
        buyer.get("mobile"),
        buyer.get("whatsapp"),
        data.get("phone"),
        data.get("buyer_phone"),
        (data.get("contact") or {}).get("phone") if isinstance(data.get("contact"), dict) else None,
        (data.get("customer") or {}).get("phone") if isinstance(data.get("customer"), dict) else None,
    ]

    product_candidates = [
        (data.get("product") or {}).get("name") if isinstance(data.get("product"), dict) else None,
        data.get("product_name"),
        data.get("name"),
        (data.get("purchase") or {}).get("name") if isinstance(data.get("purchase"), dict) else None,
    ]

    purchase_id_candidates = [
        data.get("purchase_id"),
        data.get("transaction"),
        data.get("id"),
        (data.get("purchase") or {}).get("transaction") if isinstance(data.get("purchase"), dict) else None,
        (data.get("purchase") or {}).get("id") if isinstance(data.get("purchase"), dict) else None,
    ]

    approved_at_candidates = [
        data.get("approved_date"),
        data.get("purchase_date"),
        data.get("date_approved"),
        data.get("created_at"),
        (data.get("purchase") or {}).get("approved_date") if isinstance(data.get("purchase"), dict) else None,
        (data.get("purchase") or {}).get("order_date") if isinstance(data.get("purchase"), dict) else None,
    ]

    phone = next((normalize_phone(v) for v in phone_candidates if normalize_phone(v)), None)
    if not phone:
        phone = _find_phone_deep(payload)

    product = next((str(v).strip() for v in product_candidates if v), None)
    purchase_id = next((str(v).strip() for v in purchase_id_candidates if v), None)
    approved_at = next((str(v).strip() for v in approved_at_candidates if v), None)
    language = _detect_language(payload, product)

    return phone, product, purchase_id, approved_at, event, language


def _hotmart_basic_token() -> str:
    if HOTMART_BASIC_TOKEN:
        return HOTMART_BASIC_TOKEN
    if HOTMART_CLIENT_ID and HOTMART_CLIENT_SECRET:
        import base64
        raw = f"{HOTMART_CLIENT_ID}:{HOTMART_CLIENT_SECRET}".encode()
        return base64.b64encode(raw).decode("utf-8")
    return ""


async def _hotmart_access_token() -> str | None:
    now_ts = int(now_utc().timestamp())
    cached = HOTMART_TOKEN_CACHE.get("access_token")
    if cached and HOTMART_TOKEN_CACHE.get("expires_at", 0) > now_ts + 60:
        return str(cached)

    basic = _hotmart_basic_token()
    if not basic:
        return None

    url = f"{HOTMART_AUTH_URL}?grant_type=client_credentials"
    headers = {"Authorization": f"Basic {basic}", "Accept": "application/json"}

    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(url, headers=headers)
        if r.status_code >= 400:
            logger.warning(f"Hotmart auth failed: {r.status_code} {r.text[:200]}")
            return None
        data = r.json()

    token = data.get("access_token")
    expires_in = int(data.get("expires_in") or 3600)
    if not token:
        return None

    HOTMART_TOKEN_CACHE["access_token"] = token
    HOTMART_TOKEN_CACHE["expires_at"] = now_ts + max(60, expires_in - 120)
    return str(token)


async def _phone_from_sales_users(transaction: str | None) -> str | None:
    if not transaction:
        return None

    token = await _hotmart_access_token()
    if not token:
        return None

    url = f"{HOTMART_API_BASE}/sales/users"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    params = {"transaction": transaction}

    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(url, headers=headers, params=params)
        if r.status_code >= 400:
            logger.warning(f"sales-users failed for {transaction}: {r.status_code} {r.text[:200]}")
            return None
        data = r.json()

    items = data.get("items") or []
    for item in items:
        users = item.get("users") or []
        # 1) buyer role
        for entry in users:
            role = str(entry.get("role") or "").upper()
            if role == "BUYER":
                user = entry.get("user") or {}
                phone = normalize_phone(user.get("cellphone")) or normalize_phone(user.get("phone"))
                if phone:
                    return phone
        # 2) fallback sem role explícita
        for entry in users:
            user = entry.get("user") or {}
            phone = normalize_phone(user.get("cellphone")) or normalize_phone(user.get("phone"))
            if phone:
                return phone

    return None


async def _send_text(phone: str, text: str) -> tuple[str, str | None]:
    if not EVOLUTION_API_KEY:
        raise RuntimeError("EVOLUTION_API_KEY ausente")

    url = f"{EVOLUTION_BASE_URL}/message/sendText/{EVOLUTION_INSTANCE}"
    headers = {
        "Content-Type": "application/json",
        "apikey": EVOLUTION_API_KEY,
    }
    payload = {"number": phone, "text": text}

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        body = response.json()

    provider_status = str(body.get("status") or "UNKNOWN")
    provider_id = ((body.get("key") or {}).get("id") if isinstance(body.get("key"), dict) else None)
    return provider_status, provider_id


def _upsert_customer_after_purchase(phone: str, name: str | None, product: str, approved_at: str | None, language: str | None = None) -> dict[str, Any] | None:
    sequence = _find_sequence_for_product(product, language)

    now = now_utc()
    ts = to_iso(now)
    purchase_dt = approved_at if approved_at else ts
    first_send_at = to_iso(now + timedelta(days=1))

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO marketing_customers (phone, name, status, current_sequence_id, current_step, last_product_bought, next_send_at, last_purchase_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(phone) DO UPDATE SET
              name=excluded.name,
              status=excluded.status,
              current_sequence_id=excluded.current_sequence_id,
              current_step=excluded.current_step,
              last_product_bought=excluded.last_product_bought,
              next_send_at=excluded.next_send_at,
              last_purchase_at=excluded.last_purchase_at,
              updated_at=excluded.updated_at
            """,
            (
                phone,
                name,
                "active" if sequence else "idle",
                sequence.get("id") if sequence else None,
                0,
                product,
                first_send_at if sequence else None,
                purchase_dt,
                ts,
            ),
        )
        conn.commit()

    return sequence


def _save_purchase(purchase_id: str | None, phone: str, product: str, approved_at: str | None, raw_payload: dict[str, Any]) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO marketing_purchases (purchase_id, phone, product, approved_at, raw_payload, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                purchase_id,
                phone,
                product,
                approved_at,
                json.dumps(raw_payload, ensure_ascii=False),
                to_iso(now_utc()),
            ),
        )
        conn.commit()


def _get_due_customers(limit: int = 50) -> list[sqlite3.Row]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT *
            FROM marketing_customers
            WHERE status = 'active'
              AND current_sequence_id IS NOT NULL
              AND next_send_at IS NOT NULL
              AND datetime(next_send_at) <= datetime(?)
            ORDER BY datetime(next_send_at) ASC
            LIMIT ?
            """,
            (to_iso(now_utc()), limit),
        ).fetchall()
    return rows


def _get_sequence_map() -> dict[str, dict[str, Any]]:
    return {seq.get("id"): seq for seq in _load_sequences() if seq.get("id")}


def _update_customer_state(phone: str, *, step: int, next_send_at: str | None, status: str) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            UPDATE marketing_customers
            SET current_step=?, next_send_at=?, status=?, updated_at=?
            WHERE phone=?
            """,
            (step, next_send_at, status, to_iso(now_utc()), phone),
        )
        conn.commit()


def _store_message_log(phone: str, sequence_id: str, step_index: int, text: str, provider_status: str, provider_message_id: str | None) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO marketing_messages (phone, sequence_id, step_index, text, provider_status, provider_message_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (phone, sequence_id, step_index, text, provider_status, provider_message_id, to_iso(now_utc())),
        )
        conn.commit()


def _already_sent_marketing_today(phone: str) -> bool:
    """Regra comercial: no máximo 1 mensagem de marketing por dia por contato (UTC)."""
    now = now_utc()
    day_start = datetime(now.year, now.month, now.day, tzinfo=UTC)
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM marketing_messages WHERE phone = ? AND datetime(created_at) >= datetime(?)",
            (phone, to_iso(day_start)),
        ).fetchone()
    return bool(row and row[0] > 0)


async def _process_due_customers_once() -> None:
    sequence_map = _get_sequence_map()
    due_customers = _get_due_customers()

    for cust in due_customers:
        phone = cust["phone"]
        seq_id = cust["current_sequence_id"]
        step_idx = int(cust["current_step"] or 0)

        seq = sequence_map.get(seq_id)
        if not seq:
            _update_customer_state(phone, step=0, next_send_at=None, status="idle")
            continue

        steps = seq.get("steps", [])
        if not steps:
            _update_customer_state(phone, step=0, next_send_at=None, status="idle")
            continue

        # Se acabou a sequência, entra em espera de nova compra
        if step_idx >= len(steps):
            repeat_hours = int(seq.get("repeat_last_every_hours", 0) or 0)
            if repeat_hours > 0:
                # regra: no máximo 1 mensagem de marketing/dia/contato
                if _already_sent_marketing_today(phone):
                    next_dt = now_utc() + timedelta(days=1)
                    _update_customer_state(phone, step=len(steps), next_send_at=to_iso(next_dt), status="active")
                    continue

                # repete último passo
                last_idx = len(steps) - 1
                step_obj = steps[last_idx]
                text = str(step_obj.get("text", "")).strip()
                if text:
                    try:
                        status, msg_id = await _send_text(phone, text)
                        _store_message_log(phone, seq_id, last_idx, text, status, msg_id)
                    except Exception as e:
                        logger.error(f"Erro no repeat_last para {phone}: {e}")
                next_dt = now_utc() + timedelta(hours=repeat_hours)
                _update_customer_state(phone, step=len(steps), next_send_at=to_iso(next_dt), status="active")
            else:
                _update_customer_state(phone, step=len(steps), next_send_at=None, status="waiting_purchase")
            continue

        step_obj = steps[step_idx]
        text = str(step_obj.get("text", "")).strip()
        delay_hours = int(step_obj.get("delay_hours_after", 24) or 24)

        if not text:
            _update_customer_state(phone, step=step_idx + 1, next_send_at=to_iso(now_utc()), status="active")
            continue

        # regra: no máximo 1 mensagem de marketing/dia/contato
        if _already_sent_marketing_today(phone):
            next_dt = now_utc() + timedelta(days=1)
            _update_customer_state(phone, step=step_idx, next_send_at=to_iso(next_dt), status="active")
            continue

        try:
            provider_status, provider_msg_id = await _send_text(phone, text)
            _store_message_log(phone, seq_id, step_idx, text, provider_status, provider_msg_id)
            next_dt = now_utc() + timedelta(hours=delay_hours)
            _update_customer_state(phone, step=step_idx + 1, next_send_at=to_iso(next_dt), status="active")
            logger.info(f"Mensagem de marketing enviada para {phone} seq={seq_id} step={step_idx}")
        except Exception as e:
            logger.error(f"Falha ao enviar marketing para {phone}: {e}")
            # retry leve em 30 minutos
            retry_dt = now_utc() + timedelta(minutes=30)
            _update_customer_state(phone, step=step_idx, next_send_at=to_iso(retry_dt), status="active")


async def _scheduler_loop() -> None:
    logger.info("Marketing scheduler iniciado")
    while True:
        try:
            await _process_due_customers_once()
        except Exception as e:
            logger.error(f"Erro no scheduler de marketing: {e}")
        await asyncio.sleep(SCHEDULER_INTERVAL_SECONDS)


def start_scheduler() -> None:
    global _scheduler_task
    _init_db()
    if _scheduler_task is None or _scheduler_task.done():
        _scheduler_task = asyncio.create_task(_scheduler_loop())


def stop_scheduler() -> None:
    global _scheduler_task
    if _scheduler_task and not _scheduler_task.done():
        _scheduler_task.cancel()


@router.post("/hotmart/webhook")
async def hotmart_webhook(
    request: Request,
    x_hotmart_hottok: str | None = Header(default=None),
) -> dict[str, Any]:
    payload = await request.json()

    # validação simples de segredo
    validate_shared_secret(x_hotmart_hottok, HOTMART_WEBHOOK_SECRET, "invalid_hotmart_signature")

    phone, product, purchase_id, approved_at, event, language = _extract_hotmart_fields(payload)

    # fallback oficial: sales-users por transaction
    if not phone:
        phone = await _phone_from_sales_users(purchase_id)

    if not phone or not product:
        logger.warning(f"Hotmart payload ignored: missing phone/product | event={event} | purchase_id={purchase_id} | keys={list((payload.get('data') or payload).keys())[:15]}")
        return {
            "status": "ignored",
            "reason": "missing_phone_or_product",
            "event": event,
            "purchase_id": purchase_id,
        }

    # processa apenas eventos de compra aprovada
    approved_markers = ["approved", "purchase_approved", "sale_approved", "purchase.approved"]
    if event and not any(m in event for m in approved_markers):
        return {
            "status": "ignored",
            "reason": "event_not_approved",
            "event": event,
        }

    name = None
    if isinstance(payload.get("data"), dict):
        buyer = payload.get("data", {}).get("buyer", {})
        if isinstance(buyer, dict):
            name = buyer.get("name")

    _save_purchase(purchase_id, phone, product, approved_at, payload)
    sequence = _upsert_customer_after_purchase(phone, name, product, approved_at, language)

    return {
        "status": "ok",
        "phone": phone,
        "product": product,
        "language": language,
        "sequence_started": sequence.get("id") if sequence else None,
    }


@router.post("/automation/run-once", dependencies=[Depends(require_admin_api_key)])
async def run_once() -> dict[str, Any]:
    await _process_due_customers_once()
    return {"status": "ok"}


@router.get("/automation/stats", dependencies=[Depends(require_admin_api_key)])
async def stats() -> dict[str, Any]:
    return marketing_repository.stats()


@router.get("/dashboard/data")
async def dashboard_data() -> dict[str, Any]:
    """Dashboard público (somente leitura): métricas + tabelas resumidas."""
    marketing_repository.init()
    s = marketing_repository.stats()

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        customers = conn.execute(
            """
            SELECT phone, status, current_sequence_id, current_step, next_send_at, last_product_bought, updated_at
            FROM marketing_customers
            ORDER BY datetime(updated_at) DESC
            LIMIT 200
            """
        ).fetchall()

        purchases = conn.execute(
            """
            SELECT purchase_id, phone, product, approved_at, created_at
            FROM marketing_purchases
            ORDER BY id DESC
            LIMIT 300
            """
        ).fetchall()

        messages = conn.execute(
            """
            SELECT phone, sequence_id, step_index, provider_status, created_at, text
            FROM marketing_messages
            ORDER BY id DESC
            LIMIT 300
            """
        ).fetchall()

    return {
        "stats": s,
        "customers": [dict(r) for r in customers],
        "purchases": [dict(r) for r in purchases],
        "messages": [dict(r) for r in messages],
        "generated_at": to_iso(now_utc()),
    }


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page() -> str:
    """Dashboard pública para operação de marketing."""
    return render_marketing_dashboard()
