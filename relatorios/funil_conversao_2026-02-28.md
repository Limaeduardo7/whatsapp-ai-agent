# Relatório de Funil de Conversão — 2026-02-28

- Amostra analisada: **6 leads** (base: `funnel_events.csv` + `lead_assignments.csv`).
- Conversão final (Lead → Fechamento): **100.0%**.

## Métricas por etapa
- lead_created: **1** leads
- first_message_sent: **3** leads
- qualified: **4** leads
- proposal_sent: **2** leads
- closed_won: **1** leads

## Conversões de etapa
- lead_created->first_message_sent: **300.0%** (drop-off -200.0%)
- first_message_sent->qualified: **133.3%** (drop-off -33.3%)
- qualified->proposal_sent: **50.0%** (drop-off 50.0%)
- proposal_sent->closed_won: **50.0%** (drop-off 50.0%)

## Principais gargalos
- qualified->proposal_sent: drop-off de **50.0%**
- proposal_sent->closed_won: drop-off de **50.0%**
- first_message_sent->qualified: drop-off de **-33.3%**

## Corte por variação A/B
- Variante A: leads=2, qualified=1, proposal_sent=1, closed_won=1, win_rate=50.0%
- Variante B: leads=4, qualified=3, proposal_sent=1, closed_won=0, win_rate=0.0%

## Recomendações (próximos 7 dias)
- Reforçar SLA de 1º resposta (<5 min) para elevar `lead_created -> first_message_sent`.
- Padronizar script de objeções na transição `proposal_sent -> closed_won` com follow-up em D+1 e D+3.
- Manter split A/B estável e registrar motivo de perda para segmentar melhorias por origem.
