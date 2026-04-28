import asyncio
import json
import logging
import os
import sqlite3
import unicodedata
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import HTMLResponse

from src.config import get_settings
from src.marketing_dashboard import render_marketing_dashboard
from src.repositories import MarketingRepository
from src.security import require_admin_api_key, validate_shared_secret
from src.services import EvolutionClient, language_from_phone

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
    with sqlite3.connect(DB_PATH) as conn:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(marketing_customers)").fetchall()]
        if "language" not in cols:
            conn.execute("ALTER TABLE marketing_customers ADD COLUMN language TEXT")
        conn.commit()


def _load_sequences() -> list[dict[str, Any]]:
    if not os.path.exists(settings.sequences_file):
        return []
    with open(settings.sequences_file, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return data.get("sequences", [])
    return data if isinstance(data, list) else []


def _save_sequences(sequences: list[dict[str, Any]]) -> None:
    payload = {"sequences": sequences}
    parent = os.path.dirname(settings.sequences_file)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(settings.sequences_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _normalize_language(value: Any) -> str | None:
    if value is None:
        return None
    lang = str(value).strip().lower().replace("_", "-")
    if not lang:
        return None
    if lang.startswith("pt") or lang in {"br", "brazil", "brasil", "pt-br"}:
        return "pt-BR"
    if lang.startswith("en") or lang in {"us", "usa", "gb", "uk", "english", "en-us", "en-gb"}:
        return "en"
    if lang.startswith("es") or lang in {"spanish", "espanol", "español", "es-mx", "es-es"}:
        return "es"
    return None


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""
    txt = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    txt = txt.lower()
    return " ".join(txt.replace("_", " ").replace("-", " ").split())


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


def _language_from_country(value: Any) -> str | None:
    if value is None:
        return None
    country = str(value).strip().lower()
    if not country:
        return None
    if country in {"br", "brazil", "brasil"}:
        return "pt-BR"
    if country in {"us", "usa", "gb", "uk", "ca", "au"}:
        return "en"
    if country in {"es", "mx", "ar", "co", "cl", "pe", "uy", "py", "bo", "ec", "ve", "do", "gt", "hn", "ni", "sv", "pa", "cr"}:
        return "es"
    return None


def _language_from_product_alias(product_name: str | None) -> str | None:
    product_norm = _normalize_text(product_name)
    if not product_norm:
        return None
    best_score = -1
    best_langs: set[str] = set()
    for seq in _load_sequences():
        lang = _normalize_language(seq.get("language"))
        if not lang:
            continue
        for trigger in seq.get("trigger_products", []):
            trig = _normalize_text(str(trigger))
            if not trig:
                continue
            if trig in product_norm or product_norm in trig:
                score = len(trig)
                if score > best_score:
                    best_score = score
                    best_langs = {lang}
                elif score == best_score:
                    best_langs.add(lang)
    if len(best_langs) == 1:
        return next(iter(best_langs))
    return None


def _detect_language(payload: dict[str, Any], product_name: str | None) -> str | None:
    # 1) explicit language/locale fields
    explicit = _find_value_deep(payload, {"language", "lang", "locale"})
    language = _normalize_language(explicit)
    if language:
        return language

    # 2) product alias map (sequence triggers)
    language = _language_from_product_alias(product_name)
    if language:
        return language

    # 3) keyword heuristic on normalized product name
    product_l = _normalize_text(product_name)
    if any(token in product_l for token in ["the key to power", "chameleon", "rule of life", "algorithm of the universe", "master state", "quantum leap", "mastering inner demons"]):
        return "en"
    if any(token in product_l for token in ["la clave", "la regla", "algoritmo del", "camaleon", "estado maestro", "salto cuantico", "reprogramacion", "guia practica", "demonios internos"]):
        return "es"
    if any(token in product_l for token in ["a chave", "a regra", "algoritmo do", "estado mestre", "salto quantico", "reprogramacao", "guia pratico", "demonios internos"]):
        return "pt-BR"

    # 4) country fallback
    country = _find_value_deep(payload, {"country", "country_code", "country_iso"})
    language = _language_from_country(country)
    if language:
        return language

    # 5) sem confiança: não classificar
    return None


def _find_sequence_for_product(product_name: str, language: str | None = None) -> dict[str, Any] | None:
    product_name_l = _normalize_text(product_name)
    candidates = []
    for seq in _load_sequences():
        triggers = [_normalize_text(str(p)) for p in seq.get("trigger_products", [])]
        if any(tp and (tp in product_name_l or product_name_l in tp) for tp in triggers):
            candidates.append(seq)
    if language:
        lang_norm = _normalize_language(language)
        for seq in candidates:
            if _normalize_language(seq.get("language")) == lang_norm:
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


def _get_customer_language(phone: str) -> str | None:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT language FROM marketing_customers WHERE phone = ?", (phone,)).fetchone()
    if row and row[0]:
        return _normalize_language(row[0])
    return None


def _upsert_customer_after_purchase(phone: str, name: str | None, product: str, approved_at: str | None, language: str | None = None) -> dict[str, Any] | None:
    locked_language = _get_customer_language(phone)
    detected_language = _normalize_language(language) or _detect_language({"data": {"product": {"name": product}}}, product)
    effective_language = locked_language or detected_language
    sequence = _find_sequence_for_product(product, effective_language) if effective_language else None

    now = now_utc()
    ts = to_iso(now)
    purchase_dt = approved_at if approved_at else ts
    first_send_at = to_iso(now + timedelta(days=1))

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO marketing_customers (phone, name, status, current_sequence_id, current_step, last_product_bought, next_send_at, last_purchase_at, updated_at, language)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(phone) DO UPDATE SET
              name=excluded.name,
              status=excluded.status,
              current_sequence_id=excluded.current_sequence_id,
              current_step=excluded.current_step,
              last_product_bought=excluded.last_product_bought,
              next_send_at=excluded.next_send_at,
              last_purchase_at=excluded.last_purchase_at,
              updated_at=excluded.updated_at,
              language=COALESCE(marketing_customers.language, excluded.language)
            """,
            (
                phone,
                name,
                "active" if (sequence and effective_language) else "idle",
                sequence.get("id") if sequence else None,
                0,
                product,
                first_send_at if sequence else None,
                purchase_dt,
                ts,
                effective_language,
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


def _purchase_count_for_phone(phone: str) -> int:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT COUNT(*) FROM marketing_purchases WHERE phone = ?", (phone,)).fetchone()
    return int(row[0] if row and row[0] is not None else 0)


def _welcome_message_for_first_purchase(language: str, product: str) -> str:
    product_name = str(product).strip() or "seu produto"
    if language == "es":
        return (
            f"¡Bienvenido(a)! Confirmamos tu compra de \"{product_name}\". "
            "¿Ya lograste acceder al material o quieres que te guíe en 1 minuto?"
        )
    if language == "en":
        return (
            f"Welcome! Your purchase of \"{product_name}\" is confirmed. "
            "Have you already accessed the material, or want me to guide you in 1 minute?"
        )
    return (
        f"Bem-vindo(a)! Sua compra de \"{product_name}\" foi confirmada. "
        "Você já conseguiu acessar o material ou quer que eu te guie em 1 minuto?"
    )


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


def _text_send_count_for_phone(phone: str, text: str) -> int:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM marketing_messages WHERE phone = ? AND text = ?",
            (phone, text),
        ).fetchone()
    return int(row[0] if row and row[0] is not None else 0)


def _ensure_non_repeated_text(phone: str, text: str) -> str:
    count = _text_send_count_for_phone(phone, text)
    if count == 0:
        return text

    suffixes = [
        "\n\nNota rápida: se quiser, eu te explico em 1 minuto como aplicar isso no seu caso.",
        "\n\nResumo prático: esse é o próximo passo lógico para acelerar seu resultado com consistência.",
        "\n\nSe fizer sentido, te mostro agora o caminho mais direto para começar.",
    ]
    idx = min(count - 1, len(suffixes) - 1)
    return f"{text}{suffixes[idx]}"


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

        cust_lang = _normalize_language(cust["language"]) if "language" in cust.keys() else None
        phone_lang = language_from_phone(phone)
        seq_lang = _normalize_language(seq.get("language"))
        effective_lang = cust_lang or phone_lang
        if not effective_lang or not seq_lang or effective_lang != seq_lang:
            logger.warning(
                f"Skipping marketing send due to language mismatch/unknown | phone={phone} customer_lang={cust_lang} phone_lang={phone_lang} seq_lang={seq_lang}"
            )
            _update_customer_state(phone, step=step_idx, next_send_at=None, status="idle")
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
                    send_text = _ensure_non_repeated_text(phone, text)
                    try:
                        status, msg_id = await _send_text(phone, send_text)
                        _store_message_log(phone, seq_id, last_idx, send_text, status, msg_id)
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
            send_text = _ensure_non_repeated_text(phone, text)
            provider_status, provider_msg_id = await _send_text(phone, send_text)
            _store_message_log(phone, seq_id, step_idx, send_text, provider_status, provider_msg_id)
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

    resolved_language = _normalize_language(language) or _detect_language(payload, product) or language_from_phone(phone)

    _save_purchase(purchase_id, phone, product, approved_at, payload)

    # Mensagem complementar: somente na primeira compra do contato
    purchase_count = _purchase_count_for_phone(phone)
    if purchase_count == 1 and resolved_language:
        welcome_text = _welcome_message_for_first_purchase(resolved_language, product)
        try:
            provider_status, provider_msg_id = await _send_text(phone, welcome_text)
            _store_message_log(phone, "welcome_first_purchase", 0, welcome_text, provider_status, provider_msg_id)
        except Exception as e:
            logger.error(f"Falha ao enviar mensagem de boas-vindas para {phone}: {e}")

    sequence = _upsert_customer_after_purchase(phone, name, product, approved_at, resolved_language)

    return {
        "status": "ok",
        "phone": phone,
        "product": product,
        "language": resolved_language,
        "sequence_started": sequence.get("id") if sequence else None,
        "skipped": sequence is None,
        "skip_reason": "language_not_identified_or_no_sequence" if sequence is None else None,
    }


@router.post("/automation/run-once", dependencies=[Depends(require_admin_api_key)])
async def run_once() -> dict[str, Any]:
    await _process_due_customers_once()
    return {"status": "ok"}


@router.get("/automation/stats", dependencies=[Depends(require_admin_api_key)])
async def stats() -> dict[str, Any]:
    return marketing_repository.stats()


@router.get("/sequences", dependencies=[Depends(require_admin_api_key)])
async def list_sequences() -> dict[str, Any]:
    return {"status": "ok", "sequences": _load_sequences()}


@router.put("/sequences/{sequence_id}", dependencies=[Depends(require_admin_api_key)])
async def update_sequence(sequence_id: str, request: Request) -> dict[str, Any]:
    body = await request.json()
    if not isinstance(body, dict):
        return {"status": "error", "message": "invalid_body"}

    sequences = _load_sequences()
    idx = next((i for i, s in enumerate(sequences) if str(s.get("id")) == sequence_id), None)
    if idx is None:
        return {"status": "error", "message": "sequence_not_found", "sequence_id": sequence_id}

    current = dict(sequences[idx])
    next_seq = dict(current)

    allowed_fields = {"name", "language", "goal", "trigger_products", "target_product", "repeat_last_every_hours", "steps"}
    for k, v in body.items():
        if k in allowed_fields:
            next_seq[k] = v

    # validações mínimas
    steps = next_seq.get("steps")
    if not isinstance(steps, list) or not steps:
        return {"status": "error", "message": "invalid_steps"}
    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            return {"status": "error", "message": f"invalid_step_{i}"}
        text = str(step.get("text") or "").strip()
        if not text:
            return {"status": "error", "message": f"empty_step_text_{i}"}
        if not any(term in text.upper() for term in ["SAIR", "STOP", "SALIR"]):
            return {"status": "error", "message": f"missing_opt_out_in_step_{i}"}
        try:
            step["delay_hours_after"] = int(step.get("delay_hours_after", 24) or 24)
        except Exception:
            return {"status": "error", "message": f"invalid_delay_in_step_{i}"}

    if _normalize_language(next_seq.get("language")) is None:
        return {"status": "error", "message": "invalid_language"}

    next_seq["id"] = current.get("id")
    sequences[idx] = next_seq
    _save_sequences(sequences)

    return {"status": "ok", "sequence_id": sequence_id, "sequence": next_seq}


def _load_price_map() -> dict[str, float]:
    raw = os.getenv("PRODUCT_PRICE_MAP", "{}")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    prices: dict[str, float] = {}
    for product, value in data.items():
        try:
            prices[str(product).strip().lower()] = float(value)
        except (TypeError, ValueError):
            continue
    return prices


def _row_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def _extract_tracking_fields(raw_payload: Any) -> dict[str, str]:
    if isinstance(raw_payload, str):
        try:
            raw_payload = json.loads(raw_payload)
        except Exception:
            return {}
    if not isinstance(raw_payload, dict):
        return {}

    data = raw_payload.get("data") if isinstance(raw_payload.get("data"), dict) else raw_payload
    purchase = data.get("purchase") if isinstance(data.get("purchase"), dict) else {}
    tracking = purchase.get("tracking") if isinstance(purchase.get("tracking"), dict) else {}

    def _get(obj: dict[str, Any], key: str) -> str:
        val = obj.get(key)
        return str(val).strip() if val is not None else ""

    return {
        "utm_source": _get(data, "utm_source") or _get(tracking, "utm_source"),
        "utm_medium": _get(data, "utm_medium") or _get(tracking, "utm_medium"),
        "utm_campaign": _get(data, "utm_campaign") or _get(tracking, "utm_campaign"),
        "utm_content": _get(data, "utm_content") or _get(tracking, "utm_content"),
        "sck": _get(data, "sck") or _get(tracking, "source_sck"),
        "external_code": _get(tracking, "external_code"),
    }


def _extract_purchase_amount(raw_payload: Any) -> tuple[float | None, str | None]:
    if isinstance(raw_payload, str):
        try:
            raw_payload = json.loads(raw_payload)
        except Exception:
            return None, None
    if not isinstance(raw_payload, dict):
        return None, None

    data = raw_payload.get("data") if isinstance(raw_payload.get("data"), dict) else raw_payload
    purchase = data.get("purchase") if isinstance(data.get("purchase"), dict) else {}
    price = purchase.get("price") if isinstance(purchase.get("price"), dict) else {}

    value = price.get("value") if isinstance(price, dict) else None
    currency = str(price.get("currency_code") or "").strip().upper() if isinstance(price, dict) else ""

    if value is None:
        # fallback para payloads simplificados
        value = data.get("value") or purchase.get("value")
    try:
        amount = float(value) if value is not None else None
    except (TypeError, ValueError):
        amount = None

    return amount, (currency or None)


# ─── Data-science helpers ──────────────────────────────────────────────────────

def _safe_isoparse(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(UTC)
    except Exception:
        return None


def _percentile(sorted_lst: list[float], p: float) -> float:
    if not sorted_lst:
        return 0.0
    idx = max(0, int(len(sorted_lst) * p / 100) - 1)
    return sorted_lst[min(idx, len(sorted_lst) - 1)]


def _compute_engagement_scores(
    customers: list[dict[str, Any]],
    messages: list[dict[str, Any]],
    sequence_lengths: dict[str, int],
) -> dict[str, int]:
    """phone → score 0-100  (completion 60% + recency 30% + status 10%)."""
    now = datetime.now(UTC)
    msgs_by_phone: dict[str, list[dict[str, Any]]] = {}
    for m in messages:
        msgs_by_phone.setdefault(m.get("phone", ""), []).append(m)

    scores: dict[str, int] = {}
    for c in customers:
        phone = c.get("phone", "")
        seq_id = c.get("current_sequence_id") or ""
        total_steps = max(sequence_lengths.get(seq_id, 1), 1)
        phone_msgs = msgs_by_phone.get(phone, [])

        steps_done = len({m.get("step_index", 0) for m in phone_msgs})
        completion = (steps_done / total_steps) * 0.60

        last_dates = [_safe_isoparse(m.get("created_at")) for m in phone_msgs]
        last_dates = [d for d in last_dates if d]
        if last_dates:
            days_ago = (now - max(last_dates)).days
            recency = max(0.0, 1.0 - days_ago / 30.0) * 0.30
        else:
            recency = 0.0

        status_bonus = 0.10 if c.get("status") == "active" else 0.0
        scores[phone] = min(100, round((completion + recency + status_bonus) * 100))
    return scores


def _compute_cohort_data(
    purchases: list[dict[str, Any]],
    messages: list[dict[str, Any]],
) -> dict[str, Any]:
    """Weekly cohort: for each purchase-week cohort, % who reached each step."""
    from collections import defaultdict

    phone_first_week: dict[str, str] = {}
    for p in sorted(purchases, key=lambda x: x.get("created_at") or x.get("approved_at") or ""):
        phone = p.get("phone") or ""
        raw = p.get("created_at") or p.get("approved_at")
        d = _safe_isoparse(raw)
        if phone and d and phone not in phone_first_week:
            phone_first_week[phone] = d.strftime("%Y-W%V")

    phone_max_step: dict[str, int] = {}
    for m in messages:
        phone = m.get("phone") or ""
        try:
            step = int(m.get("step_index") or 0) + 1
        except (ValueError, TypeError):
            step = 1
        if phone:
            phone_max_step[phone] = max(phone_max_step.get(phone, 0), step)

    week_phones: dict[str, list[str]] = defaultdict(list)
    for phone, week in phone_first_week.items():
        week_phones[week].append(phone)

    weeks = sorted(week_phones.keys())[-10:]
    max_step_seen = max(phone_max_step.values(), default=3)
    steps = list(range(1, min(max_step_seen + 1, 9)))

    data: list[list[Any]] = []
    for wi, week in enumerate(weeks):
        phones = week_phones[week]
        total = len(phones)
        if total == 0:
            continue
        for si, step in enumerate(steps):
            reached = sum(1 for ph in phones if phone_max_step.get(ph, 0) >= step)
            rate = round(reached / total * 100, 1)
            data.append([wi, si, rate])

    return {
        "x_labels": [f"Step {s}" for s in steps],
        "y_labels": weeks,
        "data": data,
    }


def _compute_sequence_analytics(
    customers: list[dict[str, Any]],
    purchases: list[dict[str, Any]],
    messages: list[dict[str, Any]],
    sequences: list[dict[str, Any]],
    sequence_lengths: dict[str, int],
) -> list[dict[str, Any]]:
    """Per-sequence: step completion rates, conversion rate, avg days to complete."""
    from collections import defaultdict

    seq_customers: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for c in customers:
        seq_id = c.get("current_sequence_id") or ""
        if seq_id:
            seq_customers[seq_id].append(c)

    seq_step_phones: dict[str, dict[int, set[str]]] = defaultdict(lambda: defaultdict(set))
    for m in messages:
        seq_id = m.get("sequence_id") or ""
        phone = m.get("phone") or ""
        try:
            step = int(m.get("step_index") or 0)
        except (ValueError, TypeError):
            step = 0
        if seq_id and phone:
            seq_step_phones[seq_id][step].add(phone)

    phone_first_purchase: dict[str, datetime] = {}
    for p in sorted(purchases, key=lambda x: x.get("created_at") or ""):
        phone = p.get("phone") or ""
        d = _safe_isoparse(p.get("created_at") or p.get("approved_at"))
        if phone and d and phone not in phone_first_purchase:
            phone_first_purchase[phone] = d

    result: list[dict[str, Any]] = []
    for seq in sequences:
        seq_id = seq.get("id") or ""
        n_steps = sequence_lengths.get(seq_id, 0)
        custs = seq_customers.get(seq_id, [])
        total = len(custs)

        step_rates = []
        for i in range(n_steps):
            count = len(seq_step_phones.get(seq_id, {}).get(i, set()))
            step_rates.append({
                "step": i + 1,
                "count": count,
                "rate": round(count / max(total, 1) * 100, 1),
            })

        converted = sum(1 for c in custs if c.get("status") == "waiting_purchase")
        conversion_rate = round(converted / max(total, 1) * 100, 1)

        days_list: list[float] = []
        for c in custs:
            if c.get("status") != "waiting_purchase":
                continue
            phone = c.get("phone") or ""
            t0 = phone_first_purchase.get(phone)
            t1 = _safe_isoparse(c.get("updated_at"))
            if t0 and t1:
                days_list.append((t1 - t0).total_seconds() / 86400)

        result.append({
            "id": seq_id,
            "name": seq.get("name") or seq_id,
            "language": seq.get("language"),
            "total_customers": total,
            "n_steps": n_steps,
            "step_rates": step_rates,
            "conversion_rate": conversion_rate,
            "converted": converted,
            "avg_days_to_complete": round(sum(days_list) / len(days_list), 1) if days_list else None,
        })

    return sorted(result, key=lambda x: x["conversion_rate"], reverse=True)


def _compute_attribution_comparison(purchases: list[dict[str, Any]]) -> dict[str, Any]:
    """First-touch vs last-touch side by side."""
    from collections import defaultdict

    phone_purchases: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for p in purchases:
        phone = p.get("phone") or ""
        if phone:
            phone_purchases[phone].append(p)

    def src(p: dict[str, Any]) -> str:
        t = _extract_tracking_fields(p.get("raw_payload"))
        return (
            t.get("utm_source") or t.get("utm_campaign") or
            t.get("sck") or t.get("external_code") or "sem_tracking"
        ).strip().lower()

    first_touch: dict[str, int] = {}
    last_touch: dict[str, int] = {}
    for ps in phone_purchases.values():
        sorted_ps = sorted(ps, key=lambda x: x.get("created_at") or x.get("approved_at") or "")
        f = src(sorted_ps[0])
        l = src(sorted_ps[-1])
        first_touch[f] = first_touch.get(f, 0) + 1
        last_touch[l] = last_touch.get(l, 0) + 1

    def top(d: dict[str, int], n: int = 8) -> list[dict[str, Any]]:
        return [{"source": k, "count": v} for k, v in sorted(d.items(), key=lambda x: x[1], reverse=True)[:n]]

    return {"first_touch": top(first_touch), "last_touch": top(last_touch)}


def _compute_time_to_conversion(
    customers: list[dict[str, Any]],
    purchases: list[dict[str, Any]],
) -> dict[str, Any]:
    """Distribution of days from first purchase to sequence completion."""
    phone_first: dict[str, datetime] = {}
    for p in sorted(purchases, key=lambda x: x.get("created_at") or ""):
        phone = p.get("phone") or ""
        d = _safe_isoparse(p.get("created_at") or p.get("approved_at"))
        if phone and d and phone not in phone_first:
            phone_first[phone] = d

    days_list: list[float] = []
    for c in customers:
        if c.get("status") != "waiting_purchase":
            continue
        phone = c.get("phone") or ""
        t0 = phone_first.get(phone)
        t1 = _safe_isoparse(c.get("updated_at"))
        if t0 and t1:
            days = (t1 - t0).total_seconds() / 86400
            if 0 <= days <= 180:
                days_list.append(days)

    if not days_list:
        return {"available": False}

    days_sorted = sorted(days_list)
    n = len(days_sorted)
    buckets = [(0, 3), (3, 7), (7, 14), (14, 21), (21, 30), (30, 60), (60, 180)]
    distribution = [
        {"label": f"{lo}–{hi}d", "count": sum(1 for d in days_list if lo <= d < hi)}
        for lo, hi in buckets
    ]
    return {
        "available": True,
        "n": n,
        "mean": round(sum(days_list) / n, 1),
        "min": round(days_sorted[0], 1),
        "p25": round(_percentile(days_sorted, 25), 1),
        "median": round(_percentile(days_sorted, 50), 1),
        "p75": round(_percentile(days_sorted, 75), 1),
        "max": round(days_sorted[-1], 1),
        "distribution": distribution,
    }


def _sequence_validation_issues(sequences: list[dict[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for seq in sequences:
        seq_id = str(seq.get("id") or "sem_id")
        language = seq.get("language")
        if seq_id in seen_ids:
            issues.append({"severity": "error", "sequence_id": seq_id, "message": "ID duplicado."})
        seen_ids.add(seq_id)
        if language not in {"pt-BR", "en", "es"}:
            issues.append({"severity": "warning", "sequence_id": seq_id, "message": "Idioma ausente ou inválido."})
        if not seq.get("target_product"):
            issues.append({"severity": "error", "sequence_id": seq_id, "message": "Produto alvo ausente."})
        if not seq.get("trigger_products"):
            issues.append({"severity": "error", "sequence_id": seq_id, "message": "Gatilhos ausentes."})
        steps = seq.get("steps") or []
        if not steps:
            issues.append({"severity": "error", "sequence_id": seq_id, "message": "Sequência sem mensagens."})
        for index, step in enumerate(steps):
            text = str(step.get("text") or "")
            if len(text) > 300:
                issues.append({"severity": "warning", "sequence_id": seq_id, "step": index, "message": f"Mensagem com {len(text)} caracteres."})
            if not any(term in text.upper() for term in ["SAIR", "STOP", "SALIR"]):
                issues.append({"severity": "warning", "sequence_id": seq_id, "step": index, "message": "Opt-out ausente."})
            if not step.get("delay_hours_after"):
                issues.append({"severity": "info", "sequence_id": seq_id, "step": index, "message": "Delay não configurado explicitamente."})
    return issues


def _build_dashboard_analytics(
    customers: list[dict[str, Any]],
    purchases: list[dict[str, Any]],
    messages: list[dict[str, Any]],
    sequences: list[dict[str, Any]],
) -> dict[str, Any]:
    price_map = _load_price_map()
    sequence_lengths: dict[str, int] = {seq.get("id"): len(seq.get("steps") or []) for seq in sequences}

    failed_set = {
        id(row) for row in messages
        if any(t in str(row.get("provider_status") or "").lower() for t in ["fail", "error", "timeout", "denied"])
    }
    failed_messages = [r for r in messages if id(r) in failed_set]
    successful_messages = [r for r in messages if id(r) not in failed_set and str(r.get("provider_status") or "").strip()]

    completed_customers = [
        r for r in customers
        if r.get("status") == "waiting_purchase"
        or int(r.get("current_step") or 0) >= sequence_lengths.get(r.get("current_sequence_id"), 9999)
    ]

    # ── Purchase aggregations ──────────────────────────────────────────────────
    purchases_by_product: dict[str, dict[str, Any]] = {}
    purchases_by_phone: dict[str, int] = {}
    purchases_by_tracking_source: dict[str, int] = {}
    estimated_revenue = 0.0
    has_revenue = False
    real_revenue_by_currency: dict[str, float] = {}
    attributed_sales = 0
    attributed_revenue = 0.0
    attributed_real_revenue_by_currency: dict[str, float] = {}

    for row in purchases:
        product = str(row.get("product") or "Sem produto")
        price = price_map.get(product.strip().lower())
        if price is not None:
            estimated_revenue += price
            has_revenue = True
        entry = purchases_by_product.setdefault(product, {"product": product, "count": 0, "estimated_revenue": 0.0})
        entry["count"] += 1
        if price is not None:
            entry["estimated_revenue"] += price

        phone = str(row.get("phone") or "")
        purchases_by_phone[phone] = purchases_by_phone.get(phone, 0) + 1

        raw_payload = row.get("raw_payload")
        tracking = _extract_tracking_fields(raw_payload)
        amount, currency = _extract_purchase_amount(raw_payload)
        if amount is not None:
            ccy = currency or "UNK"
            real_revenue_by_currency[ccy] = real_revenue_by_currency.get(ccy, 0.0) + amount

        source = (
            tracking.get("utm_source") or tracking.get("utm_campaign") or
            tracking.get("sck") or tracking.get("external_code") or "sem_tracking"
        ).strip().lower()
        purchases_by_tracking_source[source] = purchases_by_tracking_source.get(source, 0) + 1

        sck = (tracking.get("sck") or "").lower()
        utm_source = (tracking.get("utm_source") or "").lower()
        if ("wa_" in sck) or (utm_source == "whatsapp"):
            attributed_sales += 1
            if price is not None:
                attributed_revenue += price
            if amount is not None:
                ccy = currency or "UNK"
                attributed_real_revenue_by_currency[ccy] = attributed_real_revenue_by_currency.get(ccy, 0.0) + amount

    # ── Message / sequence aggregations ───────────────────────────────────────
    customers_by_sequence: dict[str, int] = {}
    for row in customers:
        seq_id = str(row.get("current_sequence_id") or "Sem sequência")
        customers_by_sequence[seq_id] = customers_by_sequence.get(seq_id, 0) + 1

    messages_by_sequence: dict[str, dict[str, Any]] = {}
    step_counts: dict[int, int] = {}
    for row in messages:
        seq_id = str(row.get("sequence_id") or "Sem sequência")
        entry = messages_by_sequence.setdefault(seq_id, {"sequence_id": seq_id, "sent": 0, "failed": 0})
        entry["sent"] += 1
        if id(row) in failed_set:
            entry["failed"] += 1
        try:
            step = int(row.get("step_index") or 0)
        except (TypeError, ValueError):
            step = 0
        step_counts[step] = step_counts.get(step, 0) + 1

    last_purchase_at = max((r.get("created_at") or r.get("approved_at") or "" for r in purchases), default="")
    last_message_at = max((r.get("created_at") or "" for r in messages), default="")

    # ── Dynamic funnel with conversion rates ──────────────────────────────────
    seq_started = len([r for r in customers if r.get("current_sequence_id")])
    repeat_buyers = len([ph for ph, cnt in purchases_by_phone.items() if ph and cnt > 1])
    max_step_shown = min(max(step_counts.keys(), default=2), 6)

    funnel_raw = [
        ("Compras aprovadas",   len(purchases)),
        ("Sequência iniciada",  seq_started),
        *[(f"Step {i + 1} enviado", step_counts.get(i, 0)) for i in range(max_step_shown + 1) if step_counts.get(i, 0) > 0],
        ("Repeat buyers",       repeat_buyers),
        ("Sequência concluída", len(completed_customers)),
    ]
    baseline = max(funnel_raw[0][1], 1)
    funnel: list[dict[str, Any]] = []
    prev_value = baseline
    for stage, value in funnel_raw:
        funnel.append({
            "stage": stage,
            "value": value,
            "rate_vs_top": round(value / baseline * 100, 1),
            "step_rate": round(value / max(prev_value, 1) * 100, 1),
        })
        prev_value = value

    # ── Advanced data-science analytics ───────────────────────────────────────
    engagement_scores = _compute_engagement_scores(customers, messages, sequence_lengths)
    cohort_data = _compute_cohort_data(purchases, messages)
    sequence_analytics = _compute_sequence_analytics(customers, purchases, messages, sequences, sequence_lengths)
    attribution_comparison = _compute_attribution_comparison(purchases)
    time_to_conversion = _compute_time_to_conversion(customers, purchases)

    # Engagement score distribution histogram (buckets of 10)
    score_buckets = [0] * 10
    for sc in engagement_scores.values():
        bucket = min(int(sc // 10), 9)
        score_buckets[bucket] += 1
    engagement_distribution = [
        {"range": f"{i * 10}–{i * 10 + 9}", "count": score_buckets[i]}
        for i in range(10)
    ]

    # Message failure rate trend (last 7 days)
    now = datetime.now(UTC)
    failure_trend: list[dict[str, Any]] = []
    for days_back in range(6, -1, -1):
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0) - __import__("datetime").timedelta(days=days_back)
        day_end = day_start + __import__("datetime").timedelta(days=1)
        day_msgs = [
            m for m in messages
            if day_start <= (_safe_isoparse(m.get("created_at")) or datetime.min.replace(tzinfo=UTC)) < day_end
        ]
        day_failed = sum(1 for m in day_msgs if id(m) in failed_set)
        failure_trend.append({
            "day": day_start.strftime("%d/%m"),
            "total": len(day_msgs),
            "failed": day_failed,
            "rate": round(day_failed / max(len(day_msgs), 1) * 100, 1),
        })

    return {
        # ── existing keys (unchanged API contract) ──────────────────────────
        "funnel": funnel,
        "health": {
            "status": "attention" if failed_messages else "ok",
            "marketing_enabled": settings.marketing_automation_enabled,
            "ai_agent_enabled": settings.ai_agent_enabled,
            "scheduler_interval_seconds": SCHEDULER_INTERVAL_SECONDS,
            "sequences_count": len(sequences),
            "last_purchase_at": last_purchase_at,
            "last_message_at": last_message_at,
            "failed_messages": len(failed_messages),
            "successful_messages": len(successful_messages),
            "active_customers": len([r for r in customers if r.get("status") == "active"]),
            "completed_customers": len(completed_customers),
        },
        "performance": {
            "customers_by_sequence": [
                {"sequence_id": k, "customers": v}
                for k, v in sorted(customers_by_sequence.items(), key=lambda x: x[1], reverse=True)
            ],
            "messages_by_sequence": sorted(messages_by_sequence.values(), key=lambda x: x["sent"], reverse=True),
            "purchases_by_product": sorted(purchases_by_product.values(), key=lambda x: x["count"], reverse=True),
            "purchases_by_tracking_source": [
                {"source": k, "count": v}
                for k, v in sorted(purchases_by_tracking_source.items(), key=lambda x: x[1], reverse=True)
            ],
            "attributed_sales_whatsapp": attributed_sales,
            "attributed_revenue_whatsapp": attributed_revenue if has_revenue else None,
            "real_revenue_by_currency": [
                {"currency": k, "value": round(v, 2)}
                for k, v in sorted(real_revenue_by_currency.items())
            ],
            "attributed_real_revenue_by_currency": [
                {"currency": k, "value": round(v, 2)}
                for k, v in sorted(attributed_real_revenue_by_currency.items())
            ],
            "estimated_revenue": estimated_revenue if has_revenue else None,
            "revenue_configured": has_revenue,
        },
        "failures": failed_messages[:50],
        "sequence_issues": _sequence_validation_issues(sequences),
        # ── new data-science keys ───────────────────────────────────────────
        "engagement_scores": engagement_scores,
        "engagement_distribution": engagement_distribution,
        "cohort_data": cohort_data,
        "sequence_analytics": sequence_analytics,
        "attribution_comparison": attribution_comparison,
        "time_to_conversion": time_to_conversion,
        "failure_trend": failure_trend,
    }


def _set_customer_state(phone: str, *, status: str, current_step: int | None = None, next_send_at: str | None = None) -> None:
    marketing_repository.init()
    fields = ["status = ?", "next_send_at = ?", "updated_at = ?"]
    values: list[Any] = [status, next_send_at, to_iso(now_utc())]
    if current_step is not None:
        fields.insert(1, "current_step = ?")
        values.insert(1, current_step)
    values.append(phone)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(f"UPDATE marketing_customers SET {', '.join(fields)} WHERE phone = ?", values)
        conn.commit()


@router.post("/automation/customers/{phone}/pause", dependencies=[Depends(require_admin_api_key)])
async def pause_customer(phone: str) -> dict[str, Any]:
    _set_customer_state(phone, status="paused", next_send_at=None)
    return {"status": "ok", "phone": phone, "action": "paused"}


@router.post("/automation/customers/{phone}/reactivate", dependencies=[Depends(require_admin_api_key)])
async def reactivate_customer(phone: str) -> dict[str, Any]:
    _set_customer_state(phone, status="active", next_send_at=to_iso(now_utc()))
    return {"status": "ok", "phone": phone, "action": "reactivated"}


@router.post("/automation/customers/{phone}/restart", dependencies=[Depends(require_admin_api_key)])
async def restart_customer_sequence(phone: str) -> dict[str, Any]:
    _set_customer_state(phone, status="active", current_step=0, next_send_at=to_iso(now_utc()))
    return {"status": "ok", "phone": phone, "action": "restarted"}


@router.post("/automation/customers/{phone}/force-next", dependencies=[Depends(require_admin_api_key)])
async def force_next_customer_message(phone: str) -> dict[str, Any]:
    _set_customer_state(phone, status="active", next_send_at=to_iso(now_utc()))
    return {"status": "ok", "phone": phone, "action": "force_next"}


@router.post("/automation/customers/{phone}/opt-out", dependencies=[Depends(require_admin_api_key)])
async def opt_out_customer(phone: str) -> dict[str, Any]:
    marketing_repository.init()
    ts = to_iso(now_utc())
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO chat_profiles (phone, opted_out, updated_at, last_seen_at)
            VALUES (?, 1, ?, ?)
            ON CONFLICT(phone) DO UPDATE SET
              opted_out=1,
              updated_at=excluded.updated_at,
              last_seen_at=excluded.last_seen_at
            """,
            (phone, ts, ts),
        )
        conn.execute(
            "UPDATE marketing_customers SET status='opted_out', next_send_at=NULL, updated_at=? WHERE phone=?",
            (ts, phone),
        )
        conn.commit()
    return {"status": "ok", "phone": phone, "action": "opted_out"}


@router.get("/dashboard/data")
async def dashboard_data() -> dict[str, Any]:
    """Dashboard público (somente leitura): métricas + tabelas resumidas."""
    marketing_repository.init()
    s = marketing_repository.stats()
    sequences = _load_sequences()

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        customers = conn.execute(
            """
            SELECT mc.phone, mc.name, mc.status, mc.current_sequence_id, mc.current_step, mc.next_send_at,
                   mc.last_product_bought, mc.last_purchase_at, mc.updated_at, COALESCE(cp.opted_out, 0) AS opted_out
            FROM marketing_customers mc
            LEFT JOIN chat_profiles cp ON cp.phone = mc.phone
            ORDER BY datetime(mc.updated_at) DESC
            LIMIT 200
            """
        ).fetchall()

        purchases = conn.execute(
            """
            SELECT purchase_id, phone, product, approved_at, created_at, raw_payload
            FROM marketing_purchases
            ORDER BY id DESC
            LIMIT 300
            """
        ).fetchall()

        messages = conn.execute(
            """
            SELECT id, phone, sequence_id, step_index, provider_status, provider_message_id, created_at, text
            FROM marketing_messages
            ORDER BY id DESC
            LIMIT 300
            """
        ).fetchall()

    customers_data = _row_dicts(customers)
    purchases_data = _row_dicts(purchases)
    messages_data = _row_dicts(messages)

    analytics = _build_dashboard_analytics(customers_data, purchases_data, messages_data, sequences)
    purchases_public = [{k: v for k, v in row.items() if k != "raw_payload"} for row in purchases_data]

    # Attach engagement score to each customer record
    eng_scores = analytics.get("engagement_scores", {})
    for c in customers_data:
        c["engagement_score"] = eng_scores.get(c.get("phone", ""), 0)

    return {
        "stats": s,
        "customers": customers_data,
        "purchases": purchases_public,
        "messages": messages_data,
        "sequences": sequences,
        "analytics": analytics,
        "generated_at": to_iso(now_utc()),
    }


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page() -> str:
    """Dashboard pública para operação de marketing."""
    return render_marketing_dashboard()
