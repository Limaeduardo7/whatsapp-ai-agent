# Weekly A/B Snapshot — 2026-03-05 (14:00 BRT)

## Execução do turno
- Fonte: cron diário Growth Hacker (14:00)
- Script operacional usado: `funnel_automation.py`
- Leads processados no turno: 2
  - `cron-20260305-1400-a`
  - `cron-20260305-1400-b`

## Eventos registrados
- `first_message_sent`: 2
- `first_reply_received`: 1
- `qualified`: 1
- `proposal_sent`: 0
- `closed_won`: 0
- `closed_lost`: 0

## Observações operacionais
- A execução manteve o padrão de telemetria por etapa com metadados (`source=cron`, `agent=growth`, `slot=14h`, `date=2026-03-05`).
- Ambas as leads do lote caíram na variante A pela regra determinística de hash.
- Ainda pendente conexão com gatilho real de entrada WhatsApp (execução segue via CLI/manual no cron).

## Próximos passos
1. Implementar bridge de ingestão para acionar `assign/event` automaticamente quando lead entrar no fluxo real.
2. Garantir distribuição balanceada A/B no lote de 20-30 leads reais.
3. Consolidar métricas por estágio para handoff ao Analyst/Jarvis.
