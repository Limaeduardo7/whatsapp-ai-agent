import os
import json
import sqlite3
import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx
from fastapi import APIRouter, Header, HTTPException, Request

logger = logging.getLogger("marketing-automation")

router = APIRouter(prefix="/marketing", tags=["marketing"])

DB_PATH = os.getenv("DB_PATH", "./data/agent.db")
EVOLUTION_BASE_URL = os.getenv("EVOLUTION_BASE_URL", "http://127.0.0.1:8080")
EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE", "default")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "")
HOTMART_WEBHOOK_SECRET = os.getenv("HOTMART_WEBHOOK_SECRET", "")
SEQUENCES_FILE = os.getenv("SEQUENCES_FILE", "./data/automation_sequences.json")
SCHEDULER_INTERVAL_SECONDS = int(os.getenv("SCHEDULER_INTERVAL_SECONDS", "30"))

_scheduler_task: Optional[asyncio.Task] = None


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def to_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def from_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def normalize_phone(raw: Optional[str]) -> Optional[str]:
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

    # Brasil: adiciona DDI 55 se vier sem
    if len(digits) == 11 and not digits.startswith("55"):
        digits = f"55{digits}"
    if len(digits) == 10 and not digits.startswith("55"):
        digits = f"55{digits}"

    # telefone internacional típico
    if not (12 <= len(digits) <= 15):
        return None

    return digits


def _init_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS marketing_customers (
                phone TEXT PRIMARY KEY,
                name TEXT,
                status TEXT NOT NULL DEFAULT 'idle',
                current_sequence_id TEXT,
                current_step INTEGER DEFAULT 0,
                last_product_bought TEXT,
                next_send_at TEXT,
                last_purchase_at TEXT,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS marketing_purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_id TEXT,
                phone TEXT NOT NULL,
                product TEXT NOT NULL,
                approved_at TEXT,
                raw_payload TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_marketing_purchase_unique
            ON marketing_purchases(purchase_id, phone, product)
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS marketing_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT NOT NULL,
                sequence_id TEXT NOT NULL,
                step_index INTEGER NOT NULL,
                text TEXT NOT NULL,
                provider_status TEXT,
                provider_message_id TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def _load_sequences() -> List[Dict[str, Any]]:
    if not os.path.exists(SEQUENCES_FILE):
        return []
    with open(SEQUENCES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return data.get("sequences", [])
    return data if isinstance(data, list) else []


def _find_sequence_for_product(product_name: str) -> Optional[Dict[str, Any]]:
    product_name_l = product_name.lower().strip()
    for seq in _load_sequences():
        triggers = [p.lower().strip() for p in seq.get("trigger_products", [])]
        if any(tp in product_name_l or product_name_l in tp for tp in triggers):
            return seq
    return None


def _find_phone_deep(obj: Any) -> Optional[str]:
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


def _extract_hotmart_fields(payload: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], str]:
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

    return phone, product, purchase_id, approved_at, event


async def _send_text(phone: str, text: str) -> Tuple[str, Optional[str]]:
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


def _upsert_customer_after_purchase(phone: str, name: Optional[str], product: str, approved_at: Optional[str]) -> Optional[Dict[str, Any]]:
    sequence = _find_sequence_for_product(product)

    ts = to_iso(now_utc())
    purchase_dt = approved_at if approved_at else ts

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
                ts if sequence else None,
                purchase_dt,
                ts,
            ),
        )
        conn.commit()

    return sequence


def _save_purchase(purchase_id: Optional[str], phone: str, product: str, approved_at: Optional[str], raw_payload: Dict[str, Any]) -> None:
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


def _get_due_customers(limit: int = 50) -> List[sqlite3.Row]:
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


def _get_sequence_map() -> Dict[str, Dict[str, Any]]:
    return {seq.get("id"): seq for seq in _load_sequences() if seq.get("id")}


def _update_customer_state(phone: str, *, step: int, next_send_at: Optional[str], status: str) -> None:
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


def _store_message_log(phone: str, sequence_id: str, step_index: int, text: str, provider_status: str, provider_message_id: Optional[str]) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO marketing_messages (phone, sequence_id, step_index, text, provider_status, provider_message_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (phone, sequence_id, step_index, text, provider_status, provider_message_id, to_iso(now_utc())),
        )
        conn.commit()


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
    x_hotmart_hottok: Optional[str] = Header(default=None),
) -> Dict[str, Any]:
    payload = await request.json()

    # validação simples de segredo
    if HOTMART_WEBHOOK_SECRET:
        if not x_hotmart_hottok or x_hotmart_hottok != HOTMART_WEBHOOK_SECRET:
            raise HTTPException(status_code=401, detail="invalid_hotmart_signature")

    phone, product, purchase_id, approved_at, event = _extract_hotmart_fields(payload)

    if not phone or not product:
        logger.warning(f"Hotmart payload ignored: missing phone/product | event={event} | keys={list((payload.get('data') or payload).keys())[:15]}")
        return {
            "status": "ignored",
            "reason": "missing_phone_or_product",
            "event": event,
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
    sequence = _upsert_customer_after_purchase(phone, name, product, approved_at)

    return {
        "status": "ok",
        "phone": phone,
        "product": product,
        "sequence_started": sequence.get("id") if sequence else None,
    }


@router.post("/automation/run-once")
async def run_once() -> Dict[str, Any]:
    await _process_due_customers_once()
    return {"status": "ok"}


@router.get("/automation/stats")
async def stats() -> Dict[str, Any]:
    with sqlite3.connect(DB_PATH) as conn:
        total_customers = conn.execute("SELECT COUNT(*) FROM marketing_customers").fetchone()[0]
        active = conn.execute("SELECT COUNT(*) FROM marketing_customers WHERE status='active'").fetchone()[0]
        waiting = conn.execute("SELECT COUNT(*) FROM marketing_customers WHERE status='waiting_purchase'").fetchone()[0]
        purchases = conn.execute("SELECT COUNT(*) FROM marketing_purchases").fetchone()[0]
        messages = conn.execute("SELECT COUNT(*) FROM marketing_messages").fetchone()[0]
    return {
        "customers_total": total_customers,
        "customers_active": active,
        "customers_waiting_purchase": waiting,
        "purchases_total": purchases,
        "messages_sent_total": messages,
    }
