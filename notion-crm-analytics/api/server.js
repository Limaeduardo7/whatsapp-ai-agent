import fs from 'node:fs';
import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';

dotenv.config({ override: true });

const app = express();
app.use(cors());
app.use(express.json());

const PORT = Number(process.env.PORT || 8787);
const NOTION_VERSION = '2025-09-03';
const DATA_SOURCE_ID_ENV = process.env.NOTION_DATA_SOURCE_ID || '434a45a3-9fd8-4bdd-993c-6752c91d9941';
const DATA_SOURCE_NAME = process.env.NOTION_DATA_SOURCE_NAME || 'Pipeline de Vendas';
const CACHE_TTL_MS = Number(process.env.CACHE_TTL_MS || 120000);

function loadNotionKey() {
  if (process.env.NOTION_API_KEY) return process.env.NOTION_API_KEY.trim();
  const localPath = '/root/.config/notion/api_key';
  if (fs.existsSync(localPath)) return fs.readFileSync(localPath, 'utf8').trim();
  return '';
}

const NOTION_API_KEY = loadNotionKey();
if (!NOTION_API_KEY) console.warn('[warn] NOTION_API_KEY ausente.');

async function notionRequest(endpoint, { method = 'GET', body } = {}) {
  const res = await fetch(`https://api.notion.com/v1${endpoint}`, {
    method,
    headers: {
      Authorization: `Bearer ${NOTION_API_KEY}`,
      'Notion-Version': NOTION_VERSION,
      'Content-Type': 'application/json',
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Notion ${res.status} ${endpoint}: ${text.slice(0, 320)}`);
  }

  if (res.status === 204) return {};
  return res.json();
}

const dsResolution = {
  id: null,
  title: null,
  checkedAt: 0,
};

async function verifyDataSource(id) {
  try {
    const ds = await notionRequest(`/data_sources/${id}`);
    return { id: ds.id, title: (ds.title || []).map((t) => t.plain_text || '').join('').trim() };
  } catch {
    return null;
  }
}

async function discoverDataSource() {
  const now = Date.now();
  if (dsResolution.id && now - dsResolution.checkedAt < 5 * 60 * 1000) {
    return { id: dsResolution.id, title: dsResolution.title };
  }

  const candidates = [];
  if (DATA_SOURCE_ID_ENV) candidates.push(DATA_SOURCE_ID_ENV);

  for (const id of candidates) {
    const found = await verifyDataSource(id);
    if (found) {
      dsResolution.id = found.id;
      dsResolution.title = found.title;
      dsResolution.checkedAt = now;
      return found;
    }
  }

  // Search by name
  try {
    const result = await notionRequest('/search', {
      method: 'POST',
      body: {
        query: DATA_SOURCE_NAME,
        filter: { property: 'object', value: 'data_source' },
        page_size: 20,
      },
    });

    const exact = (result.results || []).find((x) => {
      const title = (x.title || []).map((t) => t.plain_text || '').join('').trim();
      return title.toLowerCase() === DATA_SOURCE_NAME.toLowerCase();
    });
    const first = exact || (result.results || [])[0];

    if (first?.id) {
      dsResolution.id = first.id;
      dsResolution.title = (first.title || []).map((t) => t.plain_text || '').join('').trim();
      dsResolution.checkedAt = now;
      return { id: first.id, title: dsResolution.title };
    }
  } catch {
    // ignore and try broad search next
  }

  // Broad data_source search fallback
  try {
    const result = await notionRequest('/search', {
      method: 'POST',
      body: { filter: { property: 'object', value: 'data_source' }, page_size: 100 },
    });

    const all = result.results || [];
    const match = all.find((x) => {
      const title = (x.title || []).map((t) => t.plain_text || '').join('').trim().toLowerCase();
      return title.includes('pipeline') || title.includes('vendas') || title.includes('crm');
    });

    if (match?.id) {
      dsResolution.id = match.id;
      dsResolution.title = (match.title || []).map((t) => t.plain_text || '').join('').trim();
      dsResolution.checkedAt = now;
      return { id: match.id, title: dsResolution.title };
    }
  } catch {
    // ignore
  }

  throw new Error(`Nenhuma data source acessível encontrada. Recompartilhe no Notion a tabela "${DATA_SOURCE_NAME}" com a integração.`);
}

function readTitle(prop) {
  if (!prop || prop.type !== 'title') return '';
  return (prop.title || []).map((t) => t.plain_text || '').join('').trim();
}
function readRichText(prop) {
  if (!prop || prop.type !== 'rich_text') return '';
  return (prop.rich_text || []).map((t) => t.plain_text || '').join('').trim();
}
function readSelect(prop) {
  if (!prop) return '';
  if (prop.type === 'select') return prop.select?.name || '';
  if (prop.type === 'status') return prop.status?.name || '';
  return '';
}
function readNumber(prop) {
  if (!prop) return 0;
  if (prop.type === 'number') return Number(prop.number || 0);
  if (prop.type === 'formula' && prop.formula?.type === 'number') return Number(prop.formula.number || 0);
  return 0;
}
function readDate(prop) {
  if (!prop || prop.type !== 'date') return '';
  return prop.date?.start || '';
}
function readMultiSelect(prop) {
  if (!prop || prop.type !== 'multi_select') return [];
  return (prop.multi_select || []).map((x) => x.name).filter(Boolean);
}

function dayDiff(dateIso) {
  if (!dateIso) return null;
  const d = new Date(dateIso);
  if (Number.isNaN(d.getTime())) return null;
  return Math.max(0, Math.floor((Date.now() - d.getTime()) / 86400000));
}

function normalizeLead(page) {
  const p = page.properties || {};
  const probability = readNumber(p['Probabilidade de Fechamento (%)']);
  const value = readNumber(p['Valor Estimado']);
  const weightedValue = readNumber(p['Valor Ponderado']) || (value * probability) / 100;

  return {
    id: page.id,
    notionUrl: page.url,
    deal: readTitle(p['Deal']) || 'Lead sem nome',
    contato: readRichText(p['Contato']) || readRichText(p['WhatsApp']) || readRichText(p['ID Origem']) || '-',
    channel: readSelect(p['Canal']) || '-',
    source: readSelect(p['Origem da Campanha']) || '-',
    stage: readSelect(p['Etapa do Funil']) || '-',
    status: readSelect(p['Status']) || '-',
    priority: readSelect(p['Prioridade']) || '-',
    temperature: readSelect(p['Temperatura']) || '-',
    result: readSelect(p['Resultado']) || 'Em aberto',
    nextAction: readRichText(p['Próxima Ação']) || '-',
    nextActionDate: readDate(p['Data Próxima Ação']) || '',
    lastContactDate: readDate(p['Último Contato']) || '',
    closeDate: readDate(p['Data de Fechamento Real']) || '',
    lossReason: readSelect(p['Motivo de Perda']) || '-',
    value,
    probability,
    weightedValue,
    overdueFollowUp: p['Follow-up Atrasado']?.type === 'checkbox' ? Boolean(p['Follow-up Atrasado'].checkbox) : false,
    noResponseDays: readNumber(p['Dias sem Resposta']),
    tags: readMultiSelect(p['Tags']),
    lastEditedTime: page.last_edited_time,
    createdTime: page.created_time,
  };
}

async function fetchAllLeads() {
  const ds = await discoverDataSource();
  const leads = [];
  let start_cursor;

  while (true) {
    const data = await notionRequest(`/data_sources/${ds.id}/query`, {
      method: 'POST',
      body: { page_size: 100, ...(start_cursor ? { start_cursor } : {}) },
    });

    for (const row of data.results || []) leads.push(normalizeLead(row));
    if (!data.has_more) break;
    start_cursor = data.next_cursor;
  }

  return { leads, dataSource: ds };
}

function buildDateRange(days = 30) {
  const result = [];
  const now = new Date();
  for (let i = days - 1; i >= 0; i -= 1) {
    const d = new Date(now);
    d.setDate(now.getDate() - i);
    const key = d.toISOString().slice(0, 10);
    result.push({ date: key, count: 0, value: 0, weighted: 0 });
  }
  return result;
}

function computeAnalytics(leads, days = 30) {
  const openLeads = leads.filter((l) => !['Ganho', 'Perdido'].includes(l.result));
  const wonLeads = leads.filter((l) => l.result === 'Ganho');
  const lostLeads = leads.filter((l) => l.result === 'Perdido');

  const pipelineValue = openLeads.reduce((acc, l) => acc + l.value, 0);
  const forecastValue = openLeads.reduce((acc, l) => acc + l.weightedValue, 0);
  const withValue = openLeads.filter((l) => l.value > 0);
  const avgTicket = withValue.length ? withValue.reduce((acc, l) => acc + l.value, 0) / withValue.length : 0;

  const stageOrder = ['Lead', 'Qualificação', 'Proposta', 'Negociação', 'Ganho', 'Perdido'];
  const priorityOrder = ['Urgente', 'Alta', 'Média', 'Baixa', '-'];

  const stageDistribution = stageOrder.map((stage) => ({ stage, count: leads.filter((l) => l.stage === stage).length }));

  const sourceMap = new Map();
  const tempMap = new Map();
  const priorityMap = new Map();
  const lossMap = new Map();
  for (const l of leads) {
    sourceMap.set(l.source, (sourceMap.get(l.source) || 0) + 1);
    tempMap.set(l.temperature, (tempMap.get(l.temperature) || 0) + 1);
    priorityMap.set(l.priority, (priorityMap.get(l.priority) || 0) + 1);
    if (l.result === 'Perdido') lossMap.set(l.lossReason, (lossMap.get(l.lossReason) || 0) + 1);
  }

  const sourceDistribution = [...sourceMap.entries()].map(([name, value]) => ({ name, value }));
  const temperatureDistribution = [...tempMap.entries()].map(([name, value]) => ({ name, value }));
  const priorityDistribution = priorityOrder.map((name) => ({ name, value: priorityMap.get(name) || 0 })).filter((x) => x.value > 0);
  const lossReasons = [...lossMap.entries()].map(([name, value]) => ({ name, value })).sort((a, b) => b.value - a.value);

  const conversionBase = wonLeads.length + lostLeads.length;
  const conversionRate = conversionBase ? (wonLeads.length / conversionBase) * 100 : 0;

  const hotOpportunities = openLeads
    .filter((l) => l.temperature === 'Quente' || ['Urgente', 'Alta'].includes(l.priority) || ['Proposta', 'Negociação'].includes(l.stage))
    .sort((a, b) => b.weightedValue - a.weightedValue)
    .slice(0, 12);

  const overdueFollowUps = openLeads
    .filter((l) => l.overdueFollowUp)
    .sort((a, b) => (b.noResponseDays || 0) - (a.noResponseDays || 0))
    .slice(0, 20);

  const activitySeries = buildDateRange(days);
  const byDate = new Map(activitySeries.map((x) => [x.date, x]));
  for (const l of leads) {
    const date = (l.lastContactDate || l.createdTime || '').slice(0, 10);
    if (!date || !byDate.has(date)) continue;
    const row = byDate.get(date);
    row.count += 1;
    row.value += l.value;
    row.weighted += l.weightedValue;
  }

  const bucketDefs = [
    { bucket: '0-1 dia', min: 0, max: 1 },
    { bucket: '2-3 dias', min: 2, max: 3 },
    { bucket: '4-7 dias', min: 4, max: 7 },
    { bucket: '8-14 dias', min: 8, max: 14 },
    { bucket: '15+ dias', min: 15, max: Infinity },
  ];
  const agingBuckets = bucketDefs.map((b) => ({ bucket: b.bucket, count: 0 }));

  for (const l of openLeads) {
    const daysNoResponse = Number.isFinite(l.noResponseDays) ? l.noResponseDays : dayDiff(l.lastContactDate) ?? 999;
    const idx = bucketDefs.findIndex((b) => daysNoResponse >= b.min && daysNoResponse <= b.max);
    if (idx >= 0) agingBuckets[idx].count += 1;
  }

  const stagePriorityMatrix = [];
  for (const stage of stageOrder) {
    for (const priority of priorityOrder) {
      stagePriorityMatrix.push({ stage, priority, count: leads.filter((l) => l.stage === stage && l.priority === priority).length });
    }
  }

  const scatter = openLeads
    .filter((l) => l.value > 0)
    .map((l) => ({
      name: l.deal,
      probability: l.probability,
      value: l.value,
      weighted: l.weightedValue,
      daysWithoutResponse: Number.isFinite(l.noResponseDays) ? l.noResponseDays : dayDiff(l.lastContactDate) ?? 0,
      priority: l.priority,
      stage: l.stage,
      notionUrl: l.notionUrl,
    }));

  return {
    generatedAt: new Date().toISOString(),
    totals: {
      leads: leads.length,
      openLeads: openLeads.length,
      wonLeads: wonLeads.length,
      lostLeads: lostLeads.length,
      conversionRate,
      pipelineValue,
      forecastValue,
      avgTicket,
      hotCount: hotOpportunities.length,
      overdueCount: overdueFollowUps.length,
    },
    stageDistribution,
    priorityDistribution,
    sourceDistribution,
    temperatureDistribution,
    lossReasons,
    activitySeries,
    agingBuckets,
    stagePriorityMatrix,
    scatter,
    hotOpportunities,
    overdueFollowUps,
    leads,
  };
}

let cache = { at: 0, data: null, days: 30 };

async function getAnalytics(days) {
  const now = Date.now();
  if (cache.data && cache.days === days && now - cache.at < CACHE_TTL_MS) {
    return { ...cache.data, cacheHit: true, cacheAgeMs: now - cache.at };
  }

  const { leads, dataSource } = await fetchAllLeads();
  const analytics = computeAnalytics(leads, days);
  analytics.dataSource = dataSource;
  cache = { at: now, data: analytics, days };
  return { ...analytics, cacheHit: false, cacheAgeMs: 0 };
}

app.get('/api/health', async (req, res) => {
  try {
    const ds = await discoverDataSource();
    res.json({
      ok: true,
      service: 'notion-crm-analytics-api',
      configuredDataSourceId: DATA_SOURCE_ID_ENV,
      resolvedDataSourceId: ds.id,
      resolvedDataSourceTitle: ds.title,
      hasNotionKey: Boolean(NOTION_API_KEY),
      cacheTtlMs: CACHE_TTL_MS,
    });
  } catch (error) {
    res.status(500).json({
      ok: false,
      error: error.message,
      configuredDataSourceId: DATA_SOURCE_ID_ENV,
      hasNotionKey: Boolean(NOTION_API_KEY),
    });
  }
});

app.get('/api/analytics', async (req, res) => {
  try {
    const days = Math.max(7, Math.min(180, Number(req.query.days || 30)));
    const data = await getAnalytics(days);
    res.json(data);
  } catch (error) {
    res.status(500).json({ ok: false, error: error.message });
  }
});

app.get('/api/leads', async (req, res) => {
  try {
    const data = await getAnalytics(30);
    const limit = Math.max(1, Math.min(500, Number(req.query.limit || 150)));
    const sorted = [...data.leads].sort((a, b) => (b.lastContactDate || '').localeCompare(a.lastContactDate || ''));
    res.json({ generatedAt: data.generatedAt, total: data.leads.length, leads: sorted.slice(0, limit) });
  } catch (error) {
    res.status(500).json({ ok: false, error: error.message });
  }
});

app.listen(PORT, () => {
  console.log(`[notion-crm-analytics-api] running on :${PORT}`);
});
