# Weekly A/B Snapshot — 2026-02-27

## Objetivo
Gerar snapshot rápido do estado operacional do funil A/B para handoff ao Analyst/Jarvis.

## Execução deste turno (14:00)
- Novos leads de teste atribuídos: `cron-20260227-1400-a`, `cron-20260227-1400-b`
- Eventos registrados:
  - `qualified` para lead A
  - `first_message_sent` para lead B

## Leitura operacional
- Split A/B permanece determinístico por `lead_id`.
- Pipeline de evento está estável para ingestão incremental (CSV append-only).
- Dados prontos para sumarização por etapa + variante.

## Próximo experimento recomendado
1. Rodar piloto com 20-30 leads reais.
2. Coletar no mínimo eventos até `proposal_sent` para medir avanço de meio de funil.
3. Definir janela de decisão semanal com critério: +15% em `first_message_sent -> qualified` sem queda em `closed_won`.
