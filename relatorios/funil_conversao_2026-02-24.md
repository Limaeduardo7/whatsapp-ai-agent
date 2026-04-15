# Relatório de Funil de Conversão — 2026-02-24 16:00 BRT

## Base analisada
- Arquivo: `/root/clawd/agent_worklog/leads_metrics.csv`
- Amostra: 10 registros
- Campos: Lead, Response, Qualification, Proposal, Closure

## Totais consolidados
- Leads: **3.063**
- Responses: **316**
- Qualifications: **110**
- Proposals: **57**
- Closures: **14**

## Taxas do funil (sobre etapa anterior)
- Lead → Response: **10,32%**
- Response → Qualification: **34,81%**
- Qualification → Proposal: **51,82%**
- Proposal → Closure: **24,56%**

## Taxas acumuladas (sobre leads)
- Lead → Qualification: **3,59%**
- Lead → Proposal: **1,86%**
- Lead → Closure (conversão final): **0,46%**

## Gargalos prioritários
1. **Topo do funil (Lead → Response)**
   - Maior perda absoluta: 2.747 leads sem resposta (89,68%).
   - Hipótese: tempo de resposta e primeira abordagem ainda abaixo do ideal.
2. **Fechamento (Proposal → Closure)**
   - Conversão de propostas em fechamento: 24,56%.
   - Hipótese: propostas sem follow-up estruturado + objeções não tratadas em sequência.

## Recomendações práticas (semana)
1. **SLA de 5 minutos no primeiro contato** para novos leads WhatsApp.
2. **Cadência de follow-up de proposta (D+1, D+3, D+7)** com CTA único por mensagem.
3. **Tag obrigatória de motivo de perda** para negócios não fechados (preço, timing, confiança, escopo).
4. **Painel semanal A/B** comparando script A vs B em:
   - taxa de resposta;
   - taxa de qualificação;
   - taxa de fechamento.

## Nota
- O arquivo legado `/root/clawd/relatorios/metricas_conversao.json` segue com visão simplificada por origem (Google/Social/Email).
- Este relatório adiciona leitura operacional de funil ponta a ponta para tomada de decisão.
