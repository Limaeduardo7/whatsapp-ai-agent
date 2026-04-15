# Relatório de Funil de Conversão — 2026-03-08

## Janela analisada
- Início: 2026-03-01T17:00:44.530582+00:00
- Fim: 2026-03-08T17:00:44.530582+00:00
- Leads únicos na janela: **8**

## KPIs do funil (7 dias)
- `first_message_sent`: **8**
- `first_reply_received`: **5**
- `qualified`: **4**
- `proposal_sent`: **1**
- `closed_won`: **0**

> Observação de qualidade de dados: não houve eventos `lead_created` na janela, indicando sub-registro da etapa de entrada no tracking atual.

## Conversões por etapa
1. first_message_sent → first_reply_received: **62,5%** (5/8)
2. first_reply_received → qualified: **80,0%** (4/5)
3. qualified → proposal_sent: **25,0%** (1/4)
4. proposal_sent → closed_won: **0,0%** (0/1)

## Leitura analítica
- **Gargalo principal atual:** `qualified → proposal_sent` (queda de 75%).
- **Gargalo de fechamento:** `proposal_sent → closed_won` sem conversão na janela.
- **Topo do funil operacional** com bom volume de mensagem enviada, porém com deficiência de instrumentação em `lead_created`.

## Corte A/B (janela)
- **Variante A**
  - first_message_sent: 4
  - first_reply_received: 3
  - qualified: 3
  - proposal_sent: 1
  - closed_won: 0
- **Variante B**
  - first_message_sent: 4
  - first_reply_received: 2
  - qualified: 1
  - proposal_sent: 0
  - closed_won: 0

Leitura: A variante **A** performou melhor no meio de funil (reply e qualificação), mas a amostra ainda é pequena para decisão definitiva.

## Recomendações operacionais (próximos 7 dias)
1. **Corrigir tracking de entrada**: registrar `lead_created` em 100% dos novos leads para cálculo real de conversão total.
2. **Aumentar taxa qualified→proposal**: criar SLA de proposta (ex.: até 2h após qualificação) e checklist mínimo de escopo.
3. **Fechamento**: aplicar follow-up estruturado D+1 e D+3 para todos os `proposal_sent` sem resposta.
4. **Experimento A/B**: manter split 50/50 por mais 20-30 leads e reavaliar com significância mínima operacional.
