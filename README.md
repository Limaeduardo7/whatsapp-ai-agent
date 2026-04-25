# WhatsApp AI Agent

Agente de atendimento comercial para WhatsApp usando Evolution API, FastAPI, LLM OpenAI-compatible e automacao Hotmart.

## Funcionalidades

- Recebe webhooks da Evolution API.
- Responde leads com um LLM configuravel.
- Mantem memoria curta e resumo por contato em SQLite.
- Divide respostas em baloes curtos e simula digitacao.
- Registra opt-out quando o contato pede para parar.
- Deduplica mensagens recebidas para evitar resposta duplicada.
- Processa compras aprovadas da Hotmart e dispara sequencias de cross-sell.
- Expoe endpoints de saude e estatisticas operacionais protegidas.
- Expoe dashboard operacional de marketing com React, graficos, filtros e acoes manuais.

## Arquitetura

```text
WhatsApp -> Evolution API -> FastAPI webhook -> LLM -> Evolution API -> WhatsApp
                                  |
                                  +-> SQLite
                                  +-> Hotmart marketing scheduler
```

Componentes principais:

- `src/main.py`: app FastAPI, health checks e webhook Evolution.
- `src/marketing_automation.py`: webhook Hotmart e scheduler de marketing.
- `src/marketing_dashboard.py`: interface React do dashboard operacional.
- `src/config.py`: configuracao via variaveis de ambiente.
- `src/services.py`: clientes LLM e Evolution.
- `src/repositories.py`: persistencia SQLite.
- `src/domain.py`: helpers de dominio, como telefone e mascaramento.

## Quick Start

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env
python -m uvicorn src.main:app --reload --port 8001
```

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python -m uvicorn src.main:app --reload --port 8001
```

## Configuracao

Variaveis essenciais:

- `EVOLUTION_BASE_URL`
- `EVOLUTION_INSTANCE`
- `EVOLUTION_API_KEY`
- `LLM_API_URL`
- `LLM_API_KEY`
- `LLM_MODEL_ID`
- `ADMIN_API_KEY`
- `HOTMART_WEBHOOK_SECRET`
- `EVOLUTION_WEBHOOK_SECRET`
- `PRODUCT_PRICE_MAP` opcional, em JSON, para receita estimada no dashboard. Exemplo: `{"chave do poder":97,"regra da vida":197}`.

Rotas administrativas exigem `ADMIN_API_KEY` no header `x-admin-api-key` ou `Authorization: Bearer ...`.

Quando `EVOLUTION_WEBHOOK_SECRET` estiver configurado, os webhooks da Evolution devem enviar o header `x-evolution-webhook-secret`.

## Endpoints

- `GET /`: health check simples.
- `GET /healthz`: readiness com validacao basica de configuracao.
- `POST /evolution/webhook`: webhook Evolution.
- `POST /evolution/webhook/messages-upsert`: rota alternativa para eventos `messages-upsert`.
- `POST /marketing/hotmart/webhook`: webhook Hotmart.
- `GET /marketing/dashboard`: dashboard operacional de marketing, publico e somente leitura.
- `GET /marketing/dashboard/data`: dados consolidados do dashboard, publico e somente leitura.
- `POST /marketing/automation/run-once`: executa scheduler uma vez, protegido por admin key.
- `GET /marketing/automation/stats`: estatisticas, protegido por admin key.
- `POST /marketing/automation/customers/{phone}/pause`: pausa um contato, protegido por admin key.
- `POST /marketing/automation/customers/{phone}/reactivate`: reativa um contato, protegido por admin key.
- `POST /marketing/automation/customers/{phone}/restart`: reinicia a sequencia do contato, protegido por admin key.
- `POST /marketing/automation/customers/{phone}/force-next`: agenda envio imediato, protegido por admin key.
- `POST /marketing/automation/customers/{phone}/opt-out`: marca opt-out manual, protegido por admin key.

## Docker

```bash
docker compose up --build
```

## Testes

```bash
python -m pip install -e ".[dev]"
ruff check src tests
pytest
```

## Producao

Recomendacoes:

- Use usuario dedicado no systemd, nunca `root`.
- Configure `ADMIN_API_KEY`, `HOTMART_WEBHOOK_SECRET` e `EVOLUTION_WEBHOOK_SECRET`.
- Restrinja `CORS_ORIGINS`.
- Use Postgres quando o volume crescer ou quando houver multiplos workers.
- Execute o scheduler em processo separado se escalar horizontalmente.
- Monitore erros de Evolution API, LLM e Hotmart com logs estruturados.
