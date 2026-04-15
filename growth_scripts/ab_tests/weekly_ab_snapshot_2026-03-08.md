# Weekly A/B Snapshot — 2026-03-08

## Turno
- Slot: 14:00 BRT
- Agente: growth
- Execução: sanity run operacional no fluxo A/B (simulado) com persistência em CSV.

## Leads do turno
- `cron-20260308-1400-a` → variação A
- `cron-20260308-1400-b` → variação B

## Eventos registrados no turno
- first_message_sent: 2
- first_reply_received: 2
- qualified: 1 (variação B)

## Evidências
- Assignments: `/root/clawd/growth_scripts/ab_tests/data/lead_assignments.csv`
- Eventos: `/root/clawd/growth_scripts/ab_tests/data/funnel_events.csv`

## Leitura rápida
- O pipeline de registro segue íntegro (split + eventos por etapa).
- A variação B avançou 1 lead até `qualified` neste turno.

## Próximo passo crítico
- Substituir acionamento manual por gatilho de entrada real no WhatsApp para rodar piloto de 20-30 leads com telemetria completa.

## Timestamp
2026-03-08T14:00:00-03:00
