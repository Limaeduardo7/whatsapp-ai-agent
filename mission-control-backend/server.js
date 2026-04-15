import express from 'express'
import cors from 'cors'
import fs from 'fs'
import path from 'path'
import { execSync } from 'child_process'

const app = express()
const PORT = process.env.PORT || 8001
const DATA_PATH = process.env.DATA_PATH || path.join(process.cwd(), 'data.json')
const OPENCLAW_CONFIG = process.env.OPENCLAW_CONFIG || '/root/.openclaw/openclaw.json'

app.use(cors())
app.use(express.json({ limit: '1mb' }))

const defaultData = {
  agents: [
    { id: 'whatsapp', name: 'WhatsApp Comercial', role: 'VENDAS/ATENDIMENTO', icon: 'MessageSquare', color: 'emerald-400', shift: '08:00', model: 'moonshotai/kimi-k2.5', enabled: true },
    { id: 'jarvis', name: 'Jarvis', role: 'COORDENAÇÃO', icon: 'Cpu', color: 'neon-purple', shift: '07:00', model: 'moonshotai/kimi-k2.5', enabled: true },
    { id: 'researcher', name: 'Researcher', role: 'PESQUISADOR', icon: 'Search', color: 'neon-blue', shift: '07:30', model: 'moonshotai/kimi-k2.5', enabled: true },
    { id: 'estaleiro', name: 'Estaleiro', role: 'FRONTEND', icon: 'Layout', color: 'neon-purple', shift: '09:00', model: 'google-antigravity/claude-opus-4-5-thinking', enabled: true },
    { id: 'escrivao', name: 'Escrivão', role: 'COPYWRITER', icon: 'PenTool', color: 'neon-blue', shift: '10:00', model: 'google-antigravity/gemini-3-flash', enabled: true },
    { id: 'seo', name: 'SEO Expert', role: 'OTIMIZAÇÃO', icon: 'BarChart3', color: 'neon-purple', shift: '11:00', model: 'google-antigravity/gemini-3-flash', enabled: true },
    { id: 'social', name: 'Social Media', role: 'ENGAJAMENTO', icon: 'Users', color: 'neon-blue', shift: '12:00', model: 'google-antigravity/gemini-3-flash', enabled: true }
  ],
  tasks: []
}

const CRON_TZ = 'UTC'
const CRON_PREFIX = 'mission-control:agent:'

function listCronJobs() {
  const cli = process.env.OPENCLAW_CLI || '/root/.nvm/versions/node/v22.22.0/bin/openclaw'
  try {
    const raw = execSync(`${cli} cron list --json`, { encoding: 'utf-8' })
    const json = raw.slice(raw.indexOf('{'))
    const data = JSON.parse(json)
    return data.jobs || []
  } catch (err) {
    console.error('Cron list failed:', err?.message || err)
    return []
  }
}

function upsertAgentCron(agent, jobs) {
  if (!agent?.id || !agent?.shift) return
  const [hh, mm] = agent.shift.split(':')
  if (hh === undefined || mm === undefined) return
  const expr = `${mm} ${hh} * * *`
  const name = `${CRON_PREFIX}${agent.id}`
  const existing = jobs.find(job => job.name === name)
  const systemEvent = `Mission Control: iniciar turno do agente ${agent.name} (${agent.id}).`

  const cli = process.env.OPENCLAW_CLI || '/root/.nvm/versions/node/v22.22.0/bin/openclaw'
  const baseArgs = `--cron "${expr}" --tz ${CRON_TZ} --session main --system-event "${systemEvent}" --wake now --name "${name}"`

  try {
    if (agent.enabled) {
      if (existing?.id) {
        execSync(`${cli} cron edit ${existing.id} ${baseArgs} --enable`, { stdio: 'ignore' })
      } else {
        execSync(`${cli} cron add ${baseArgs}`, { stdio: 'ignore' })
      }
    } else if (existing?.id) {
      execSync(`${cli} cron edit ${existing.id} --disable`, { stdio: 'ignore' })
    }
  } catch (err) {
    console.error('Cron upsert failed:', err?.message || err)
  }
}

function syncCrons(agents = []) {
  const jobs = listCronJobs()
  agents.forEach(agent => upsertAgentCron(agent, jobs))
}

function readData() {
  if (!fs.existsSync(DATA_PATH)) {
    fs.writeFileSync(DATA_PATH, JSON.stringify(defaultData, null, 2))
  }
  const raw = fs.readFileSync(DATA_PATH, 'utf-8')
  return JSON.parse(raw)
}

function writeData(data) {
  fs.writeFileSync(DATA_PATH, JSON.stringify(data, null, 2))
}

function readAvailableModels() {
  try {
    if (!fs.existsSync(OPENCLAW_CONFIG)) return []
    const raw = fs.readFileSync(OPENCLAW_CONFIG, 'utf-8')
    const json = JSON.parse(raw)
    const defaults = json?.agents?.defaults || {}
    const modelsMap = defaults?.models || {}
    const primary = defaults?.model?.primary
    const models = new Set([...
      Object.keys(modelsMap),
      ...(primary ? [primary] : [])
    ])
    return [...models].sort()
  } catch (err) {
    console.error('Read models failed:', err?.message || err)
    return []
  }
}

app.get('/api/agents', (req, res) => {
  const data = readData()
  const models = readAvailableModels()
  res.json({ ...data, models })
})

app.post('/api/agents', (req, res) => {
  const payload = req.body || {}
  const data = {
    agents: payload.agents || [],
    tasks: payload.tasks || []
  }
  writeData(data)
  res.json({ ok: true })
  setTimeout(() => syncCrons(data.agents), 50)
})

app.post('/api/tasks', (req, res) => {
  const { title, description = '', agent = 'jarvis', status = 'todo' } = req.body || {}
  if (!title) return res.status(400).json({ error: 'title is required' })
  const now = Date.now()
  const data = readData()
  const task = { id: 't' + now, title, description, agent, status, created_at: now, updated_at: now }
  data.tasks.push(task)
  writeData(data)
  res.json({ ok: true, task })
})

app.get('/api/tasks', (req, res) => {
  const data = readData()
  res.json({ tasks: data.tasks || [] })
})

function updateTaskById(taskId, patch = {}) {
  const data = readData()
  const idx = (data.tasks || []).findIndex(t => t.id === taskId)
  if (idx === -1) return { ok: false, notFound: true }

  const prev = data.tasks[idx]
  const next = {
    ...prev,
    ...patch,
    updated_at: Date.now()
  }

  if (patch.status === 'done' && !prev.completed_at) {
    next.completed_at = Date.now()
  }

  data.tasks[idx] = next
  writeData(data)
  return { ok: true, task: next }
}

app.patch('/api/tasks/:id', (req, res) => {
  const result = updateTaskById(req.params.id, req.body || {})
  if (result.notFound) return res.status(404).json({ error: 'task not found' })
  res.json(result)
})

app.put('/api/tasks/:id', (req, res) => {
  const result = updateTaskById(req.params.id, req.body || {})
  if (result.notFound) return res.status(404).json({ error: 'task not found' })
  res.json(result)
})

app.post('/api/tasks/:id/complete', (req, res) => {
  const result = updateTaskById(req.params.id, { status: 'done' })
  if (result.notFound) return res.status(404).json({ error: 'task not found' })
  res.json(result)
})

app.get('/api/models', (req, res) => {
  const models = readAvailableModels()
  res.json({ models })
})

// Fetch agents from main API (port 8001) for complete agent list
async function fetchMainAgents() {
  try {
    const mainApi = process.env.MAIN_API || 'http://127.0.0.1:8001'
    const res = await fetch(`${mainApi}/api/agents`)
    const json = await res.json()
    return json.agents || []
  } catch {
    return []
  }
}

// Match a cron job name to an agent id
function matchJobToAgent(jobName, agents) {
  const name = (jobName || '').toLowerCase()
  // Sort agents by name length desc so longer names match first (e.g. "whatsapp comercial" before "whatsapp")
  const sorted = [...agents].sort((a, b) => (b.name?.length || 0) - (a.name?.length || 0))
  for (const agent of sorted) {
    if (name.includes(agent.id) || name.includes(agent.name.toLowerCase())) {
      return agent.id
    }
  }
  return null
}

// Detailed cron status for all agents
app.get('/api/agents/cron-details', async (req, res) => {
  try {
    const jobs = listCronJobs()
    const now = Date.now()
    // Use agents from main API (complete list) with fallback to local data
    let agentList = await fetchMainAgents()
    if (!agentList.length) {
      agentList = readData().agents || []
    }
    const agents = {}

    for (const job of jobs) {
      if (!job.enabled) continue
      const agentId = matchJobToAgent(job.name, agentList)
      if (!agentId) continue

      const state = job.state || {}
      const lastRun = state.lastRunAtMs || 0
      const lastDuration = state.lastDurationMs || 0
      const nextRun = state.nextRunAtMs || 0
      const elapsed = now - lastRun
      const maxExpected = Math.max(lastDuration * 2, 120000)
      const running = lastRun > 0 && elapsed < maxExpected && elapsed < 900000
      const model = job.payload?.model || null

      // Keep the job with the most recent lastRun per agent
      if (!agents[agentId] || (lastRun > (agents[agentId].lastRunAt || 0))) {
        agents[agentId] = {
          running,
          lastRunAt: lastRun || null,
          lastDuration,
          nextRunAt: nextRun || null,
          lastStatus: state.lastStatus || null,
          consecutiveErrors: state.consecutiveErrors || 0,
          cronName: job.name || null,
          model
        }
      }
    }

    res.json({ agents })
  } catch (err) {
    console.error('Cron details failed:', err?.message || err)
    res.json({ agents: {} })
  }
})

// Compat: simple running map
app.get('/api/agents/status', async (req, res) => {
  try {
    const jobs = listCronJobs()
    const now = Date.now()
    let agentList = await fetchMainAgents()
    if (!agentList.length) agentList = readData().agents || []
    const running = {}
    for (const job of jobs) {
      if (!job.enabled) continue
      const agentId = matchJobToAgent(job.name, agentList)
      if (!agentId) continue
      const state = job.state || {}
      const lastRun = state.lastRunAtMs || 0
      const lastDuration = state.lastDurationMs || 60000
      const elapsed = now - lastRun
      const maxExpected = Math.max(lastDuration * 2, 120000)
      if (lastRun > 0 && elapsed < maxExpected && elapsed < 900000) {
        running[agentId] = true
      }
    }
    res.json({ running })
  } catch (err) {
    res.json({ running: {} })
  }
})

// Agent worklog reader
const WORKLOG_DIR = process.env.WORKLOG_DIR || '/root/clawd/agent_worklog'

app.get('/api/agents/:id/worklog', (req, res) => {
  const agentId = req.params.id
  const filePath = path.join(WORKLOG_DIR, `${agentId}.md`)
  try {
    if (!fs.existsSync(filePath)) {
      return res.json({ content: '', lines: 0, agentId })
    }
    const raw = fs.readFileSync(filePath, 'utf-8')
    const lines = raw.split('\n')
    const last100 = lines.slice(-100).join('\n')
    res.json({ content: last100, lines: lines.length, agentId })
  } catch (err) {
    console.error(`Worklog read failed for ${agentId}:`, err?.message || err)
    res.json({ content: '', lines: 0, agentId, error: err?.message })
  }
})

// Simple health
app.get('/health', (req, res) => res.json({ ok: true }))

app.listen(PORT, () => {
  console.log(`Mission Control API on :${PORT}`)
  try {
    const data = readData()
    syncCrons(data.agents)
  } catch (err) {
    console.error('Cron sync on boot failed:', err?.message || err)
  }
})
