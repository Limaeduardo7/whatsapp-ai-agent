# ENV Reference (Variáveis de Ambiente)

Referência detalhada das variáveis usadas pelo projeto.

## Formato

- **Obrigatória**: sim/não
- **Default**: valor padrão
- **Uso**: onde impacta

---

## Evolution / WhatsApp

### `EVOLUTION_BASE_URL`
- Obrigatória: **sim**
- Default: `https://your-evolution-api.com`
- Uso: base da API Evolution para envio e gestão de webhooks.

### `EVOLUTION_INSTANCE`
- Obrigatória: **sim**
- Default: `default`
- Uso: nome da instância WhatsApp.

### `EVOLUTION_API_KEY`
- Obrigatória: **sim**
- Default: vazio
- Uso: autenticação de chamadas para Evolution.

### `EVOLUTION_WEBHOOK_SECRET`
- Obrigatória: não (mas recomendado)
- Default: vazio
- Uso: valida header `x-evolution-webhook-secret` no webhook inbound.

---

## LLM / IA

### `LLM_API_URL`
- Obrigatória: **sim**
- Default: `http://localhost:18789/v1/chat/completions`
- Uso: endpoint compatível com chat completions.

### `LLM_API_KEY`
- Obrigatória: **sim**
- Default: vazio
- Uso: autenticação do modelo.

### `LLM_MODEL_ID`
- Obrigatória: **sim**
- Default: `nvidia-kimi/moonshotai/kimi-k2.5`
- Uso: modelo usado nas respostas do agente.

### `THINKING_LEVEL`
- Obrigatória: não
- Default: `high`
- Uso: controle adicional para backends que suportem esse parâmetro.

---

## Segurança / Admin

### `ADMIN_API_KEY`
- Obrigatória: **sim** (produção)
- Default: vazio
- Uso: protege rotas administrativas (`/marketing/automation/*`, ações por contato).

### `CORS_ORIGINS`
- Obrigatória: não
- Default: `*`
- Uso: controle de origens do dashboard/API.

---

## Marketing Automation

### `MARKETING_AUTOMATION_ENABLED`
- Obrigatória: não
- Default: `true`
- Uso: liga/desliga processamento de automação.

### `HOTMART_WEBHOOK_SECRET`
- Obrigatória: sim (se usar endpoint de compras com assinatura)
- Default: vazio
- Uso: valida `x-hotmart-hottok`.

### `SEQUENCES_FILE`
- Obrigatória: não
- Default: `./data/automation_sequences.json`
- Uso: arquivo de sequências de copy e delays.

### `SCHEDULER_INTERVAL_SECONDS`
- Obrigatória: não
- Default: `30`
- Uso: intervalo do scheduler para varrer envios pendentes.

### `PRODUCT_PRICE_MAP`
- Obrigatória: não
- Default: `{}`
- Uso: fallback para receita estimada por produto.

### `HOTMART_CLIENT_ID`
- Obrigatória: não
- Default: vazio
- Uso: OAuth Hotmart (fallback de telefone por transação).

### `HOTMART_CLIENT_SECRET`
- Obrigatória: não
- Default: vazio
- Uso: OAuth Hotmart.

### `HOTMART_BASIC_TOKEN`
- Obrigatória: não
- Default: vazio
- Uso: alternativa ao par client id/secret.

### `HOTMART_AUTH_URL`
- Obrigatória: não
- Default: `https://api-sec-vlc.hotmart.com/security/oauth/token`
- Uso: URL de autenticação.

### `HOTMART_API_BASE`
- Obrigatória: não
- Default: `https://developers.hotmart.com/payments/api/v1`
- Uso: base da API de pagamentos.

> Observação importante: mesmo com nomes "Hotmart", a fonte de dados pode ser substituída por CRM/ERP/plataforma própria, mantendo o contrato de payload no webhook de compra.

---

## AI Closer

### `AI_AGENT_ENABLED`
- Obrigatória: não
- Default: `true`
- Uso: liga/desliga agente de resposta conversacional.

### `CLOSER_ENABLED`
- Obrigatória: não
- Default: `true`
- Uso: feature flag adicional do fluxo de closer.

### `TYPING_ENABLED`
- Obrigatória: não
- Default: `true`
- Uso: simulação de digitação no WhatsApp.

### `MAX_HISTORY_MESSAGES`
- Obrigatória: não
- Default: `12`
- Uso: quantidade de mensagens no contexto curto.

---

## Persistência e Paths

### `DB_PATH`
- Obrigatória: não
- Default: `./data/agent.db`
- Uso: banco SQLite principal.

### `MEMORY_FILE`
- Obrigatória: não
- Default: `./data/chat_memory.json`
- Uso: memória de conversa (legado/auxiliar).

### `BLACKLIST_FILE`
- Obrigatória: não
- Default: `./data/ignored_numbers.json`
- Uso: contatos ignorados.

### `LOG_FILE`
- Obrigatória: não
- Default: `./logs/app.log`
- Uso: arquivo de log local.

### `AGENTS_DIR`, `WORKSPACE_DIR`, `CLIENTS_DIR`
- Obrigatória: não
- Default: caminhos locais
- Uso: integração com ambiente OpenClaw/local ops.

---

## Integrações opcionais

### `GEMINI_API_KEY`
- Obrigatória: não
- Uso: STT/visão complementar.

### `GEMINI_STT_MODEL`
- Obrigatória: não
- Default: `gemini-1.5-flash`

### `TELEGRAM_BOT_TOKEN`
- Obrigatória: não
- Uso: alertas/notificações.

### `TELEGRAM_CHAT_IDS`
- Obrigatória: não
- Uso: destinatários dos alertas.

### `OWNER_NUMBER`
- Obrigatória: não
- Uso: destino de alertas internos.

### `NOTION_API_KEY`, `NOTION_DATABASE_ID`
- Obrigatória: não
- Uso: integrações paralelas.

---

## Perfis de ambiente recomendados

## Desenvolvimento

- CORS aberto (`*`)
- logs verbosos
- execução manual uvicorn

## Produção

- `ADMIN_API_KEY` forte
- segredos de webhook ativos
- CORS restrito
- systemd com restart automático
- backup diário do `agent.db`

---

## Validação rápida de configuração

```bash
curl -s http://127.0.0.1:8001/healthz
curl -s http://127.0.0.1:8002/healthz
```

Se `status` não for `ok`, revisar `.env` e logs dos serviços.
