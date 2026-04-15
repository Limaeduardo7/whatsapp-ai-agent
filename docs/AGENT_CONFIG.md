# WhatsApp Comercial — Configuração Completa e Arquitetura Técnica

> Documento técnico do agente comercial de WhatsApp via Evolution.
> Escopo: configuração atual, automações, fluxo técnico, correções aplicadas e operação.

## 1) Objetivo do bot

Atender leads de criação de sites no WhatsApp com foco em:
- resposta rápida,
- condução comercial objetiva,
- encaminhamento para humano quando necessário,
- registro de contexto para continuidade.

Regras de negócio ativas no comportamento:
- Não enrolar (objetivo/prático).
- Respostas humanizadas em mensagens fragmentadas (balões curtos).
- Oferecer sugestões práticas quando agregarem valor ao avanço da conversa.
- Oferecer demonstração sem custo após aceite de orçamento.
- Tratar projetos complexos com escalonamento humano.

---

## 2) Arquitetura técnica

## 2.1 Componentes

1. **Evolution API (WhatsApp gateway)**
   - Serviço Docker (EasyPanel/Swarm): `automacoes_evolution-api`
   - Imagem: `evoapicloud/evolution-api:v2.3.6`
   - Instância WhatsApp: `Eu`

2. **Bridge Python/FastAPI**
   - Arquivo principal: `/root/clawd/scripts/evo_auto_reply.py`
   - Processo: Uvicorn
   - Porta: `8001`
   - Webhook receptor: `/evolution/webhook`

3. **Systemd do bridge**
   - Unit: `/etc/systemd/system/evolution-bridge.service`
   - Start:
     - `ExecStart=/root/clawd/.venv/bin/python -m uvicorn scripts.evo_auto_reply:app --host 0.0.0.0 --port 8001`

4. **Modelo de IA de resposta**
   - Endpoint: NVIDIA OpenAI-compatible (`/v1/chat/completions`)
   - Modelo configurado no código: `meta/llama-3.1-70b-instruct`
   - **Thinking**: `very_high` (aplicado em todas as respostas, incluindo follow-up)

5. **STT/Vision auxiliar**
   - Gemini (`gemini-1.5-flash`) para:
     - transcrição de áudio
     - descrição de imagem

6. **TTS auxiliar**
   - gTTS para geração de áudio (quando necessário)

---

## 2.2 Fluxo de dados (alto nível)

1. Lead envia mensagem no WhatsApp.
2. Evolution dispara webhook para:
   - `http://31.97.165.161:8001/evolution/webhook`
3. Bridge recebe evento (`messages-upsert`), normaliza e valida.
4. Bridge processa contexto (memória + intenção + regras).
5. Bridge chama modelo para resposta comercial.
6. Resposta é enviada em balões fragmentados via Evolution.
7. Estado do lead, histórico e resumo ficam persistidos em arquivos/DB.

---

## 3) Configurações principais (estado atual)

## 3.1 Config de conectividade (bridge)

- Base Evolution: `https://automacoes-evolution-api.hpfunv.easypanel.host`
- Instância: `Eu`
- Owner number (alertas internos): `5554991879262`

> **Segurança:** chaves/tokens estão hoje no código. Recomenda-se mover para variáveis de ambiente e arquivo `.env`.

## 3.2 Persistência local

Arquivos usados:
- Memória de conversa: `/root/clawd/scripts/chat_memory.json`
- Lista ignorados/pausados: `/root/clawd/scripts/ignored_numbers.json`
- Log de interação IA: `/root/clawd/scripts/kimi_logs.jsonl`
- Fila de notificação: `/root/clawd/scripts/notify_queue.jsonl`
- Config de agentes/tarefas: `/root/clawd/scripts/agents_config.json`
- DB SQLite: `/root/clawd/scripts/notion.db`
- Contexto cliente por contato: `/root/clawd/clients/*.md`

---

## 4) Automações implementadas

## 4.1 Recepção de webhook e filtro

- Aceita apenas evento de mensagem:
  - `messages.upsert`
- Normalização de nome de evento aplicada:
  - `-`, `_`, case (maiúscula/minúscula) -> formato padronizado
- Deduplicação por:
  - `message_id`
  - fingerprint (jid + texto + timestamp)

## 4.2 Pausa por intervenção humana

Se detectar `fromMe=true` para conversa de lead:
- marca contato como `paused=true`
- interrompe auto-resposta
- notifica no Telegram que bot foi pausado
- retomada só com gatilho de texto (ex.: “retomar”, “continuar”)

## 4.3 Follow-up automático

Loop periódico:
- intervalo interno: 30 min
- follow-up em leads com `awaiting_response`
- disparo após ~5h sem resposta
- evita disparo tarde da noite
- follow-up enviado em balões (`send_bubbles`)

## 4.4 Detecção de intenção comercial

Intents principais:
- `preco`, `prazo`, `pagamento`, `site`, `loja`, `portfolio`, `fechamento`, `complexo`, `geral`

## 4.5 Escalonamentos automáticos

- **Lead quente** (`fechamento`) -> alerta ao owner
- **Projeto complexo** (`complexo`) -> alerta e pausa de automação
- **Pedido de humano** -> alerta ao owner

## 4.6 Regra de demonstração sem custo

Quando lead aceita orçamento:
- bot responde explicitamente oferecendo demonstração sem custo
- depois segue coleta objetiva para fechamento

## 4.7 Mensagens fragmentadas/humanização

Função `send_bubbles`:
- quebra por parágrafos/frases
- limita tamanho por balão
- simula digitação (`sendPresence`) com pausas
- envia múltiplos balões curtos para parecer conversa humana

## 4.8 Regra central de linguagem

Prompt comercial reforçado com:
- objetividade extrema
- praticidade
- não enrolar
- sugestões práticas e concretas quando fizer sentido
- sem markdown/negrito

## 4.9 Suporte multimídia

- Áudio recebido -> transcrição Gemini
- Imagem recebida -> descrição Gemini
- Texto final segue para o motor comercial

## 4.10 PDF de orçamento

- Gera PDF com FPDF
- inclui escopo/prazo/valor/condições
- envio como documento via Evolution

## 4.11 Kanban/Feed e tarefas

- Cria tarefa quando novo lead inicia
- Atualiza status no `agents_config.json` + SQLite
- Integra com feed de inteligência interno

---

## 5) Endpoints expostos pelo bridge

Principais rotas:
- `GET /` (health)
- `POST /evolution/webhook`
- `POST /evolution/webhook/{event_path}`
- `POST /notify-task`
- `POST /api/whatsapp/send-text`
- `POST /api/whatsapp/send-audio`
- `POST /api/whatsapp/send-document`
- `GET /api/tts`
- rotas de dashboard (`/api/agents`, `/api/tasks`, `/api/feed`, `/api/context`)

---

## 6) Hardening/correções aplicadas recentemente

### 6.1 Normalização robusta de eventos
- Correção para aceitar variações de evento (`messages-upsert`, `messages_upsert`, etc).

### 6.2 Envio para JID/numero
- Normalização de destino para número limpo (remove `@...`)
- Fallback para alvo original quando houver 400
- Coberto em:
  - `sendText`
  - `sendAudio`
  - `sendDocument`
  - `sendPresence`

### 6.3 Retry em falha 5xx
- `sendText` com retry automático em erro de servidor (5xx).

### 6.4 Limpeza de containers stale
- Remoção de containers duplicados/stale de Evolution/Redis para reduzir conflito de sessão.

---

## 7) Incidentes observados (raiz do “não responde”)

Padrões detectados nos logs:
- `messages-upsert` chegando (entrada OK)
- falha intermitente na saída (`sendText 500`)
- conflitos de sessão/stream:
  - `conflict: replaced`
  - `Connection Closed (428)`
- reconexões frequentes (`connection-update` em alta frequência)

Interpretação:
- O bot "parado" nem sempre era falta de entrada.
- Em vários momentos era instabilidade do canal de saída no Evolution/Baileys.

---

## 8) Operação diária (comandos úteis)

```bash
# status do bridge
systemctl status evolution-bridge.service

# restart do bridge
systemctl restart evolution-bridge.service

# logs do bridge
journalctl -u evolution-bridge.service -f

# tarefas do serviço Evolution (Swarm)
docker service ps automacoes_evolution-api --no-trunc

docker service ps automacoes_evolution-api-redis --no-trunc
```

---

## 9) Regras operacionais obrigatórias

- Canal WhatsApp oficial desta automação: **Evolution**.
- Não depender do canal WhatsApp nativo do OpenClaw.
- Em demandas de dev web vindas de WhatsApp, roteamento deve seguir protocolo com Jarvis/agentes.

---

## 10) Melhorias recomendadas (próximas)

1. Mover segredos para ambiente (`.env`) e retirar hardcode do script.
2. Circuit breaker para reduzir tempestade de retry em reconexões.
3. Métrica de entrega por contato (taxa de 200/201 vs 400/500).
4. Fila de envio (com backoff exponencial) para momentos de instabilidade do Evolution.
5. Healthcheck ativo com alerta quando houver sequência de `sendText 500`.

---

## 11) Arquivos de referência

- Core do bot: `/root/clawd/scripts/evo_auto_reply.py`
- Service unit: `/etc/systemd/system/evolution-bridge.service`
- Memória de decisões: `/root/clawd/MEMORY.md`
- Log diário de ações: `/root/clawd/memory/2026-02-11.md`

---

**Status no momento desta documentação:** bot operacional, com hardening aplicado para instabilidade intermitente de envio e humanização ativa em mensagens fragmentadas.