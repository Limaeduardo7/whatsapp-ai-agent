# Notion CRM Analytics Dashboard (React + Vite + API)

Dashboard avançado de analytics para o CRM no Notion.

## Stack
- **Frontend:** React + Vite + ECharts
- **Backend/API:** Node.js + Express
- **Data Source:** Notion API (`Pipeline de Vendas`)

## Estrutura
- `api/` → API que consulta o Notion e calcula métricas
- `web/` → dashboard React com gráficos avançados

## Configuração

> **Importante:** a integração do Notion precisa ter acesso à tabela **Pipeline de Vendas**.  
> No Notion: abra a tabela → `...` → **Connect to** → selecione sua integração.

### 1) API
```bash
cd /root/clawd/notion-crm-analytics/api
cp .env.example .env
# opcional: editar NOTION_API_KEY e NOTION_DATA_SOURCE_ID
npm install
npm run dev
```

> Se `NOTION_API_KEY` estiver vazio, a API usa automaticamente `~/.config/notion/api_key`.

### 2) Frontend
```bash
cd /root/clawd/notion-crm-analytics/web
npm install
npm run dev
```

Abrir: `http://localhost:5174`

## Endpoints
- `GET /api/health`
- `GET /api/analytics?days=30`
- `GET /api/leads?limit=150`

## Analytics incluídos
- KPIs (pipeline, forecast, conversão, ticket médio)
- Série temporal (atividade e valor ponderado)
- Funil de conversão
- Distribuição por origem
- Matriz etapa × prioridade (heatmap)
- Aging de follow-up
- Scatter de oportunidades (probabilidade × valor)
- Tabelas: top quentes e follow-up atrasado
