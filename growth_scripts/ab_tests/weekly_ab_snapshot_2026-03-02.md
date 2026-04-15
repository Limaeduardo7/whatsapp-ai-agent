# Weekly A/B Snapshot — 2026-03-02

## Contexto do turno
- Slot: 14:00 (BRT)
- Origem: cron
- Objetivo: manter execução operacional do framework A/B enquanto integração total do gatilho real WhatsApp segue em andamento.

## Execução do turno
Leads processados no turno:
- `cron-20260302-1400-a`
- `cron-20260302-1400-b`

Eventos registrados:
- `first_message_sent`: 2
- `first_reply_received`: 1
- `qualified`: 1
- `proposal_sent`: 1

Observação:
- O lead `cron-20260302-1400-a` avançou até `proposal_sent`.
- O lead `cron-20260302-1400-b` ficou em `first_message_sent` (aguardando resposta), útil para monitorar latência de reply por variação.

## Leitura rápida
- O pipeline de split e telemetria segue funcional.
- Há evidência de progressão de estágio no mesmo turno para uma variação.
- Próxima alavanca é plugar ingestão real de lead WhatsApp sem intervenção manual por CLI.

## Próximas ações recomendadas
1. Ativar listener real no ponto de entrada de leads WhatsApp para chamar `assign` automaticamente.
2. Preservar o mesmo schema de `meta` para manter consistência histórica.
3. Rodar novo lote com volume maior (20-30 leads reais) para comparação A/B com significância mínima operacional.
