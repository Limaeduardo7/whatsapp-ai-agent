import { useEffect, useMemo, useState } from 'react'
import ReactECharts from 'echarts-for-react'

const REFRESH_MS = 60_000

function formatMoney(value = 0) {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    maximumFractionDigits: 2,
  }).format(Number(value || 0))
}

function formatPct(value = 0) {
  return `${Number(value || 0).toFixed(1)}%`
}

function App() {
  const [days, setDays] = useState(30)
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = async () => {
    try {
      setLoading(true)
      const res = await fetch(`/api/analytics?days=${days}`)
      const json = await res.json()
      if (!res.ok) throw new Error(json?.error || 'Falha ao carregar API')
      setData(json)
      setError('')
    } catch (err) {
      setError(err.message || 'Erro inesperado')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [days])

  useEffect(() => {
    const id = setInterval(() => load(), REFRESH_MS)
    return () => clearInterval(id)
  }, [days])

  const charts = useMemo(() => {
    if (!data) return null

    const stageOrder = ['Lead', 'Qualificação', 'Proposta', 'Negociação', 'Ganho', 'Perdido']
    const priorityOrder = ['Urgente', 'Alta', 'Média', 'Baixa', '-']

    const lineOption = {
      tooltip: { trigger: 'axis' },
      legend: { textStyle: { color: '#cbd5e1' } },
      xAxis: { type: 'category', data: data.activitySeries.map((d) => d.date.slice(5)), axisLabel: { color: '#94a3b8' } },
      yAxis: [
        { type: 'value', name: 'Leads', axisLabel: { color: '#94a3b8' } },
        { type: 'value', name: 'Valor', axisLabel: { color: '#94a3b8' } },
      ],
      grid: { left: 36, right: 44, top: 36, bottom: 28 },
      series: [
        {
          name: 'Leads',
          type: 'line',
          smooth: true,
          areaStyle: { opacity: 0.25 },
          lineStyle: { width: 3 },
          data: data.activitySeries.map((d) => d.count),
          color: '#38bdf8',
        },
        {
          name: 'Valor Ponderado',
          type: 'line',
          yAxisIndex: 1,
          smooth: true,
          lineStyle: { width: 2, type: 'dashed' },
          data: data.activitySeries.map((d) => Number(d.weighted.toFixed(2))),
          color: '#a78bfa',
        },
      ],
    }

    const funnelOption = {
      tooltip: { trigger: 'item' },
      series: [
        {
          type: 'funnel',
          sort: 'none',
          top: 10,
          bottom: 10,
          left: '8%',
          width: '84%',
          label: { color: '#e2e8f0', formatter: '{b}: {c}' },
          itemStyle: { borderColor: '#0f172a', borderWidth: 1 },
          data: stageOrder
            .map((stage) => ({ stage, count: data.stageDistribution.find((x) => x.stage === stage)?.count || 0 }))
            .filter((x) => x.count > 0)
            .map((x) => ({ name: x.stage, value: x.count })),
        },
      ],
    }

    const sourceOption = {
      tooltip: { trigger: 'item' },
      legend: { bottom: 0, textStyle: { color: '#cbd5e1' } },
      series: [
        {
          type: 'pie',
          radius: ['48%', '75%'],
          avoidLabelOverlap: true,
          itemStyle: { borderColor: '#020617', borderWidth: 2 },
          label: { color: '#e2e8f0' },
          data: data.sourceDistribution,
        },
      ],
    }

    const matrix = data.stagePriorityMatrix || []
    const heatData = []
    for (let y = 0; y < stageOrder.length; y += 1) {
      for (let x = 0; x < priorityOrder.length; x += 1) {
        const item = matrix.find((m) => m.stage === stageOrder[y] && m.priority === priorityOrder[x])
        heatData.push([x, y, item?.count || 0])
      }
    }

    const heatmapOption = {
      tooltip: { position: 'top' },
      grid: { top: 28, height: '68%' },
      xAxis: { type: 'category', data: priorityOrder, splitArea: { show: true }, axisLabel: { color: '#94a3b8' } },
      yAxis: { type: 'category', data: stageOrder, splitArea: { show: true }, axisLabel: { color: '#94a3b8' } },
      visualMap: {
        min: 0,
        max: Math.max(1, ...heatData.map((i) => i[2])),
        calculable: true,
        orient: 'horizontal',
        left: 'center',
        bottom: 0,
        textStyle: { color: '#94a3b8' },
      },
      series: [
        {
          name: 'Volume',
          type: 'heatmap',
          data: heatData,
          label: { show: true, color: '#f8fafc' },
          emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(59,130,246,0.35)' } },
        },
      ],
    }

    const scatterOption = {
      tooltip: {
        formatter: (params) => {
          const [prob, value, size, weighted, name] = params.data
          return `<strong>${name}</strong><br/>Prob.: ${prob}%<br/>Valor: ${formatMoney(value)}<br/>Ponderado: ${formatMoney(weighted)}<br/>Dias sem resposta: ${size}`
        },
      },
      xAxis: { type: 'value', name: 'Probabilidade (%)', axisLabel: { color: '#94a3b8' } },
      yAxis: { type: 'value', name: 'Valor (R$)', axisLabel: { color: '#94a3b8' } },
      series: [
        {
          type: 'scatter',
          symbolSize: (val) => 8 + Math.min(22, Number(val[2] || 0)),
          itemStyle: { color: '#22d3ee', opacity: 0.75 },
          data: (data.scatter || []).slice(0, 200).map((s) => [s.probability, s.value, s.daysWithoutResponse, s.weighted, s.name]),
        },
      ],
      grid: { left: 52, right: 24, top: 24, bottom: 42 },
    }

    const agingOption = {
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: data.agingBuckets.map((x) => x.bucket), axisLabel: { color: '#94a3b8' } },
      yAxis: { type: 'value', axisLabel: { color: '#94a3b8' } },
      grid: { left: 34, right: 20, top: 24, bottom: 30 },
      series: [
        {
          type: 'bar',
          data: data.agingBuckets.map((x) => x.count),
          itemStyle: {
            color: '#f97316',
            borderRadius: [6, 6, 0, 0],
          },
        },
      ],
    }

    return { lineOption, funnelOption, sourceOption, heatmapOption, scatterOption, agingOption }
  }, [data])

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <h1>Notion CRM · Data Analytics Dashboard</h1>
          <p>React + Vite · API integrada ao Notion</p>
        </div>
        <div className="controls">
          <select value={days} onChange={(e) => setDays(Number(e.target.value))}>
            <option value={14}>14 dias</option>
            <option value={30}>30 dias</option>
            <option value={60}>60 dias</option>
            <option value={90}>90 dias</option>
          </select>
          <button onClick={load}>Atualizar</button>
        </div>
      </header>

      {error && <div className="error">{error}</div>}
      {loading && <div className="loading">Carregando dados do Notion…</div>}

      {!loading && data && (
        <>
          <section className="kpis">
            <article className="card"><span>Total de leads</span><strong>{data.totals.leads}</strong></article>
            <article className="card"><span>Em aberto</span><strong>{data.totals.openLeads}</strong></article>
            <article className="card"><span>Conversão</span><strong>{formatPct(data.totals.conversionRate)}</strong></article>
            <article className="card"><span>Pipeline</span><strong>{formatMoney(data.totals.pipelineValue)}</strong></article>
            <article className="card"><span>Forecast</span><strong>{formatMoney(data.totals.forecastValue)}</strong></article>
            <article className="card"><span>Ticket médio</span><strong>{formatMoney(data.totals.avgTicket)}</strong></article>
            <article className="card"><span>Quentes</span><strong>{data.totals.hotCount}</strong></article>
            <article className="card"><span>Follow-up atrasado</span><strong>{data.totals.overdueCount}</strong></article>
          </section>

          <section className="grid two">
            <div className="panel">
              <h3>Atividade + valor ponderado</h3>
              <ReactECharts option={charts.lineOption} style={{ height: 320 }} />
            </div>
            <div className="panel">
              <h3>Funil de conversão</h3>
              <ReactECharts option={charts.funnelOption} style={{ height: 320 }} />
            </div>
          </section>

          <section className="grid three">
            <div className="panel">
              <h3>Origem da campanha</h3>
              <ReactECharts option={charts.sourceOption} style={{ height: 320 }} />
            </div>
            <div className="panel">
              <h3>Matriz etapa × prioridade</h3>
              <ReactECharts option={charts.heatmapOption} style={{ height: 320 }} />
            </div>
            <div className="panel">
              <h3>Aging de follow-up</h3>
              <ReactECharts option={charts.agingOption} style={{ height: 320 }} />
            </div>
          </section>

          <section className="grid one">
            <div className="panel">
              <h3>Oportunidades (probabilidade × valor)</h3>
              <ReactECharts option={charts.scatterOption} style={{ height: 360 }} />
            </div>
          </section>

          <section className="grid two">
            <div className="panel table-wrap">
              <h3>Top oportunidades quentes</h3>
              <table>
                <thead>
                  <tr>
                    <th>Lead</th>
                    <th>Etapa</th>
                    <th>Prioridade</th>
                    <th>Ponderado</th>
                  </tr>
                </thead>
                <tbody>
                  {(data.hotOpportunities || []).slice(0, 12).map((lead) => (
                    <tr key={lead.id}>
                      <td><a href={lead.notionUrl} target="_blank" rel="noreferrer">{lead.deal}</a></td>
                      <td>{lead.stage}</td>
                      <td>{lead.priority}</td>
                      <td>{formatMoney(lead.weightedValue)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="panel table-wrap">
              <h3>Follow-ups atrasados</h3>
              <table>
                <thead>
                  <tr>
                    <th>Lead</th>
                    <th>Dias</th>
                    <th>Próxima ação</th>
                    <th>Prioridade</th>
                  </tr>
                </thead>
                <tbody>
                  {(data.overdueFollowUps || []).slice(0, 12).map((lead) => (
                    <tr key={lead.id}>
                      <td><a href={lead.notionUrl} target="_blank" rel="noreferrer">{lead.deal}</a></td>
                      <td>{lead.noResponseDays}</td>
                      <td>{lead.nextAction}</td>
                      <td>{lead.priority}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <footer className="footer">
            <span>Atualizado: {new Date(data.generatedAt).toLocaleString('pt-BR')}</span>
            <span>{data.cacheHit ? `cache ${Math.round(data.cacheAgeMs / 1000)}s` : 'live'}</span>
          </footer>
        </>
      )}
    </div>
  )
}

export default App
