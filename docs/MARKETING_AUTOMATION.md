# Automacao Hotmart para WhatsApp

## Fluxo

```text
Hotmart purchase approved
  -> POST /marketing/hotmart/webhook
  -> extrai telefone, produto e transacao
  -> registra compra no SQLite
  -> seleciona sequencia por produto
  -> scheduler envia proximos passos via Evolution API
```

## Endpoints

- `POST /marketing/hotmart/webhook`
- `POST /marketing/automation/run-once`
- `GET /marketing/automation/stats`

As rotas `/automation/*` exigem `ADMIN_API_KEY`.

## Sequencias

As sequencias ficam em `data/automation_sequences.json`.

Campos:

- `id`
- `trigger_products`
- `target_product`
- `steps[].text`
- `steps[].delay_hours_after`
- `repeat_last_every_hours`

## Regras operacionais

- Compra duplicada e deduplicada por `purchase_id + phone + product`.
- Cada contato recebe no maximo 1 mensagem de marketing por dia.
- Contatos com opt-out persistido em `chat_profiles.opted_out` nao recebem novas mensagens.
- Se uma sequencia terminar, o contato fica em `waiting_purchase` ou repete o ultimo passo quando `repeat_last_every_hours` estiver configurado.

## Principios de copy

- Comecar com contexto da compra anterior, sem parecer disparo frio.
- Dar uma dica pratica antes de vender.
- Fazer ponte logica entre o produto comprado e o proximo produto.
- Usar CTA direto, sem pressao artificial.
- Encerrar a sequencia com opt-out claro.
- Evitar repeticao infinita de lembrete para preservar reputacao do numero.

## Producao

- Configure `HOTMART_WEBHOOK_SECRET`.
- Configure `ADMIN_API_KEY`.
- Monitore falhas de envio para Evolution API.
- Para escalar horizontalmente, tire o scheduler do processo web e use fila/worker dedicado.
