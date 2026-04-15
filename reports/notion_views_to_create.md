# Notion CRM — Views para criar (manual, 2 minutos)

Base: `Pipeline de Vendas`

## 1) Kanban por Etapa
- Tipo: Board
- Group by: `Etapa do Funil`
- Sort: `Prioridade` (Urgente > Alta > Média > Baixa)

## 2) Follow-up Vencido
- Tipo: Table
- Filtro:
  - `Follow-up Atrasado` = true
  - `Resultado` = Em aberto
- Sort:
  - `Data Próxima Ação` asc
  - `Prioridade` desc

## 3) Quentes
- Tipo: Table
- Filtro:
  - `Temperatura` = Quente
  - `Resultado` = Em aberto
- Sort:
  - `Prioridade` desc
  - `Data Próxima Ação` asc

## 4) Ganhos
- Tipo: Table
- Filtro:
  - `Resultado` = Ganho
- Sort:
  - `Data de Entrega` desc

## 5) Perdidos
- Tipo: Table
- Filtro:
  - `Resultado` = Perdido
- Sort:
  - `Último Contato` desc

## 6) Sem Nome (higiene)
- Tipo: Table
- Filtro:
  - `Tags` contém `Sem nome`
- Sort:
  - `Último Contato` desc

## 7) Bloqueados
- Tipo: Table
- Filtro:
  - `Status` = Bloqueado
- Sort:
  - `Último Contato` desc
