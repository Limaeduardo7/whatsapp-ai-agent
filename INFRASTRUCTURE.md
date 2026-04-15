# Infraestrutura - OpenClaw + Evolution API

Documentação operacional do ambiente de produção. Última atualização: 2026-02-10.

## Visão Geral

O sistema roda em um VPS Linux (6.8.0-94-generic, x64) com IP `31.97.165.161`, usando:
- **OpenClaw** (gateway de agentes IA multi-canal)
- **Evolution API** (gateway WhatsApp via Baileys)
- **Easypanel** (orquestrador Docker Swarm)
- **n8n** (automações/workflows)

---

## OpenClaw

### Configuração

- **Config principal:** `/root/.openclaw/openclaw.json`
- **Workspace:** `/root/clawd`
- **Gateway:** `ws://127.0.0.1:18789` (loopback, auth por token)
- **Serviço systemd:** `openclaw-gateway.service`
- **Versão:** 2026.2.9 (npm: `@anthropic-ai/openclaw` → na verdade `openclaw`)
- **Dashboard:** `http://127.0.0.1:18789/`
- **Node:** v22.22.0 via nvm (`/root/.nvm/versions/node/v22.22.0/bin/node`)

### Agentes (13 total)

| ID | Nome | Modelo | Função |
|----|------|--------|--------|
| crustaceo | Crustáceo | openai-codex/gpt-5.2-codex | Agente padrão (default) |
| main | Main | openai-codex/gpt-5.3-codex (default) | Agente principal do sistema |
| jarvis | Jarvis | openai-codex/gpt-5.3-codex | Assistente pessoal |
| estaleiro | Estaleiro | google-antigravity/claude-opus-4-5-thinking | Desenvolvimento/código |
| escrivao | Escrivão | google-antigravity/gemini-3-flash | Escrita/documentação |
| designer | Designer | google-antigravity/gemini-3-flash | Design |
| seo | SEO Expert | google-antigravity/gemini-3-flash | SEO |
| researcher | Researcher | google-antigravity/gemini-3-flash | Pesquisa |
| social | Social Media | google-antigravity/gemini-3-flash | Redes sociais |
| growth | Growth Hacker | google-antigravity/gemini-3-flash | Growth |
| analyst | Data Analyst | google-antigravity/gemini-3-flash | Análise de dados |
| inspetor | Inspetor | google-antigravity/gemini-3-flash | Inspeção/qualidade |
| whatsapp-comercial | WhatsApp Comercial | openai-codex/gpt-5.3-codex | Atendimento WhatsApp |

### Estrutura de diretórios dos agentes

```
/root/.openclaw/agents/<agent-id>/
├── agent/
│   ├── SOUL.md              # Persona/identidade do agente
│   ├── auth-profiles.json   # Credenciais de providers (OBRIGATÓRIO)
│   └── documento.md         # Docs extras (opcional)
└── sessions/
    ├── sessions.json        # Índice de sessões
    └── <uuid>.jsonl         # Transcript da sessão
```

### Auth Profiles

Cada agente precisa de um `auth-profiles.json` em seu diretório `agent/` com os providers configurados. Sem esse arquivo, o agente **não funciona**.

Providers disponíveis:
- `google:default` — Google (API key)
- `openai-codex:default` — OpenAI Codex (OAuth)
- `google-antigravity:bosoncorp7@gmail.com` — Google Antigravity (OAuth, proxy para Claude/Gemini)

Para copiar auth de um agente funcional para outro:
```bash
cp /root/.openclaw/agents/crustaceo/agent/auth-profiles.json /root/.openclaw/agents/<novo-agente>/agent/auth-profiles.json
chmod 600 /root/.openclaw/agents/<novo-agente>/agent/auth-profiles.json
```

### Canais

| Canal | Status | Config |
|-------|--------|--------|
| Telegram | Ativo | Bot @Rekflexbot, dmPolicy=pairing |
| WhatsApp | Depende do link | dmPolicy=open, via Evolution API |
| Discord | Desabilitado | groupPolicy=open (RISCO se habilitado) |

### Comandos úteis

```bash
# Status geral
openclaw status

# Health check rápido
openclaw gateway health

# Diagnóstico completo
openclaw doctor
openclaw doctor --fix          # aplica correções automáticas

# Listar sessões de um agente
openclaw sessions --store /root/.openclaw/agents/<agent>/sessions/sessions.json

# Compactar sessão de agente (quando contexto está cheio)
openclaw agent --agent <agent-id> --message "compact"

# Reiniciar gateway
openclaw gateway restart

# Logs em tempo real
openclaw logs --follow

# Auditoria de segurança
openclaw security audit
openclaw security audit --deep
```

### Manutenção de sessões

Quando um agente atinge 100% do contexto (ex: 400k/400k tokens), a sessão precisa ser compactada:

```bash
# Verificar uso de contexto
openclaw sessions --store /root/.openclaw/agents/<agent>/sessions/sessions.json

# Compactar (o agente resume o histórico automaticamente)
openclaw agent --agent <agent-id> --message "compact"
```

### Permissões de segurança

- `/root/.openclaw/credentials` deve ter modo `700` (não 755)
- Auth profiles (`auth-profiles.json`) devem ter modo `600`

---

## Evolution API (WhatsApp)

### Configuração

- **Versão:** v2.3.6
- **URL pública:** `https://automacoes-evolution-api.hpfunv.easypanel.host`
- **API Key:** `1F7A7491E835-4C96-B1F8-9AECFA71B6A9`
- **Instância:** "Eu" (Eduardo - Meraki Group, +55 54 99139-7178)
- **Integration:** WHATSAPP-BAILEYS
- **Webhook:** `http://31.97.165.161:8001/evolution/webhook`

### Docker Swarm Services

| Service | Imagem | Rede |
|---------|--------|------|
| `automacoes_evolution-api` | evoapicloud/evolution-api:v2.3.6 | easypanel, easypanel-automacoes |
| `automacoes_evolution-api-db` | postgres:17 | easypanel-automacoes |
| `automacoes_evolution-api-redis` | redis:7 (dnsrr) | easypanel, easypanel-automacoes |
| `automacoes_n8n` | n8nio/n8n:latest | easypanel-automacoes |

### Problema conhecido: Redis perde IP no Docker Swarm

O container Redis usa `Endpoint Mode: dnsrr` e pode perder o IP nas redes overlay do Docker. Quando isso acontece, a Evolution API entra em loop de `redis disconnected`.

**Sintomas:**
- Logs da Evolution API: `ERROR [Redis] redis disconnected` em loop
- Container Redis rodando (`docker ps`) mas com IP vazio nas redes

**Diagnóstico:**
```bash
# Verificar se Redis tem IP
REDIS_ID=$(docker ps -f "name=evolution-api-redis" --format "{{.ID}}" | head -1)
docker inspect $REDIS_ID -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}}: IP={{$v.IPAddress}} {{end}}'

# Se IP estiver vazio → problema confirmado
```

**Solução:**
```bash
# 1. Recriar container Redis com IPs corretos
docker service update --force automacoes_evolution-api-redis

# 2. Aguardar convergência, depois recriar Evolution API para reconectar
docker service update --force automacoes_evolution-api

# 3. Verificar reconexão (deve mostrar "redis ready" e "CONNECTED TO WHATSAPP")
EVOL_ID=$(docker ps -f "name=automacoes_evolution-api.1" --format "{{.ID}}" | head -1)
docker logs $EVOL_ID --tail 30 2>&1 | grep -i -E "redis|connected"
```

### Verificar estado da instância WhatsApp

```bash
EVOL_ID=$(docker ps -f "name=automacoes_evolution-api.1" --format "{{.ID}}" | head -1)
docker exec $EVOL_ID wget -qO- http://localhost:8080/instance/fetchInstances \
  --header="apikey: 1F7A7491E835-4C96-B1F8-9AECFA71B6A9"
```

Campos importantes na resposta:
- `connectionStatus: "open"` → conectado
- `disconnectionReasonCode: 401` → device_removed (precisa re-scanear QR)
- `connectionStatus: "connecting"` → tentando reconectar

### Redis Config

- **URI:** `redis://default:3639ed6536cf67b0b7fb@automacoes_evolution-api-redis:6379`
- **TTL:** 604800 (7 dias)
- **Prefix:** `evolution`
- **Dados persistidos em:** `/etc/easypanel/projects/automacoes/evolution-api-redis/data`

---

## Easypanel

Orquestrador Docker Swarm que gerencia os services. Os services ficam no stack `automacoes`.

```bash
# Listar services do stack
docker service ls | grep automacoes

# Ver logs de um service
docker service logs automacoes_evolution-api --tail 50 --raw

# Forçar restart de um service
docker service update --force automacoes_<service>
```

---

## Checklist de troubleshooting

1. **Agente OpenClaw não responde** → Verificar `auth-profiles.json` existe e tem os providers corretos
2. **Agente com contexto cheio** → `openclaw agent --agent <id> --message "compact"`
3. **Redis disconnected na Evolution API** → Verificar IP do container Redis, `docker service update --force`
4. **WhatsApp desconectado** → Verificar `connectionStatus` via API, re-scanear QR se `device_removed`
5. **Gateway OpenClaw não inicia** → `openclaw doctor --fix`, verificar Node 22+
6. **Telegram bot não responde em grupo** → Verificar `requireMention` e `/setprivacy Disable` no BotFather
