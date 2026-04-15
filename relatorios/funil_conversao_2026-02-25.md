# Relatório de Funil de Conversão — 2026-02-25

## Fonte de dados
- Arquivos-base analisados:
  - `/root/clawd/relatorios/metricas_conversao.json`
  - `/root/clawd/relatorios/funil_conversao_2026-02-24.json`

## Resumo executivo
- O funil mantém gargalos nas etapas iniciais (**Lead → Resposta**) e finais (**Proposta → Fechamento**), conforme padrão da análise anterior.
- Nas métricas por origem, a melhor taxa reportada segue em **Email (6%)**, seguida de **Google (5%)** e **Social Media (4%)**.
- Recomendação operacional imediata: priorizar melhoria de tempo de primeira resposta e reforço de follow-up estruturado após envio de proposta.

## Leitura de performance (snapshot)
### Conversão por origem (último snapshot disponível)
- Google: **5%**
- Social Media: **4%**
- Email: **6%**

### Diagnóstico de gargalos
1. **Topo do funil (Lead → Resposta)**
   - Sinal: perda relevante de leads antes da primeira interação qualificada.
   - Hipótese: latência de atendimento e abertura pouco contextualizada.
2. **Fundo do funil (Proposta → Fechamento)**
   - Sinal: parte das propostas não evolui para decisão final.
   - Hipótese: ausência de cadência de follow-up e reforço de valor/ROI.

## Recomendações priorizadas (próximos 7 dias)
1. **SLA de primeira resposta**
   - Meta: reduzir mediana de tempo para primeira resposta para < 5 min em horário comercial.
2. **Cadência de follow-up pós-proposta**
   - D+1: reforço de valor e prova social.
   - D+3: pergunta de objeção principal.
   - D+5: CTA de fechamento com janela de decisão.
3. **Corte por script A/B (assim que eventos estiverem completos)**
   - Medir por etapa: resposta, qualificação, proposta e fechamento.
   - Critério inicial de vitória: uplift consistente em Proposta→Fechamento.

## Próximos passos analíticos
- Integrar ingestão automática dos arquivos de funil no dashboard principal.
- Publicar comparativo semanal com tendência por origem e por variação de script.
