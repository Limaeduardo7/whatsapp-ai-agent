# Deploy Runbook (Clonagem para Novos Servidores)

Este runbook é o passo a passo operacional para subir o sistema completo em qualquer servidor novo.

## 1) Pré-requisitos

- Linux com `systemd`
- Python 3.11+
- Git
- Acesso à Evolution API
- Chaves de API (LLM, Hotmart se usar Hotmart)
- Portas abertas:
  - `8001` (Marketing Automation)
  - `8002` (AI Closer)

## 2) Clonar e preparar projeto

```bash
git clone https://github.com/Limaeduardo7/whatsapp-ai-agent.git
cd whatsapp-ai-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## 3) Configurar `.env`

Preencher no mínimo:

- `EVOLUTION_BASE_URL`
- `EVOLUTION_INSTANCE`
- `EVOLUTION_API_KEY`
- `LLM_API_URL`
- `LLM_API_KEY`
- `LLM_MODEL_ID`
- `ADMIN_API_KEY`
- `EVOLUTION_WEBHOOK_SECRET` (recomendado)
- `HOTMART_WEBHOOK_SECRET` (se usar Hotmart)

Também configurar:

- `MARKETING_AUTOMATION_ENABLED`
- `AI_AGENT_ENABLED`
- `SEQUENCES_FILE`
- `DB_PATH`

> Referência completa: `docs/ENV_REFERENCE.md`

## 4) Escolher modo de execução

### Opção A: serviços separados (recomendado)

- `syncronix-marketing.service` na porta `8001`
- `syncronix-closer.service` na porta `8002`

Instalação:

```bash
sudo cp config/syncronix-marketing.service /etc/systemd/system/
sudo cp config/syncronix-closer.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now syncronix-marketing.service
sudo systemctl enable --now syncronix-closer.service
```

Checagem:

```bash
systemctl is-active syncronix-marketing.service
systemctl is-active syncronix-closer.service
```

### Opção B: execução manual (desenvolvimento)

```bash
python -m uvicorn src.main:app --host 0.0.0.0 --port 8001
# em outro terminal
python -m uvicorn src.main:app --host 0.0.0.0 --port 8002
```

## 5) Configurar webhook da Evolution

### AI Closer

Apontar eventos de mensagem para:

- `http://SEU_IP:8002/evolution/webhook`

Configuração recomendada:

- `webhookByEvents: false`
- `events: ["MESSAGES_UPSERT"]`

### Marketing

Webhook da Hotmart (ou outra fonte) deve chamar:

- `http://SEU_IP:8001/marketing/hotmart/webhook`

Com header:

- `x-hotmart-hottok: <HOTMART_WEBHOOK_SECRET>`

## 6) Teste de saúde

```bash
curl -s http://127.0.0.1:8001/healthz
curl -s http://127.0.0.1:8002/healthz
```

Esperado: `status: ok`.

## 7) Teste operacional rápido

1. Enviar uma mensagem para o WhatsApp conectado.
2. Verificar logs do closer:

```bash
journalctl -u syncronix-closer.service -n 80 --no-pager
```

3. Testar dashboard:

- `http://SEU_IP:8001/marketing/dashboard`

4. Rodar ciclo manual de automação:

```bash
curl -X POST http://127.0.0.1:8001/marketing/automation/run-once \
  -H 'x-admin-api-key: SEU_ADMIN_API_KEY'
```

## 8) Fonte de dados (Hotmart ou qualquer outra)

A automação **não precisa ficar presa à Hotmart**.

Você pode trocar a origem de compras por:

- CRM do cliente
- ERP
- Plataforma própria
- Outra plataforma de pagamento

### Como integrar outra fonte

Basta enviar eventos de compra para o endpoint:

- `POST /marketing/hotmart/webhook`

Com payload mínimo equivalente:

- evento de compra aprovada
- telefone do comprador
- nome do produto
- id/transação

Exemplo de estrutura aceita:

```json
{
  "event": "purchase.approved",
  "data": {
    "purchase": {
      "transaction": "TX-123",
      "approved_date": "2026-04-25T00:00:00Z"
    },
    "product": {
      "name": "A Regra da Vida"
    },
    "buyer": {
      "phone": "5511999999999",
      "name": "Cliente"
    }
  }
}
```

> Se trocar a fonte, mantenha o contrato de campos e assinatura para segurança.

## 9) Backup e recuperação

Banco padrão: SQLite em `DB_PATH`.

Backup simples:

```bash
cp data/agent.db data/agent.db.bak-$(date +%F-%H%M)
```

Restaurar:

```bash
cp data/agent.db.bak-YYYY-MM-DD-HHMM data/agent.db
sudo systemctl restart syncronix-marketing.service syncronix-closer.service
```

## 10) Troubleshooting

### AI não responde no WhatsApp

- conferir webhook da Evolution apontando para `:8002`
- checar `EVOLUTION_API_KEY` e `EVOLUTION_INSTANCE`
- validar `LLM_API_KEY` e `LLM_MODEL_ID`

### Marketing não dispara

- checar `MARKETING_AUTOMATION_ENABLED=true`
- validar `HOTMART_WEBHOOK_SECRET`
- verificar se contato está opt-out
- verificar regra de 1 mensagem/dia

### Erro 400 no envio

- número inválido / sem WhatsApp (`exists:false`)
- revisar normalização de telefone

## 11) Checklist de aceite (novo servidor)

- [ ] serviços ativos (`marketing` e `closer`)
- [ ] healthz 8001/8002 ok
- [ ] webhook Evolution ok
- [ ] mensagem teste recebida e respondida
- [ ] dashboard carregando
- [ ] automação run-once executando
- [ ] logs limpos sem erro crítico
