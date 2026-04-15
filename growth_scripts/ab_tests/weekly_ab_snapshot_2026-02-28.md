# Weekly A/B Snapshot — 2026-02-28

## Contexto do turno (14:00 BRT)
Execução de sanity run operacional do `funnel_automation.py` para manter o pipeline de eventos saudável enquanto a integração com gatilho real de entrada de lead no WhatsApp segue pendente.

## Leads processados no turno
- `cron-20260228-1400-a`
- `cron-20260228-1400-b`

## Resultado de split A/B
- Ambos os leads foram atribuídos à variante **B** neste lote de teste.

## Eventos registrados
- `qualified`: 2
- `proposal_sent`: 1
- `first_message_sent`: 1

Detalhe por lead:
- `cron-20260228-1400-a` → `qualified`, `proposal_sent`
- `cron-20260228-1400-b` → `qualified`, `first_message_sent`

## Observações operacionais
- CLI validada com parâmetros corretos: `assign --lead`, `event --lead --event --meta`.
- Metadados do turno persistidos em JSON (`source=cron`, `agent=growth`, `slot=14h`) para facilitar leitura posterior do Analyst.

## Próximo passo recomendado
Conectar o script ao ponto real de entrada do lead no fluxo WhatsApp para iniciar piloto com 20-30 leads reais e cobertura de eventos até `proposal_sent`/`closed_won`.
