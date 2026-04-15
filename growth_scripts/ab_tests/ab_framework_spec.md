# Framework A/B — Conversion Lab (WhatsApp → Fechamento)

## Objetivo
Padronizar testes A/B para aumentar taxa de resposta qualificada e taxa de fechamento no funil comercial via WhatsApp.

## Hipóteses atuais
- **A (direto-consultivo):** mensagem curta com qualificação imediata tende a aumentar resposta inicial.
- **B (valor-primeiro):** mensagem com prova/benefício antes da pergunta tende a aumentar avanço para proposta.

## Regras de Split
1. Unidade de randomização: `lead_id` (contato).
2. Regra determinística: `hash(lead_id) % 2`.
   - 0 = Variante A
   - 1 = Variante B
3. Persistência: lead mantém variante em todo o ciclo.
4. Exclusões:
   - Leads já em negociação ativa antes do experimento.
   - Leads sem 1º contato válido (spam/teste interno).

## Janela de Teste
- Duração mínima: 7 dias corridos.
- Ou até atingir 100 leads válidos por variante (o que ocorrer por último).

## Eventos obrigatórios
- `lead_created`
- `first_message_sent`
- `first_reply_received`
- `qualified`
- `proposal_sent`
- `objection_logged`
- `closed_won`
- `closed_lost`

## Métricas de decisão
1. **Resposta Inicial (%)** = `first_reply_received / first_message_sent`
2. **Qualificação (%)** = `qualified / first_reply_received`
3. **Proposta (%)** = `proposal_sent / qualified`
4. **Fechamento (%)** = `closed_won / proposal_sent`
5. **Tempo até resposta (mediana)**

## Critério de vitória semanal
- Prioridade 1: maior **Fechamento (%)**
- Prioridade 2: maior **Resposta Inicial (%)**
- Guardrail: sem aumento >15% em `closed_lost` por desqualificação tardia.

## Operação (Growth + Analyst)
- Growth: cria e aplica scripts por variante.
- Analyst: consolida métricas por etapa e publica leitura semanal.
- Jarvis: decide manutenção/troca da variante vencedora.

## Próximos experimentos
- Teste de CTA único vs CTA com opções.
- Teste de follow-up em D+1 vs D+2.
- Teste de prova social curta no 1º contato.
