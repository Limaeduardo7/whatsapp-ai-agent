---
name: whatsapp-agent-dev
description: Desenvolver, implantar e operar agente de IA para WhatsApp Comercial usando Evolution API + FastAPI Bridge + Kimi K2.5. Inclui arquitetura completa, deploy, troubleshooting e operações diárias.
---

# WhatsApp Agent Development

Desenvolvimento e operação do agente comercial de WhatsApp.

## When to Use

Use esta skill quando:
- Precisar criar/modificar o agente de WhatsApp
- Fazer deploy do bridge Python
- Diagnosticar problemas de conexão/resposta
- Configurar webhooks da Evolution API
- Alterar o modelo LLM ou system prompt
- Realizar manutenção do serviço

## Arquitetura

```
Lead(WA) → Evolution API → Bridge FastAPI → Kimi K2.5 → Resposta
                ↓               ↓
            PostgreSQL      SQLite/JSON
            Redis           Notion
```

**Componentes:**
| Componente | Tecnologia | Porta/URL |
|------------|------------|-----------|
| Evolution API | Docker (Baileys) | 8080 (interna), HTTPS externo |
| Bridge Python | FastAPI/Uvicorn | 8001 |
| LLM | Kimi K2.5 (NVIDIA) | via OpenAI-compatible |
| Memória | SQLite + JSON | /root/clawd/scripts/ |

## Quick Start

### 1. Verificar Status

```bash
# Status do bridge
systemctl status evolution-bridge.service

# Logs em tempo real
journalctl -u evolution-bridge.service -f

# Status Evolution
 docker service ps automacoes_evolution-api
```

### 2. Restart do Sistema

```bash
# Reiniciar bridge
sudo systemctl restart evolution-bridge.service

# Reiniciar Evolution (se necessário)
docker service update --force automacoes_evolution-api
```

## Configuração

### Bridge Python

**Arquivo:** `/root/clawd/scripts/evo_auto_reply.py`

```python
# Modelo (Kimi K2.5)
MODEL_ID = "nvidia-kimi/moonshotai/kimi-k2"
THINKING_LEVEL = "high"

# Evolution API
EVOLUTION_BASE_URL = "https://automacoes-evolution-api.hpfunv.easypanel.host"
EVOLUTION_INSTANCE = "Eu"
EVOLUTION_API_KEY = "..."

# Webhook
WEBHOOK_URL = "http://31.97.165.161:8001/evolution/webhook"
```

### Ficheiros de Persistência

| Arquivo | Função |
|---------|--------|
| `/root/clawd/scripts/chat_memory.json` | Memória de conversas |
| `/root/clawd/scripts/ignored_numbers.json` | Blacklist |
| `/root/clawd/scripts/mission_control.db` | SQLite (tarefas) |
| `/root/clawd/clients/*.md` | Contexto por cliente |

### Systemd Service

**Unit:** `/etc/systemd/system/evolution-bridge.service`

```ini
[Unit]
Description=Evolution API to OpenClaw Bridge
After=network.target

[Service]
User=root
WorkingDirectory=/root/clawd
ExecStart=/usr/bin/python3 -m uvicorn scripts.evo_auto_reply:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## Deploy

### Instalar Bridge

```bash
# Criar service
sudo tee /etc/systemd/system/evolution-bridge.service > /dev/null << 'EOF'
[Unit]
Description=Evolution API to OpenClaw Bridge
After=network.target

[Service]
User=root
WorkingDirectory=/root/clawd
ExecStart=/usr/bin/python3 -m uvicorn scripts.evo_auto_reply:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Ativar e iniciar
sudo systemctl daemon-reload
sudo systemctl enable evolution-bridge.service
sudo systemctl start evolution-bridge.service
```

### Configurar Webhook

```bash
curl -X POST "$EVOLUTION_BASE_URL/webhook/set" \
  -H "Content-Type: application/json" \
  -H "apikey: $EVOLUTION_API_KEY" \
  -d '{
    "webhook": {
      "url": "http://31.97.165.161:8001/evolution/webhook",
      "events": ["MESSAGES_UPSERT"]
    }
  }'
```

## Troubleshooting

### Problema: Redis disconnected

**Sintoma:** Logs da Evolution mostram "redis disconnected" em loop

**Solução:**
```bash
docker service update --force automacoes_evolution-api-redis
sleep 5
docker service update --force automacoes_evolution-api
```

### Problema: Bot não responde

**Diagnóstico:**
```bash
# 1. Bridge está rodando?
systemctl is-active evolution-bridge.service

# 2. Webhooks chegando?
tail -f /root/clawd/scripts/kimi_logs.jsonl | grep webhook

# 3. Conflito de sessão?
docker logs $(docker ps -f "name=evolution-api" -q) | grep "conflict\|428"
```

**Se conflito:**
```bash
docker rm -f $(docker ps -f "name=evolution" -f "status=exited" -q)
docker service update --force automacoes_evolution-api
```

### Problema: Envio falha (500)

**Verificar formato do número:**
```bash
curl -X POST "$EVOLUTION_BASE_URL/message/sendText/Eu" \
  -H "Content-Type: application/json" \
  -H "apikey: $EVOLUTION_API_KEY" \
  -d '{"number": "5554999999999", "text": "Teste"}'
```

### Diagnóstico Completo

```bash
# Status instância WhatsApp
docker exec $(docker ps -f "name=evolution-api" -q) \
  wget -qO- http://localhost:8080/instance/fetchInstances \
  --header="apikey: $EVOLUTION_API_KEY" | jq '.[] | {name, connectionStatus}'

# Verificar Redis IP
REDIS_ID=$(docker ps -f "name=evolution-api-redis" --format "{{.ID}}" | head -1)
docker inspect $REDIS_ID -f '{{.NetworkSettings.Networks}}'

# Logs bridge
journalctl -u evolution-bridge.service --since "1 hour ago"
```

## Fluxo de Mensagens

### Webhook Event (messages.upsert)

```json
{
  "event": "messages.upsert",
  "instance": "Eu",
  "data": {
    "key": {
      "remoteJid": "5554999999999@s.whatsapp.net",
      "fromMe": false
    },
    "message": {
      "conversation": "Olá, quero um site"
    }
  }
}
```

### Processamento

1. **Normalização** — Event name → `messages.upsert` (case/underscore)
2. **Deduplicação** — Verifica `message_id` ou fingerprint
3. **Intenção** — Classifica (`preco`, `prazo`, `fechamento`, etc)
4. **Pausa** — Se `fromMe=true`, marca como paused
5. **LLM** — Gera resposta com Kimi K2.5
6. **Fragmenta** — Quebra em balões via `send_bubbles()`

## Referências

- **Config completa:** `/root/clawd/WHATSAPP_COMERCIAL_AGENT_CONFIG.md`
- **Memória:** `/root/clawd/MEMORY.md` (seção WhatsApp)
- **Infraestrutura:** `/root/clawd/INFRASTRUCTURE.md`
- **Script core:** `/root/clawd/scripts/evo_auto_reply.py`
