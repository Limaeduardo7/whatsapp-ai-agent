# Análise Operacional de Engajamento — 2026-03-01

## Contexto
Sem acesso direto a analytics nativo da plataforma neste turno; análise orientada por histórico recente de tarefas e desempenho operacional já observado nos ciclos anteriores.

## Leitura de performance (hipóteses de trabalho)
1. **Conteúdo com dor concreta + checklist** tende a elevar comentários qualificados.
2. **CTA direto para WhatsApp** aumenta velocidade de conversa, mas pode reduzir volume bruto vs CTA por comentário.
3. **Formato Reels** tende a ampliar alcance; **carrossel** tende a aumentar salvamento.
4. **Stories com enquete + caixa de pergunta** aumentam sinais de intenção para abordagem em DM.

## Riscos da semana
- Excesso de CTA de venda em sequência pode reduzir retenção de feed.
- Falta de padronização no registro de origem (comentário/DM/WhatsApp) dificulta decisão de vencedor A/B.
- Resposta tardia (>30 min) nos primeiros comentários reduz efeito de distribuição.

## Ações de mitigação
- Limitar CTA forte a 1 por peça e alternar com conteúdo educativo.
- Registrar origem de cada conversa com tag simples: `origem=comentario|dm|whatsapp`.
- SLA de resposta: primeiro bloco de interação em até 30 min pós-publicação.

## Plano de mensuração (D+1 e D+3)
Para cada post da semana 3:
- Alcance
- Curtidas
- Comentários
- Compartilhamentos
- Salvamentos
- DMs iniciadas
- Conversas WhatsApp iniciadas
- Conversas qualificadas (sim/não)

## Critério de decisão A/B
- Vencedor primário: maior nº de **conversas qualificadas** em D+3
- Desempate: maior razão `conversas qualificadas / alcance`

## Recomendação executiva
Priorizar conteúdo com utilidade imediata (checklist, erros comuns, mini-casos) e CTA de baixa fricção no início da jornada, migrando para WhatsApp após interação inicial para melhorar qualidade do lead.