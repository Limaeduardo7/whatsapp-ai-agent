# HEARTBEAT.md

## Modo Anti-Spam (pedido do Eduardo)

**Regra principal:** NÃO enviar mensagem de status a cada heartbeat.

Só enviar mensagem quando houver pelo menos um destes casos:
- decisão nova relevante;
- tarefa concluída desde o último heartbeat;
- erro novo detectado e/ou corrigido;
- risco que precisa atenção agora.

Se não houver novidade relevante, responder apenas: `HEARTBEAT_OK`.

---

## Checklist (cada heartbeat)

### 1) Revisão rápida
- [ ] Reler `AUTONOMY.md`
- [ ] Verificar `exec-approvals.json` (auto-approve ativo)
- [ ] Checar logs em `/tmp/openclaw/` por erro novo crítico

### 2) Proatividade sem spam
- [ ] Verificar se há pendência real para resolver agora
- [ ] Executar correção apenas se houver problema concreto

### 3) Comunicação
- [ ] Se houver novidade relevante: enviar resumo curto no Telegram
- [ ] Se não houver novidade: **não enviar status**, apenas `HEARTBEAT_OK`

### 4) Memória
- [ ] Registrar em `memory/YYYY-MM-DD.md` somente fatos novos relevantes
- [ ] Atualizar `MEMORY.md` apenas para decisões duráveis
