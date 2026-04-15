#!/usr/bin/env python3
"""Automação simples de funil com split A/B e logging de eventos.

Uso:
  python3 funnel_automation.py assign --lead 5511999999999
  python3 funnel_automation.py event --lead 5511999999999 --event lead_created
  python3 funnel_automation.py event --lead 5511999999999 --event first_message_sent --meta '{"channel":"whatsapp"}'
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
EVENTS_CSV = DATA_DIR / "funnel_events.csv"
ASSIGNMENTS_CSV = DATA_DIR / "lead_assignments.csv"

VALID_EVENTS = {
    "lead_created",
    "first_message_sent",
    "first_reply_received",
    "qualified",
    "proposal_sent",
    "objection_logged",
    "closed_won",
    "closed_lost",
}


def ensure_files() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not ASSIGNMENTS_CSV.exists():
        with ASSIGNMENTS_CSV.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["lead_id", "variant", "assigned_at"])

    if not EVENTS_CSV.exists():
        with EVENTS_CSV.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "lead_id", "variant", "event", "meta_json"])


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def assign_variant(lead_id: str) -> str:
    digest = hashlib.sha256(lead_id.encode("utf-8")).hexdigest()
    return "A" if int(digest, 16) % 2 == 0 else "B"


def load_assignments() -> dict[str, str]:
    assignments: dict[str, str] = {}
    if not ASSIGNMENTS_CSV.exists():
        return assignments
    with ASSIGNMENTS_CSV.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            assignments[row["lead_id"]] = row["variant"]
    return assignments


def get_or_create_assignment(lead_id: str) -> str:
    assignments = load_assignments()
    if lead_id in assignments:
        return assignments[lead_id]

    variant = assign_variant(lead_id)
    with ASSIGNMENTS_CSV.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([lead_id, variant, now_iso()])
    return variant


def append_event(lead_id: str, event: str, meta: dict) -> None:
    if event not in VALID_EVENTS:
        raise ValueError(f"Evento inválido: {event}. Válidos: {sorted(VALID_EVENTS)}")

    variant = get_or_create_assignment(lead_id)
    with EVENTS_CSV.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([now_iso(), lead_id, variant, event, json.dumps(meta, ensure_ascii=False)])


def cmd_assign(args: argparse.Namespace) -> None:
    variant = get_or_create_assignment(args.lead)
    print(json.dumps({"lead_id": args.lead, "variant": variant}, ensure_ascii=False))


def cmd_event(args: argparse.Namespace) -> None:
    meta = {}
    if args.meta:
        meta = json.loads(args.meta)
    append_event(args.lead, args.event, meta)
    print(json.dumps({"ok": True, "lead_id": args.lead, "event": args.event}, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Funnel automation helper")
    sub = parser.add_subparsers(required=True)

    p_assign = sub.add_parser("assign", help="Atribui variante A/B ao lead")
    p_assign.add_argument("--lead", required=True)
    p_assign.set_defaults(func=cmd_assign)

    p_event = sub.add_parser("event", help="Registra evento de funil")
    p_event.add_argument("--lead", required=True)
    p_event.add_argument("--event", required=True, choices=sorted(VALID_EVENTS))
    p_event.add_argument("--meta", required=False, help="JSON com metadados")
    p_event.set_defaults(func=cmd_event)

    return parser


def main() -> None:
    ensure_files()
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
