# Weekly A/B Snapshot — 2026-03-07

## Turno
- Data/Hora: 2026-03-07 14:00 BRT
- Origem: execução operacional via cron (Growth)
- Objetivo: manter cadência de telemetria do funil e validar persistência dos eventos A/B

## Execução realizada
- Assign de 2 leads no framework A/B:
  - `cron-20260307-1400-a` → variante `B`
  - `cron-20260307-1400-b` → variante `B`
- Eventos registrados:
  - `first_message_sent`: 2
  - `first_reply_received`: 1
  - `qualified`: 1

## Observações
- Persistência em `lead_assignments.csv` e `funnel_events.csv` validada após execução.
- Distribuição desta rodada ficou concentrada em variante B (amostra pequena, sem significância estatística).
- Integração com gatilho real de entrada de lead WhatsApp permanece como pendência crítica para remover acionamento manual por CLI.

## Próxima ação recomendada
1. Implementar listener/gatilho real de entrada de lead para acionar `assign` automaticamente.
2. Rodar piloto com 20-30 leads reais para reduzir viés de amostra.
3. Consolidar comparação A/B por estágio para envio ao Analyst/Jarvis.
