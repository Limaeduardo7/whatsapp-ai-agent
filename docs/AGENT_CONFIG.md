# Configuracao Tecnica

Este documento descreve a arquitetura atual do projeto depois da separacao em camadas.

## Componentes

- FastAPI: recebe webhooks e expoe health checks.
- Evolution API: gateway de envio e recebimento WhatsApp.
- LLM OpenAI-compatible: gera as respostas comerciais.
- SQLite: persistencia local de memoria, idempotencia, opt-out e automacao.
- Scheduler interno: processa sequencias de marketing quando habilitado.

## Variaveis principais

- `EVOLUTION_BASE_URL`
- `EVOLUTION_INSTANCE`
- `EVOLUTION_API_KEY`
- `EVOLUTION_WEBHOOK_SECRET`
- `LLM_API_URL`
- `LLM_API_KEY`
- `LLM_MODEL_ID`
- `ADMIN_API_KEY`
- `HOTMART_WEBHOOK_SECRET`
- `DB_PATH`
- `CORS_ORIGINS`

## Seguranca

- Rotas administrativas exigem `ADMIN_API_KEY`.
- Webhook Hotmart valida `x-hotmart-hottok` quando `HOTMART_WEBHOOK_SECRET` esta configurado.
- Webhook Evolution valida `x-evolution-webhook-secret` quando `EVOLUTION_WEBHOOK_SECRET` esta configurado.
- Telefones sao mascarados nos logs principais.
- Opt-out fica persistido em SQLite.

## Escalabilidade

SQLite atende MVP e baixo volume. Para multiplos workers, alto volume ou SLA mais forte, migrar para Postgres e executar o scheduler em processo separado com lock distribuido ou fila.

## Testes

```bash
python -m pip install -e ".[dev]"
ruff check src tests
pytest
```
