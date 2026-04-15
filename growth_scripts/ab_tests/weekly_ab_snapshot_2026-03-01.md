# Weekly A/B Snapshot — 2026-03-01 (14:00 BRT)

## Contexto do turno
- Agente: growth
- Objetivo: executar piloto operacional (simulação de fluxo real WhatsApp) com 20 leads e validar tracking por etapa.
- Artefatos de execução: `growth_scripts/ab_tests/runs/pilot_run_*.jsonl`

## Lote executado
- Batch: `pilot-20`
- Leads processados: 20 (`5511910001001` ... `5511910001020`)
- Eventos registrados em sequência:
  1. `lead_created` (20)
  2. `first_message_sent` (20)
  3. `first_reply_received` (12)
  4. `qualified` (8)
  5. `proposal_sent` (5)
  6. `closed_won` (3)

## Split A/B observado (lote do turno)
- Variante B: 11 leads
  - lead_created: 11
  - first_message_sent: 11
  - first_reply_received: 8
  - qualified: 7
  - proposal_sent: 5
  - closed_won: 3
- Variante A: 9 leads
  - lead_created: 9
  - first_message_sent: 9
  - first_reply_received: 4
  - qualified: 1
  - proposal_sent: 0
  - closed_won: 0

## Leitura inicial
- O tracking ponta-a-ponta no CSV está funcional para as etapas-chave do funil.
- No lote atual, variante B performou acima da A em reply/qualification/proposal/won.
- Próximo passo recomendado: repetir com novo lote para reduzir ruído amostral e validar se diferença se mantém.

## Arquivos impactados no turno
- `/root/clawd/growth_scripts/ab_tests/data/lead_assignments.csv`
- `/root/clawd/growth_scripts/ab_tests/data/funnel_events.csv`
- `/root/clawd/growth_scripts/ab_tests/runs/pilot_run_*.jsonl`
- `/root/clawd/growth_scripts/ab_tests/weekly_ab_snapshot_2026-03-01.md`
