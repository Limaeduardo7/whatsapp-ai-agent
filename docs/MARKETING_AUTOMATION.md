# Hotmart -> WhatsApp Marketing Automation (Syncronix)

## Objetivo
Quando uma compra for aprovada na Hotmart:
1. identificar comprador (telefone + produto),
2. iniciar sequência de cross-sell no WhatsApp,
3. parar a sequência quando houver nova compra,
4. iniciar nova sequência para o próximo produto.

## Arquitetura

```text
Hotmart Webhook (purchase approved)
  -> POST /marketing/hotmart/webhook
  -> normaliza telefone + produto
  -> grava purchase no SQLite
  -> seleciona sequência por produto gatilho
  -> atualiza estado do cliente

Scheduler interno (a cada N segundos)
  -> encontra clientes com next_send_at vencido
  -> envia mensagem via Evolution API
  -> avança step e agenda próxima mensagem
  -> ao final: waiting_purchase (ou repeat_last)
```

## Endpoints

- `POST /marketing/hotmart/webhook`
- `POST /marketing/automation/run-once`
- `GET /marketing/automation/stats`

## Persistência (SQLite)

- `marketing_customers`
- `marketing_purchases`
- `marketing_messages`

## Arquivo de Sequências

`data/automation_sequences.json`

Cada sequência contém:
- `id`
- `trigger_products` (produtos que disparam essa jornada)
- `target_product`
- `steps[]` com `text` e `delay_hours_after`
- `repeat_last_every_hours` (opcional)

## Configuração obrigatória (.env)

- `EVOLUTION_BASE_URL`
- `EVOLUTION_INSTANCE`
- `EVOLUTION_API_KEY`
- `HOTMART_WEBHOOK_SECRET`
- `SEQUENCES_FILE`

## Observações de produção

1. **Compliance LGPD / opt-out**: inclua comando de saída (ex: "SAIR").
2. **Frequência**: limite mensagens para evitar bloqueio por spam.
3. **Webhook validation**: mantenha `HOTMART_WEBHOOK_SECRET` ativo.
4. **Monitoramento**: alerte em falha de envio (>X tentativas).
5. **Idempotência**: `purchase_id + phone + product` já está deduplicado.
