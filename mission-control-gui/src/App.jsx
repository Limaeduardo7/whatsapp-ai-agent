import { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import {
  Shield, Cpu, Search, PenTool, BarChart3, Zap, Layout,
  Image as ImageIcon, Users, Terminal, Activity, Send, Crown,
  MessageSquare, Clock, Save, RefreshCw, Power, PowerOff,
  Plus, CheckCircle2, Circle, Kanban as KanbanIcon, LayoutDashboard, Menu, X,
  FileText, ChevronLeft, ChevronRight, Eye, Edit3, Briefcase, ExternalLink, Calendar
} from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  PieChart, Pie, Cell, BarChart, Bar, Legend, AreaChart, Area
} from 'recharts'

// Skeleton loading components
function Skeleton({ className = '' }) {
  return <div className={`animate-pulse bg-white/[0.06] rounded-xl ${className}`} />
}

function MetricsSkeleton() {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="p-4 md:p-5 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
          <Skeleton className="h-3 w-16 mb-3" />
          <Skeleton className="h-8 w-20" />
        </div>
      ))}
    </div>
  )
}

function AgentCardSkeleton() {
  return (
    <div className="p-4 md:p-5 rounded-2xl md:rounded-3xl border border-white/[0.06] bg-white/[0.02]">
      <div className="flex items-center gap-3 mb-4">
        <Skeleton className="w-10 h-10 md:w-11 md:h-11 rounded-xl md:rounded-2xl" />
        <div className="flex-1">
          <Skeleton className="h-3.5 w-24 mb-2" />
          <Skeleton className="h-2.5 w-16" />
        </div>
        <Skeleton className="w-9 h-9 rounded-xl" />
      </div>
      <div className="grid grid-cols-3 gap-2">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="bg-black/30 rounded-lg px-2 py-1.5 border border-white/[0.04]">
            <Skeleton className="h-2 w-10 mb-1.5" />
            <Skeleton className="h-3 w-12" />
          </div>
        ))}
      </div>
    </div>
  )
}

function FeedSkeleton() {
  return (
    <div className="space-y-3 p-4 md:p-6">
      {[...Array(6)].map((_, i) => (
        <div key={i} className="flex gap-2" style={{ opacity: 1 - i * 0.12 }}>
          <Skeleton className="h-3 w-12 shrink-0" />
          <Skeleton className="h-3 w-16 shrink-0" />
          <Skeleton className="h-3 flex-1" />
        </div>
      ))}
    </div>
  )
}

function KanbanSkeleton() {
  return (
    <div className="flex-1 flex flex-col lg:flex-row gap-4 md:gap-6 overflow-hidden">
      {[...Array(3)].map((_, col) => (
        <div key={col} className="flex-1 min-w-0 bg-white/[0.02] border border-white/[0.06] rounded-2xl md:rounded-3xl p-4 md:p-5">
          <div className="flex items-center gap-2.5 mb-4">
            <Skeleton className="w-2.5 h-2.5 rounded-full" />
            <Skeleton className="h-3 w-20" />
          </div>
          <div className="space-y-3">
            {[...Array(2 + col)].map((_, i) => (
              <div key={i} className="p-3 rounded-xl border border-white/[0.04] bg-black/20">
                <Skeleton className="h-3.5 w-3/4 mb-2" />
                <Skeleton className="h-2.5 w-1/2" />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

function FullPageLoader() {
  return (
    <div className="flex-1 flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          className="w-10 h-10 rounded-2xl bg-gradient-to-br from-neon-purple to-neon-blue flex items-center justify-center shadow-[0_0_30px_rgba(180,126,255,0.3)]"
        >
          <Cpu className="w-5 h-5 text-white" />
        </motion.div>
        <p className="text-[10px] uppercase tracking-[0.2em] text-white/30 font-medium">Carregando Mission Control</p>
      </div>
    </div>
  )
}

const DEFAULT_API_BASE = 'http://31.97.165.161:8001'
const API_BASE = import.meta.env.VITE_API_BASE
  || (typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.hostname}:8001` : DEFAULT_API_BASE)
  || DEFAULT_API_BASE
const API_URL = import.meta.env.VITE_API_URL || `${API_BASE}/api/agents`
const FEED_PAGE_SIZE = 30

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [data, setData] = useState({ agents: [], tasks: [] })
  const [leads, setLeads] = useState({})
  const [availableModels, setAvailableModels] = useState([])
  const [mission, setMission] = useState('')
  const [loading, setLoading] = useState(true)
  const [initialLoad, setInitialLoad] = useState(true)
  const [saving, setSaving] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [logs, setLogs] = useState([{ id: 1, time: '05:40', from: 'Jarvis', text: 'Interface v5.1 inicializada com abas e detalhamento de tarefas.', type: 'system' }])
  const [agentMessage, setAgentMessage] = useState('')
  const [agentFrom, setAgentFrom] = useState('jarvis')
  const [agentTo, setAgentTo] = useState('all')
  const [feedPage, setFeedPage] = useState(1)
  const [feedTotal, setFeedTotal] = useState(0)
  const [toast, setToast] = useState(null)
  const [contextItems, setContextItems] = useState([])
  const [contextKey, setContextKey] = useState('')
  const [contextValue, setContextValue] = useState('')
  const [agentRunning, setAgentRunning] = useState({})
  const [cronDetails, setCronDetails] = useState({})
  const [terminalAgent, setTerminalAgent] = useState(null)
  const [worklogContent, setWorklogContent] = useState('')
  const [worklogLines, setWorklogLines] = useState(0)
  const [connectionOk, setConnectionOk] = useState(true)
  const [lastRefresh, setLastRefresh] = useState(null)
  const feedRef = useRef(null)
  const lastDoneIdsRef = useRef(new Set())
  const lastInProgressIdsRef = useRef(new Set())
  const lastFeedMsgIdRef = useRef(null)
  const initializedRef = useRef(false)

  const formatModelLabel = (modelId) => {
    if (!modelId) return ''
    const name = modelId.split('/').slice(1).join('/') || modelId
    return name
      .replace(/[-_]/g, ' ')
      .replace(/\b\w/g, (c) => c.toUpperCase())
  }

  const groupModels = (models) => {
    const providerLabels = {
      'google-antigravity': 'Antigravity',
      'openai-codex': 'OpenAI Codex',
      'google': 'Google Direct',
      'moonshotai': 'Moonshot',
      'minimax': 'MiniMax',
      'anthropic': 'Anthropic'
    }
    const groups = {}
    models.forEach((modelId) => {
      const provider = modelId.split('/')[0] || 'outros'
      const label = providerLabels[provider] || provider.charAt(0).toUpperCase() + provider.slice(1)
      if (!groups[label]) groups[label] = []
      groups[label].push(modelId)
    })
    return groups
  }

  const timeAgoShort = (ts) => {
    if (!ts) return null
    const secs = Math.floor((Date.now() - ts) / 1000)
    if (secs < 60) return 'agora'
    const mins = Math.floor(secs / 60)
    if (mins < 60) return `${mins}min`
    const hrs = Math.floor(mins / 60)
    if (hrs < 24) return `${hrs}h`
    return `${Math.floor(hrs / 24)}d`
  }

  const formatDuration = (ms) => {
    if (!ms) return '—'
    const secs = Math.round(ms / 1000)
    if (secs < 60) return `${secs}s`
    const mins = Math.round(secs / 60)
    return `${mins}min`
  }

  const formatTime = (ts) => {
    if (!ts) return '—'
    const d = new Date(ts)
    return `${String(d.getUTCHours()).padStart(2, '0')}:${String(d.getUTCMinutes()).padStart(2, '0')} UTC`
  }

  const showToast = (message, tone = 'success') => {
    setToast({ message, tone })
    setTimeout(() => setToast(null), 2500)
  }

  const metrics = (() => {
    const tasks = data.tasks || []
    const total = tasks.length
    const inProgress = tasks.filter(t => t.status === 'in_progress').length
    const done = tasks.filter(t => t.status === 'done').length
    const durations = tasks
      .filter(t => t.status === 'done' && t.completed_at && t.created_at)
      .map(t => (t.completed_at - t.created_at) / 60000)
    const avg = durations.length ? Math.round(durations.reduce((a, b) => a + b, 0) / durations.length) : null
    return { total, inProgress, done, avg }
  })()

  const highlightMentions = (text) => {
    const parts = text.split(/(@[\w-]+)/g)
    const agentIds = new Set((data.agents || []).map(a => a.id))
    return parts.map((p, i) => {
      if (p.startsWith('@')) {
        const tag = p.slice(1)
        if (tag === 'all' || agentIds.has(tag)) {
          return <span key={i} className="text-neon-purple font-semibold">{p}</span>
        }
      }
      return <span key={i}>{p}</span>
    })
  }

  // Agent files modal state
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [agentFiles, setAgentFiles] = useState({})
  const [activeFile, setActiveFile] = useState(null)
  const [fileContent, setFileContent] = useState('')
  const [fileSaving, setFileSaving] = useState(false)
  const [fileLoading, setFileLoading] = useState(false)

  const playDoneSound = useCallback(() => {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)()
      const o = ctx.createOscillator()
      const g = ctx.createGain()
      o.type = 'sine'
      o.frequency.value = 880
      g.gain.value = 0.05
      o.connect(g)
      g.connect(ctx.destination)
      o.start()
      setTimeout(() => { o.stop(); ctx.close() }, 180)
    } catch (e) {}
  }, [])

  const playFeedSound = useCallback(() => {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)()
      const o = ctx.createOscillator()
      const g = ctx.createGain()
      o.type = 'triangle'
      o.frequency.value = 523.25 // C5
      g.gain.value = 0.05
      o.connect(g)
      g.connect(ctx.destination)
      o.start()
      setTimeout(() => { o.stop(); ctx.close() }, 100)
    } catch (e) {}
  }, [])

  const speakTask = useCallback(async (title) => {
    try {
      const res = await fetch(`${API_BASE}/api/tts?text=${encodeURIComponent(`Nova tarefa em andamento: ${title}`)}`)
      const json = await res.json()
      if (!json?.audio_b64) return
      const audio = new Audio(`data:${json.mime || 'audio/mpeg'};base64,${json.audio_b64}`)
      audio.play()
    } catch (e) {}
  }, [])

  const fetchData = async () => {
    setLoading(true)
    try {
      const res = await fetch(API_URL)
      const json = await res.json()
      setData(json)
      if (Array.isArray(json?.models)) setAvailableModels(json.models)

      const doneIds = new Set((json.tasks || []).filter(t => t.status === 'done').map(t => t.id))
      const prevDone = lastDoneIdsRef.current || new Set()
      const newlyDone = [...doneIds].filter(id => !prevDone.has(id))
      if (newlyDone.length) playDoneSound()
      lastDoneIdsRef.current = doneIds

      const inProgressIds = new Set((json.tasks || []).filter(t => t.status === 'in_progress').map(t => t.id))
      const prevInProgress = lastInProgressIdsRef.current || new Set()
      const newlyInProgress = [...inProgressIds].filter(id => !prevInProgress.has(id))
      if (initializedRef.current && newlyInProgress.length) {
        const taskMap = new Map((json.tasks || []).map(t => [t.id, t]))
        newlyInProgress.forEach(id => {
          const t = taskMap.get(id)
          if (t?.title) speakTask(t.title)
        })
      }
      lastInProgressIdsRef.current = inProgressIds
      if (!initializedRef.current) initializedRef.current = true
      if (initialLoad) setInitialLoad(false)
    } catch (err) { console.error(err); showToast('Erro ao carregar dados', 'error') }
    finally { setLoading(false) }
  }

  const MC_BASE = import.meta.env.VITE_MC_API_BASE
    || (typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.hostname}:8011` : 'http://127.0.0.1:8011')

  const fetchAgentStatus = async () => {
    try {
      const res = await fetch(`${MC_BASE}/api/agents/cron-details`)
      const json = await res.json()
      const details = json.agents || {}
      setCronDetails(details)
      const running = {}
      for (const [id, info] of Object.entries(details)) {
        if (info.running) running[id] = true
      }
      setAgentRunning(running)
      setConnectionOk(true)
      setLastRefresh(Date.now())
    } catch (err) {
      console.error(err)
      setConnectionOk(false)
    }
  }

  const fetchWorklog = async (agentId) => {
    try {
      const res = await fetch(`${MC_BASE}/api/agents/${agentId}/worklog`)
      const json = await res.json()
      setWorklogContent(json.content || '')
      setWorklogLines(json.lines || 0)
    } catch (err) { console.error(err) }
  }

  const fetchLeads = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/leads`)
      const json = await res.json()
      setLeads(json)
    } catch (err) { console.error(err) }
  }

  const fetchModels = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/models`)
      const json = await res.json()
      const models = Array.isArray(json?.models) ? json.models : []
      setAvailableModels(models)
    } catch (err) { console.error(err); showToast('Erro ao carregar modelos', 'error') }
  }

  const fetchFeed = async (page) => {
    const p = page || feedPage
    const offset = (p - 1) * FEED_PAGE_SIZE
    try {
      const res = await fetch(`${API_BASE}/api/feed?limit=${FEED_PAGE_SIZE}&offset=${offset}`)
      const json = await res.json()
      setFeedTotal(json.total || 0)
      const logsArr = (json.logs || []).map((l, idx) => ({
        id: `${l.time}-${idx}`,
        time: new Date(l.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        from: l.from || 'System',
        text: l.text || '',
        type: l.type || 'system'
      })).reverse()
      
      if (initializedRef.current && logsArr.length > 0) {
        const latestMsg = logsArr[logsArr.length - 1]
        if (lastFeedMsgIdRef.current && lastFeedMsgIdRef.current !== latestMsg.id) {
          playFeedSound()
        }
        lastFeedMsgIdRef.current = latestMsg.id
      }

      setLogs(logsArr)
    } catch (err) { console.error(err) }
  }

  const fetchContext = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/context`)
      const json = await res.json()
      setContextItems(json.items || [])
    } catch (err) { console.error(err) }
  }

  const saveContext = async () => {
    if (!contextKey.trim()) return
    try {
      await fetch(`${API_BASE}/api/context`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key: contextKey.trim(), value: contextValue, agent: 'mission-control' })
      })
      setContextKey('')
      setContextValue('')
      fetchContext()
      showToast('Contexto salvo', 'success')
    } catch (err) { console.error(err); showToast('Erro ao salvar contexto', 'error') }
  }

  const sendAgentMessage = async () => {
    const text = agentMessage.trim()
    if (!text) return
    const mention = agentTo !== 'all' ? `@${agentTo} ` : ''
    const payload = {
      agent: agentFrom,
      type: 'agent',
      text: `[${agentFrom} → ${agentTo}] ${mention}${text}`
    }
    try {
      await fetch(`${API_BASE}/api/feed`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      setAgentMessage('')
      fetchFeed(1)
    } catch (err) { console.error(err) }
  }

  const saveData = async (updatedData) => {
    setSaving(true)
    try {
      await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatedData || data)
      })
      showToast('Salvo', 'success')
    } catch (err) { console.error(err); showToast('Erro ao salvar', 'error') }
    finally { setSaving(false) }
  }

  useEffect(() => { fetchData(); fetchFeed(1); fetchModels(); fetchContext(); fetchLeads(); fetchAgentStatus() }, [])

  // Auto-fetch worklog when terminal agent changes
  useEffect(() => {
    if (terminalAgent) fetchWorklog(terminalAgent)
  }, [terminalAgent])

  // Real-time refresh (polling) - only auto-refresh on page 1
  useEffect(() => {
    const id = setInterval(() => {
      fetchData()
      fetchLeads()
      fetchAgentStatus()
      if (feedPage === 1) fetchFeed(1)
      if (terminalAgent) fetchWorklog(terminalAgent)
    }, 5000)
    return () => clearInterval(id)
  }, [feedPage, terminalAgent])

  const updateAgent = (id, field, value) => {
    const updated = { ...data, agents: data.agents.map(a => a.id === id ? { ...a, [field]: value } : a) }
    setData(updated)
    saveData(updated)
  }

  const moveTask = (taskId, newStatus) => {
    const now = Date.now()
    const updated = { ...data, tasks: data.tasks.map(t => t.id === taskId ? { ...t, status: newStatus, updated_at: now, completed_at: newStatus === 'done' ? now : t.completed_at } : t) }
    setData(updated)
    if (newStatus === 'in_progress') {
      const t = data.tasks.find(x => x.id === taskId)
      if (t?.title) speakTask(t.title)
    }
    saveData(updated)
  }

  const editTask = (taskId) => {
    const task = data.tasks.find(t => t.id === taskId)
    if (!task) return
    const title = prompt("Editar título:", task.title)
    if (!title) return
    const description = prompt("Editar descrição:", task.description || '')
    const agent = prompt("Agente responsável:", task.agent || 'jarvis')
    const updated = {
      ...data,
      tasks: data.tasks.map(t => t.id === taskId ? { ...t, title, description: description || '', agent: agent || task.agent, updated_at: Date.now() } : t)
    }
    setData(updated)
    saveData(updated)
  }

  const deleteTask = (taskId) => {
    const task = data.tasks.find(t => t.id === taskId)
    if (!task) return
    if (!confirm(`Excluir tarefa "${task.title}"?`)) return
    const updated = { ...data, tasks: data.tasks.filter(t => t.id !== taskId) }
    setData(updated)
    saveData(updated)
  }

  const addTask = () => {
    const title = prompt("Título da tarefa:")
    if (!title) return
    const description = prompt("Descrição da tarefa:")
    const agent = prompt("Agente responsável:", 'jarvis')
    const now = Date.now()
    const newTask = { id: 't' + now, title, description: description || '', agent: agent || 'jarvis', status: 'todo', created_at: now, updated_at: now }
    const updated = { ...data, tasks: [...data.tasks, newTask] }
    setData(updated)
    saveData(updated)
  }

  const createTask = (title, description, agent) => {
    if (!title?.trim()) return
    const now = Date.now()
    const newTask = { id: 't' + now, title: title.trim(), description: (description || '').trim(), agent: agent || 'jarvis', status: 'todo', created_at: now, updated_at: now }
    const updated = { ...data, tasks: [...data.tasks, newTask] }
    setData(updated)
    saveData(updated)
  }

  // Agent files functions
  const openAgentFiles = async (agent) => {
    setSelectedAgent(agent)
    setFileLoading(true)
    setActiveFile(null)
    setFileContent('')
    try {
      const res = await fetch(`${API_BASE}/api/agents/${agent.id}/files`)
      const json = await res.json()
      const files = json.files || {}
      setAgentFiles(files)
      const firstFile = Object.keys(files)[0]
      if (firstFile) {
        setActiveFile(firstFile)
        setFileContent(files[firstFile].content)
      }
    } catch (err) { console.error(err) }
    finally { setFileLoading(false) }
  }

  const selectFile = (filename) => {
    setActiveFile(filename)
    setFileContent(agentFiles[filename]?.content || '')
  }

  const saveFile = async () => {
    if (!selectedAgent || !activeFile) return
    setFileSaving(true)
    try {
      await fetch(`${API_BASE}/api/agents/${selectedAgent.id}/files/${activeFile}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: fileContent })
      })
      setAgentFiles(prev => ({ ...prev, [activeFile]: { ...prev[activeFile], content: fileContent } }))
    } catch (err) { console.error(err) }
    finally { setFileSaving(false) }
  }

  const closeAgentFiles = () => {
    setSelectedAgent(null)
    setAgentFiles({})
    setActiveFile(null)
    setFileContent('')
  }

  const feedTotalPages = Math.max(1, Math.ceil(feedTotal / FEED_PAGE_SIZE))

  const goToFeedPage = (page) => {
    const p = Math.max(1, Math.min(page, feedTotalPages))
    setFeedPage(p)
    fetchFeed(p)
    if (feedRef.current) feedRef.current.scrollTop = 0
  }

  const sendMission = async () => {
    if (!mission) return
    try {
      await fetch(`${API_BASE}/api/feed`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: mission, agent: 'Comandante', type: 'user' })
      })
      setFeedPage(1)
      fetchFeed(1)
    } catch (e) { console.error(e) }
    setMission('')
  }

  const getIcon = (iconName, color) => {
    const props = { className: `w-5 h-5 text-${color}` };
    switch(iconName) {
      case 'Cpu': return <Cpu {...props} />;
      case 'Search': return <Search {...props} />;
      case 'Layout': return <Layout {...props} />;
      case 'PenTool': return <PenTool {...props} />;
      case 'BarChart3': return <BarChart3 {...props} />;
      case 'Users': return <Users {...props} />;
      case 'Zap': return <Zap {...props} />;
      case 'Activity': return <Activity {...props} />;
      case 'ImageIcon': return <ImageIcon {...props} />;
      case 'Shield': return <Shield {...props} />;
      case 'MessageSquare': return <MessageSquare {...props} />;
      case 'Crown': return <Crown {...props} />;
      default: return <Cpu {...props} />;
    }
  }

  return (
    <div className="min-h-screen bg-[#020202] text-white font-sans selection:bg-purple-500/30 flex flex-col">
      {toast && (
        <div className={`fixed top-4 right-4 z-[200] px-4 py-2 rounded-xl text-xs font-semibold shadow-lg border ${toast.tone === 'error' ? 'bg-red-500/20 border-red-400/30 text-red-200' : 'bg-emerald-500/20 border-emerald-400/30 text-emerald-100'}`}>
          {toast.message}
        </div>
      )}
      {/* HEADER - Apple Style Glass */}
      <header className="sticky top-0 z-50 h-14 md:h-16 border-b border-white/[0.06] bg-black/60 backdrop-blur-xl backdrop-saturate-150 flex items-center justify-between px-4 md:px-8">
        <div className="flex items-center gap-3 md:gap-8">
          {/* Logo */}
          <div className="flex items-center gap-2 md:gap-3">
            <div className="w-7 h-7 md:w-8 md:h-8 rounded-xl bg-gradient-to-br from-neon-purple to-neon-blue flex items-center justify-center shadow-[0_0_20px_rgba(180,126,255,0.3)]">
              <Cpu className="w-4 h-4 md:w-5 md:h-5 text-white" />
            </div>
            <h1 className="text-base md:text-xl font-semibold tracking-tight">
              Mission <span className="text-neon-purple">Control</span>
            </h1>
          </div>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center gap-1 bg-white/[0.04] p-1 rounded-xl border border-white/[0.06]">
             <button
               onClick={() => setActiveTab('dashboard')}
               className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium tracking-wide transition-all duration-200 ${activeTab === 'dashboard' ? 'bg-white/10 text-white shadow-sm' : 'text-white/50 hover:text-white/80 hover:bg-white/[0.04]'}`}
             >
               <LayoutDashboard className="w-4 h-4" /> Dashboard
             </button>
             <button
               onClick={() => setActiveTab('kanban')}
               className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium tracking-wide transition-all duration-200 ${activeTab === 'kanban' ? 'bg-white/10 text-white shadow-sm' : 'text-white/50 hover:text-white/80 hover:bg-white/[0.04]'}`}
             >
               <KanbanIcon className="w-4 h-4" /> Kanban
             </button>
             <button
               onClick={() => setActiveTab('terminal')}
               className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium tracking-wide transition-all duration-200 ${activeTab === 'terminal' ? 'bg-white/10 text-white shadow-sm' : 'text-white/50 hover:text-white/80 hover:bg-white/[0.04]'}`}
             >
               <Terminal className="w-4 h-4" /> Terminal
             </button>
             <button
               onClick={() => setActiveTab('crm')}
               className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium tracking-wide transition-all duration-200 ${activeTab === 'crm' ? 'bg-white/10 text-white shadow-sm' : 'text-white/50 hover:text-white/80 hover:bg-white/[0.04]'}`}
             >
               <Briefcase className="w-4 h-4" /> CRM
             </button>
          </nav>
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-2 md:gap-4">
          <button onClick={fetchData} className="p-2 hover:bg-white/[0.06] rounded-xl transition-all text-white/40 hover:text-white active:scale-95">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          {/* Save button removed */}
          {/* Mobile menu button removed (bottom tabs used) */}
        </div>
      </header>

      {/* Mobile Navigation Dropdown */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="md:hidden fixed top-14 left-0 right-0 z-40 bg-black/80 backdrop-blur-2xl border-b border-white/[0.06] p-4 space-y-2"
          >
            <button
              onClick={() => { setActiveTab('dashboard'); setMobileMenuOpen(false); }}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-sm font-medium transition-all ${activeTab === 'dashboard' ? 'bg-white/10 text-white' : 'text-white/60 hover:bg-white/[0.04]'}`}
            >
              <LayoutDashboard className="w-5 h-5" /> Dashboard
            </button>
            <button
              onClick={() => { setActiveTab('kanban'); setMobileMenuOpen(false); }}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-sm font-medium transition-all ${activeTab === 'kanban' ? 'bg-white/10 text-white' : 'text-white/60 hover:bg-white/[0.04]'}`}
            >
              <KanbanIcon className="w-5 h-5" /> Kanban
            </button>
            <button
              onClick={() => { setActiveTab('terminal'); setMobileMenuOpen(false); }}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-sm font-medium transition-all ${activeTab === 'terminal' ? 'bg-white/10 text-white' : 'text-white/60 hover:bg-white/[0.04]'}`}
            >
              <Terminal className="w-5 h-5" /> Terminal
            </button>
            <button
              onClick={() => { setActiveTab('crm'); setMobileMenuOpen(false); }}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-sm font-medium transition-all ${activeTab === 'crm' ? 'bg-white/10 text-white' : 'text-white/60 hover:bg-white/[0.04]'}`}
            >
              <Briefcase className="w-5 h-5" /> CRM
            </button>
            <button
              onClick={() => { setActiveTab('feed'); setMobileMenuOpen(false); }}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-sm font-medium transition-all ${activeTab === 'feed' ? 'bg-white/10 text-white' : 'text-white/60 hover:bg-white/[0.04]'}`}
            >
              <Terminal className="w-5 h-5" /> Intelligence Feed
            </button>
            <button onClick={() => saveData()} className="sm:hidden w-full flex items-center justify-center gap-2 px-4 py-3 rounded-2xl bg-white/90 text-black text-sm font-semibold mt-4">
               <Save className="w-4 h-4" /> {saving ? 'Salvando...' : 'Salvar Alterações'}
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* MAIN CONTENT */}
      <main className="flex-1 flex flex-col overflow-hidden p-3 md:p-6 pb-16 md:pb-6 gap-4 md:gap-6 min-h-0">

        {initialLoad ? (
          <FullPageLoader />
        ) : activeTab === 'dashboard' ? (
          <>
            {/* METRICS */}
            <div className="shrink-0 space-y-3">
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
                <div className="group p-4 md:p-5 rounded-2xl bg-white/[0.03] border border-white/[0.06] backdrop-blur-xl hover:border-white/[0.12] hover:bg-white/[0.05] hover:-translate-y-0.5 transition-all duration-300 cursor-default">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-[9px] uppercase tracking-widest text-white/30">Tarefas</p>
                    <BarChart3 className="w-4 h-4 text-white/10 group-hover:text-white/25 transition-colors" />
                  </div>
                  <p className="text-2xl md:text-3xl font-bold text-white/90">{metrics.total}</p>
                </div>
                <div className="group p-4 md:p-5 rounded-2xl bg-white/[0.03] border border-white/[0.06] backdrop-blur-xl hover:border-white/[0.12] hover:bg-white/[0.05] hover:-translate-y-0.5 transition-all duration-300 cursor-default">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-[9px] uppercase tracking-widest text-white/30">Em andamento</p>
                    <Activity className="w-4 h-4 text-white/10 group-hover:text-white/30 transition-colors" />
                  </div>
                  <p className="text-2xl md:text-3xl font-bold text-neon-blue">{metrics.inProgress}</p>
                </div>
                <div className="group p-4 md:p-5 rounded-2xl bg-white/[0.03] border border-white/[0.06] backdrop-blur-xl hover:border-emerald-400/20 hover:bg-white/[0.05] hover:-translate-y-0.5 transition-all duration-300 cursor-default">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-[9px] uppercase tracking-widest text-white/30">Finalizadas</p>
                    <CheckCircle2 className="w-4 h-4 text-white/10 group-hover:text-emerald-400/40 transition-colors" />
                  </div>
                  <p className="text-2xl md:text-3xl font-bold text-emerald-300">{metrics.done}</p>
                </div>
                <div className="group p-4 md:p-5 rounded-2xl bg-white/[0.03] border border-white/[0.06] backdrop-blur-xl hover:border-white/[0.12] hover:bg-white/[0.05] hover:-translate-y-0.5 transition-all duration-300 cursor-default">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-[9px] uppercase tracking-widest text-white/30">Tempo médio</p>
                    <Clock className="w-4 h-4 text-white/10 group-hover:text-white/25 transition-colors" />
                  </div>
                  <p className="text-2xl md:text-3xl font-bold text-white/80">{metrics.avg ? `${metrics.avg} min` : '—'}</p>
                </div>
              </div>
              {metrics.total > 0 && (
                <div className="flex items-center gap-3">
                  <div className="flex-1 h-1.5 bg-white/[0.04] rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${Math.round((metrics.done / metrics.total) * 100)}%` }}
                      transition={{ duration: 1.2, ease: 'easeOut' }}
                      className="h-full rounded-full"
                      style={{ background: 'linear-gradient(to right, #b47eff, #34d399)' }}
                    />
                  </div>
                  <span className="text-[9px] text-white/25 font-mono shrink-0">{Math.round((metrics.done / metrics.total) * 100)}%</span>
                </div>
              )}
            </div>

            {/* SQUAD + FEED ROW */}
            <div className="flex-1 flex flex-col lg:flex-row gap-4 md:gap-6 min-h-0 overflow-hidden">
            {/* SQUAD AREA */}
            <section className="lg:w-[380px] flex flex-col gap-3 md:gap-4 lg:pr-2 min-h-0 max-h-[45vh] lg:max-h-full shrink-0 overflow-hidden">
              <h2 className="text-[10px] font-semibold uppercase tracking-[0.15em] text-white/30 px-1 shrink-0">Squad & Brain Engine</h2>
              <div className="flex flex-col gap-3 flex-1 min-h-0 overflow-y-auto pr-2 styled-scrollbar">
                {!data.agents.length ? (
                  [...Array(4)].map((_, i) => <AgentCardSkeleton key={i} />)
                ) : data.agents.map((agent) => {
                  const isBusy = !!agentRunning[agent.id]
                  return (
                    <motion.div
                      layout
                      key={agent.id}
                      animate={isBusy ? { 
                        borderColor: ["rgba(255,255,255,0.08)", "rgba(180,126,255,0.4)", "rgba(255,255,255,0.08)"],
                        boxShadow: isBusy ? ["0 0 0px rgba(180,126,255,0)", "0 0 15px rgba(180,126,255,0.2)", "0 0 0px rgba(180,126,255,0)"] : "none"
                      } : {}}
                      transition={isBusy ? { duration: 2, repeat: Infinity } : {}}
                      className={`relative overflow-hidden p-4 md:p-5 rounded-2xl md:rounded-3xl border transition-all duration-300 backdrop-blur-xl cursor-pointer hover:border-neon-purple/30 ${agent.enabled ? 'bg-white/[0.03] border-white/[0.08] shadow-xl shadow-black/30' : 'bg-transparent border-white/[0.04] opacity-40'}`}
                      onClick={() => openAgentFiles(agent)}
                    >
                      {/* Scanning Line Animation for busy agents */}
                      {isBusy && (
                        <motion.div 
                          className="absolute inset-0 bg-gradient-to-b from-transparent via-neon-purple/5 to-transparent h-[50%]"
                          animate={{ y: ['-100%', '200%'] }}
                          transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
                        />
                      )}
                      <div className="flex items-center justify-between mb-4 relative z-10">
                         <div className="flex items-center gap-3">
                            <div className="relative">
                              <motion.div 
                                animate={isBusy ? { rotate: [0, 360], scale: [1, 1.05, 1] } : {}}
                                transition={isBusy ? { rotate: { duration: 8, repeat: Infinity, ease: "linear" }, scale: { duration: 2, repeat: Infinity } } : {}}
                                className="w-10 h-10 md:w-11 md:h-11 rounded-xl md:rounded-2xl bg-white/[0.04] flex items-center justify-center border border-white/[0.08]"
                              >
                                {getIcon(agent.icon, agent.color)}
                              </motion.div>
                              <span className={`absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border-2 border-[#020202] ${isBusy ? 'bg-neon-blue' : (agent.enabled ? 'bg-emerald-400' : 'bg-white/20')}`} style={(isBusy || agent.enabled) ? { boxShadow: isBusy ? '0 0 8px #00d4ff' : '0 0 6px rgba(52,211,153,0.6)' } : {}}>
                                {(isBusy || agent.enabled) && <span className={`absolute inset-0 rounded-full animate-ping opacity-40 ${isBusy ? 'bg-neon-blue' : 'bg-emerald-400'}`}></span>}
                              </span>
                            </div>
                            <div>
                              <h3 className="font-semibold text-sm md:text-[13px] text-white/90">{agent.name}</h3>
                              <div className="flex items-center gap-2">
                                <p className="text-[10px] text-white/30 uppercase tracking-widest">{agent.role}</p>
                                {isBusy && (
                                  <span className="text-[8px] text-neon-blue font-bold tracking-tighter animate-pulse">EXECUTANDO</span>
                                )}
                              </div>
                            </div>
                         </div>
                       <div className="flex items-center gap-2">
                         <div className="p-2 text-white/20 hover:text-neon-purple/60 transition-all" title="Ver arquivos">
                           <FileText className="w-3.5 h-3.5" />
                         </div>
                         <button
                           onClick={(e) => { e.stopPropagation(); updateAgent(agent.id, 'enabled', !agent.enabled); }}
                           className={`p-2.5 rounded-xl transition-all active:scale-95 ${agent.enabled ? 'text-emerald-400 bg-emerald-400/10 border border-emerald-400/20' : 'text-white/20 bg-white/[0.04] border border-white/[0.06]'}`}
                         >
                            {agent.enabled ? <Power className="w-4 h-4" /> : <PowerOff className="w-4 h-4" />}
                         </button>
                       </div>
                    </div>
                    {/* Cron status info */}
                    {(() => {
                      const cron = cronDetails[agent.id]
                      if (!cron) return null
                      return (
                        <div className="grid grid-cols-3 gap-2 mt-1 relative z-10" onClick={(e) => e.stopPropagation()}>
                          <div className="bg-black/30 rounded-lg px-2 py-1.5 border border-white/[0.04]">
                            <p className="text-[8px] uppercase tracking-widest text-white/20 mb-0.5">Último run</p>
                            <p className="text-[10px] font-mono text-white/60">{cron.running ? 'agora' : (timeAgoShort(cron.lastRunAt) || '—')}</p>
                          </div>
                          <div className="bg-black/30 rounded-lg px-2 py-1.5 border border-white/[0.04]">
                            <p className="text-[8px] uppercase tracking-widest text-white/20 mb-0.5">Duração</p>
                            <p className="text-[10px] font-mono text-white/60">{formatDuration(cron.lastDuration)}</p>
                          </div>
                          <div className="bg-black/30 rounded-lg px-2 py-1.5 border border-white/[0.04]">
                            <p className="text-[8px] uppercase tracking-widest text-white/20 mb-0.5">Próximo</p>
                            <p className="text-[10px] font-mono text-neon-blue/70">{formatTime(cron.nextRunAt)}</p>
                          </div>
                          {cron.model && (
                            <div className="col-span-3 bg-black/30 rounded-lg px-2 py-1.5 border border-white/[0.04] flex items-center gap-1.5">
                              <Cpu className="w-3 h-3 text-white/15 shrink-0" />
                              <p className="text-[9px] font-mono text-white/40 truncate">{cron.model.split('/').pop()}</p>
                            </div>
                          )}
                          {cron.consecutiveErrors > 0 && (
                            <div className="col-span-3 flex items-center gap-1.5 px-2 py-1 bg-red-500/10 border border-red-500/20 rounded-lg">
                              <span className="w-1.5 h-1.5 rounded-full bg-red-400"></span>
                              <span className="text-[9px] text-red-300">{cron.consecutiveErrors} erro(s) consecutivo(s)</span>
                            </div>
                          )}
                        </div>
                      )
                    })()}
                  </motion.div>
                  )
                })}
              </div>
            </section>

            {/* INTELLIGENCE FEED */}
            <section className="hidden lg:flex flex-1 flex-col gap-4 md:gap-6 min-h-0 min-w-0 overflow-hidden">
              {/* Context Store removed */}
              {/* Input Area - Glass Effect */}
              <div className="relative group">
                <div className="absolute -inset-0.5 bg-gradient-to-r from-neon-purple/30 to-neon-blue/30 rounded-2xl md:rounded-3xl blur-xl opacity-0 group-focus-within:opacity-100 transition duration-500"></div>
                <div className="relative bg-white/[0.03] border border-white/[0.08] rounded-2xl md:rounded-3xl p-1.5 md:p-2 flex items-center gap-2 backdrop-blur-xl">
                  <input
                    value={mission}
                    onChange={(e) => setMission(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && sendMission()}
                    placeholder="Dite o objetivo macro para o Jarvis..."
                    className="flex-1 bg-transparent border-none focus:ring-0 px-4 md:px-6 py-3 md:py-4 text-sm md:text-base text-white placeholder:text-white/20"
                  />
                  <button
                    onClick={sendMission}
                    className="w-10 h-10 md:w-12 md:h-12 rounded-xl md:rounded-2xl bg-white text-black flex items-center justify-center hover:bg-neon-purple hover:text-white transition-all active:scale-95 shadow-lg"
                  >
                    <Send className="w-4 h-4 md:w-5 md:h-5" />
                  </button>
                </div>
              </div>

              {/* Feed Area - Glass Card */}
              <div className="flex-1 min-h-0 bg-white/[0.02] border border-white/[0.06] rounded-2xl md:rounded-3xl flex flex-col overflow-hidden backdrop-blur-xl">
                {/* Agent Comms */}
                <div className="border-b border-white/[0.06] px-4 md:px-6 py-3 flex flex-col md:flex-row gap-2 md:items-center bg-white/[0.02]">
                  <div className="flex gap-2 items-center">
                    <select value={agentFrom} onChange={(e) => setAgentFrom(e.target.value)} className="bg-black/40 border border-white/[0.06] rounded-lg px-2 py-1 text-[10px] text-white/70">
                      {(data.agents || []).map(a => (
                        <option key={a.id} value={a.id}>{a.name}</option>
                      ))}
                    </select>
                    <select value={agentTo} onChange={(e) => setAgentTo(e.target.value)} className="bg-black/40 border border-white/[0.06] rounded-lg px-2 py-1 text-[10px] text-white/70">
                      <option value="all">Todos</option>
                      {(data.agents || []).map(a => (
                        <option key={a.id} value={a.id}>{a.name}</option>
                      ))}
                    </select>
                  </div>
                  <div className="flex-1 flex gap-2">
                    <input
                      value={agentMessage}
                      onChange={(e) => setAgentMessage(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && sendAgentMessage()}
                      placeholder="Mensagem interna entre agentes..."
                      className="flex-1 bg-black/40 border border-white/[0.06] rounded-lg px-3 py-1.5 text-[11px] text-white/80"
                    />
                    <button onClick={sendAgentMessage} className="px-3 py-1.5 rounded-lg bg-white text-black text-[10px] font-semibold">Enviar</button>
                  </div>
                </div>
                <div className="h-11 md:h-12 border-b border-white/[0.06] px-4 md:px-6 flex items-center justify-between bg-white/[0.02] shrink-0">
                  <div className="flex items-center gap-2 text-[9px] md:text-[10px] font-semibold uppercase tracking-[0.15em] text-white/30">
                    <Terminal className="w-3.5 h-3.5 md:w-4 md:h-4" /> Intelligence Feed
                  </div>
                  <div className="flex items-center gap-2 md:gap-3">
                    {feedPage === 1 && (
                      <div className="flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-neon-blue animate-pulse"></span>
                        <span className="text-neon-blue/80 text-[9px] md:text-[10px] font-semibold uppercase tracking-[0.15em]">LIVE</span>
                      </div>
                    )}
                    <span className="text-[9px] text-white/20 font-mono">{feedTotal} msgs</span>
                  </div>
                </div>
                <div ref={feedRef} className="flex-1 min-h-0 p-4 md:p-6 overflow-y-auto space-y-3 md:space-y-4 font-mono text-xs md:text-sm styled-scrollbar">
                   {logs.length === 0 && loading ? (
                     <FeedSkeleton />
                   ) : logs.length === 0 ? (
                     <div className="text-[10px] text-white/30">Sem mensagens no feed ainda.</div>
                   ) : null}
                   {logs.map(l => (
                     <div key={l.id} className="flex flex-wrap md:flex-nowrap gap-1.5 md:gap-2">
                       <span className="text-white/15 shrink-0">[{l.time}]</span>
                       <span className="text-neon-purple shrink-0">{l.from}:</span>
                       <span className="text-white/70 break-words">{highlightMentions(l.text)}</span>
                     </div>
                   ))}
                </div>
                {/* Pagination Controls */}
                {feedTotalPages > 1 && (
                  <div className="h-10 md:h-11 border-t border-white/[0.06] px-4 md:px-6 flex items-center justify-between bg-white/[0.02] shrink-0">
                    <button
                      onClick={() => goToFeedPage(feedPage - 1)}
                      disabled={feedPage <= 1}
                      className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[10px] font-medium text-white/40 hover:text-white/80 hover:bg-white/[0.06] transition-all disabled:opacity-20 disabled:cursor-not-allowed"
                    >
                      <ChevronLeft className="w-3 h-3" /> Anterior
                    </button>
                    <div className="flex items-center gap-1.5">
                      {Array.from({ length: Math.min(feedTotalPages, 5) }, (_, i) => {
                        let page
                        if (feedTotalPages <= 5) {
                          page = i + 1
                        } else if (feedPage <= 3) {
                          page = i + 1
                        } else if (feedPage >= feedTotalPages - 2) {
                          page = feedTotalPages - 4 + i
                        } else {
                          page = feedPage - 2 + i
                        }
                        return (
                          <button
                            key={page}
                            onClick={() => goToFeedPage(page)}
                            className={`w-7 h-7 rounded-lg text-[10px] font-semibold transition-all ${feedPage === page ? 'bg-neon-purple/20 text-neon-purple border border-neon-purple/30' : 'text-white/30 hover:text-white/60 hover:bg-white/[0.06]'}`}
                          >
                            {page}
                          </button>
                        )
                      })}
                    </div>
                    <button
                      onClick={() => goToFeedPage(feedPage + 1)}
                      disabled={feedPage >= feedTotalPages}
                      className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[10px] font-medium text-white/40 hover:text-white/80 hover:bg-white/[0.06] transition-all disabled:opacity-20 disabled:cursor-not-allowed"
                    >
                      Próxima <ChevronRight className="w-3 h-3" />
                    </button>
                  </div>
                )}
              </div>
            </section>
            </div>
          </>
        ) : activeTab === 'feed' ? (
          <section className="flex-1 flex flex-col gap-4 min-h-0 min-w-0 overflow-hidden">
            {/* Input Area - Glass Effect */}
            <div className="relative group">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-neon-purple/30 to-neon-blue/30 rounded-2xl blur-xl opacity-0 group-focus-within:opacity-100 transition duration-500"></div>
              <div className="relative bg-white/[0.03] border border-white/[0.08] rounded-2xl p-1.5 flex items-center gap-2 backdrop-blur-xl">
                <input
                  value={mission}
                  onChange={(e) => setMission(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && sendMission()}
                  placeholder="Dite o objetivo macro para o Jarvis..."
                  className="flex-1 bg-transparent border-none focus:ring-0 px-4 py-3 text-sm text-white placeholder:text-white/20"
                />
                <button
                  onClick={sendMission}
                  className="w-10 h-10 rounded-xl bg-white text-black flex items-center justify-center hover:bg-neon-purple hover:text-white transition-all active:scale-95 shadow-lg"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Feed Area - Glass Card */}
            <div className="flex-1 min-h-0 bg-white/[0.02] border border-white/[0.06] rounded-2xl flex flex-col overflow-hidden backdrop-blur-xl">
              <div className="h-11 border-b border-white/[0.06] px-4 flex items-center justify-between bg-white/[0.02] shrink-0">
                <div className="flex items-center gap-2 text-[9px] font-semibold uppercase tracking-[0.15em] text-white/30">
                  <Terminal className="w-3.5 h-3.5" /> Intelligence Feed
                </div>
                <div className="flex items-center gap-2">
                  {feedPage === 1 && (
                    <div className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-neon-blue animate-pulse"></span>
                      <span className="text-neon-blue/80 text-[9px] font-semibold uppercase tracking-[0.15em]">LIVE</span>
                    </div>
                  )}
                  <span className="text-[9px] text-white/20 font-mono">{feedTotal} msgs</span>
                </div>
              </div>
              <div ref={feedRef} className="flex-1 min-h-0 p-4 overflow-y-auto space-y-3 font-mono text-xs styled-scrollbar">
                 {logs.length === 0 && (
                   <div className="text-[10px] text-white/30">Sem mensagens no feed ainda.</div>
                 )}
                 {logs.map(l => (
                   <div key={l.id} className="flex flex-wrap gap-1.5">
                     <span className="text-white/15 shrink-0">[{l.time}]</span>
                     <span className="text-neon-purple shrink-0">{l.from}:</span>
                     <span className="text-white/70 break-words">{highlightMentions(l.text)}</span>
                   </div>
                 ))}
              </div>
              {feedTotalPages > 1 && (
                <div className="h-10 border-t border-white/[0.06] px-4 flex items-center justify-between bg-white/[0.02] shrink-0">
                  <button
                    onClick={() => goToFeedPage(feedPage - 1)}
                    disabled={feedPage <= 1}
                    className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[10px] font-medium text-white/40 hover:text-white/80 hover:bg-white/[0.06] transition-all disabled:opacity-20 disabled:cursor-not-allowed"
                  >
                    <ChevronLeft className="w-3 h-3" /> Anterior
                  </button>
                  <div className="flex items-center gap-1.5">
                    {Array.from({ length: Math.min(feedTotalPages, 5) }, (_, i) => {
                      let page
                      if (feedTotalPages <= 5) {
                        page = i + 1
                      } else if (feedPage <= 3) {
                        page = i + 1
                      } else if (feedPage >= feedTotalPages - 2) {
                        page = feedTotalPages - 4 + i
                      } else {
                        page = feedPage - 2 + i
                      }
                      return (
                        <button
                          key={page}
                          onClick={() => goToFeedPage(page)}
                          className={`w-7 h-7 rounded-lg text-[10px] font-semibold transition-all ${feedPage === page ? 'bg-neon-purple/20 text-neon-purple border border-neon-purple/30' : 'text-white/30 hover:text-white/60 hover:bg-white/[0.06]'}`}
                        >
                          {page}
                        </button>
                      )
                    })}
                  </div>
                  <button
                    onClick={() => goToFeedPage(feedPage + 1)}
                    disabled={feedPage >= feedTotalPages}
                    className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[10px] font-medium text-white/40 hover:text-white/80 hover:bg-white/[0.06] transition-all disabled:opacity-20 disabled:cursor-not-allowed"
                  >
                    Próxima <ChevronRight className="w-3 h-3" />
                  </button>
                </div>
              )}
            </div>
          </section>
        ) : activeTab === 'kanban' ? (
          /* KANBAN TAB */
          <section className="flex-1 flex flex-col gap-4 md:gap-5 min-h-0 overflow-hidden">
            {!data.agents.length && loading ? (
              <KanbanSkeleton />
            ) : (
              <>
                {/* Kanban Summary Bar */}
                <div className="shrink-0 flex flex-wrap items-center gap-4 md:gap-6 px-1">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-white/30"></span>
                    <span className="text-[10px] text-white/40 font-semibold uppercase tracking-wider">{(data.tasks || []).filter(t => t.status === 'todo').length} a fazer</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full" style={{ background: '#00d4ff' }}></span>
                    <span className="text-[10px] text-white/40 font-semibold uppercase tracking-wider">{(data.tasks || []).filter(t => t.status === 'in_progress').length} em andamento</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                    <span className="text-[10px] text-white/40 font-semibold uppercase tracking-wider">{(data.tasks || []).filter(t => t.status === 'done').length} finalizadas</span>
                  </div>
                </div>
                {/* Kanban Columns */}
                <div className="flex-1 flex flex-col lg:flex-row gap-4 md:gap-6 overflow-auto pb-4 custom-scrollbar">
                  <KanbanColumn title="A Fazer" status="todo" tasks={data.tasks} moveTask={moveTask} editTask={editTask} deleteTask={deleteTask} onCreateTask={createTask} agents={data.agents} />
                  <KanbanColumn title="Em Andamento" status="in_progress" tasks={data.tasks} moveTask={moveTask} editTask={editTask} deleteTask={deleteTask} agents={data.agents} />
                  <KanbanColumn title="Finalizado" status="done" tasks={data.tasks} moveTask={moveTask} editTask={editTask} deleteTask={deleteTask} agents={data.agents} />
                </div>
              </>
            )}
          </section>
        ) : activeTab === 'terminal' ? (
          /* TERMINAL TAB */
          <section className="flex-1 flex flex-col lg:flex-row gap-4 min-h-0 overflow-hidden">
            {!data.agents.length && loading ? (
              <div className="flex-1 flex flex-col lg:flex-row gap-4">
                <div className="lg:w-56 shrink-0 flex lg:flex-col gap-2">
                  {[...Array(5)].map((_, i) => <Skeleton key={i} className="h-10 w-32 lg:w-full" />)}
                </div>
                <Skeleton className="flex-1 min-h-[300px]" />
              </div>
            ) : (
            <>
            {/* Agent Sidebar */}
            <div className="lg:w-56 shrink-0 flex lg:flex-col gap-2 overflow-x-auto lg:overflow-y-auto lg:pr-2 styled-scrollbar">
              <h2 className="hidden lg:block text-[10px] font-semibold uppercase tracking-[0.15em] text-white/30 px-1 mb-1">Agentes</h2>
              {data.agents.map((agent) => {
                const cron = cronDetails[agent.id]
                const isSelected = terminalAgent === agent.id
                return (
                  <button
                    key={agent.id}
                    onClick={() => setTerminalAgent(agent.id)}
                    className={`flex items-center gap-2 px-3 py-2.5 rounded-xl text-left text-[11px] font-medium transition-all whitespace-nowrap shrink-0 ${isSelected ? 'bg-neon-purple/20 text-neon-purple border border-neon-purple/20' : 'text-white/50 bg-white/[0.03] border border-white/[0.06] hover:bg-white/[0.06] hover:text-white/80'}`}
                  >
                    <div className="relative">
                      {getIcon(agent.icon, agent.color)}
                      <span className={`absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full border border-[#020202] ${cron?.running ? 'bg-neon-blue' : (agent.enabled ? 'bg-emerald-400' : 'bg-white/20')}`}></span>
                    </div>
                    <span className="truncate">{agent.name}</span>
                  </button>
                )
              })}
            </div>

            {/* Terminal Content */}
            <div className="flex-1 min-h-0 bg-black/60 border border-white/[0.06] rounded-2xl flex flex-col overflow-hidden backdrop-blur-xl">
              {terminalAgent ? (
                <>
                  <div className="h-11 border-b border-white/[0.06] px-4 flex items-center justify-between bg-white/[0.02] shrink-0">
                    <div className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.15em] text-white/30">
                      <Terminal className="w-3.5 h-3.5" />
                      <span>Worklog — {terminalAgent}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-[9px] text-white/20 font-mono">{worklogLines} linhas</span>
                      <button onClick={() => fetchWorklog(terminalAgent)} className="p-1.5 hover:bg-white/[0.06] rounded-lg transition-all text-white/30 hover:text-white">
                        <RefreshCw className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                  <div className="flex-1 min-h-0 p-4 overflow-y-auto font-mono text-xs leading-relaxed text-white/70 whitespace-pre-wrap styled-scrollbar">
                    {worklogContent || <span className="text-white/20">Sem worklog disponível para este agente.</span>}
                  </div>
                </>
              ) : (
                <div className="flex-1 flex items-center justify-center text-white/20 text-sm">
                  Selecione um agente para ver o worklog
                </div>
              )}
            </div>
            </>
            )}
          </section>
        ) : activeTab === 'crm' ? (
          /* CRM TAB */
          <CrmView leads={leads} />
        ) : (
          /* FEED TAB (mobile) */
          null
        )}
      </main>

      {/* Desktop StatusBar */}
      <div className="hidden md:flex h-8 border-t border-white/[0.06] bg-black/60 backdrop-blur-xl items-center justify-between px-4 md:px-8 text-[9px] font-mono shrink-0">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <span className={`w-1.5 h-1.5 rounded-full ${connectionOk ? 'bg-emerald-400' : 'bg-red-400'}`}></span>
            <span className={connectionOk ? 'text-emerald-400/80' : 'text-red-400/80'}>{connectionOk ? 'Conectado' : 'Offline'}</span>
          </div>
          <div className="text-white/30">
            {Object.values(agentRunning).filter(Boolean).length > 0
              ? <span className="text-neon-blue">{Object.values(agentRunning).filter(Boolean).length} agente(s) executando</span>
              : <span>Nenhum agente executando</span>
            }
          </div>
        </div>
        <div className="flex items-center gap-4">
          {(() => {
            const nextAgent = Object.entries(cronDetails)
              .filter(([, info]) => info.nextRunAt)
              .sort((a, b) => a[1].nextRunAt - b[1].nextRunAt)[0]
            if (!nextAgent) return null
            const agent = data.agents.find(a => a.id === nextAgent[0])
            return (
              <span className="text-white/30">
                Próximo: <span className="text-neon-purple/80">{agent?.name || nextAgent[0]}</span> às {formatTime(nextAgent[1].nextRunAt)}
              </span>
            )
          })()}
          {lastRefresh && (
            <span className="text-white/20">Atualizado {timeAgoShort(lastRefresh)}</span>
          )}
        </div>
      </div>

      {/* Mobile Bottom Tabs */}
      <div className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-black/80 backdrop-blur-xl border-t border-white/[0.08] flex items-center justify-around py-2">
        <button onClick={() => setActiveTab('dashboard')} className={`flex flex-col items-center gap-1 text-[9px] ${activeTab === 'dashboard' ? 'text-white' : 'text-white/40'}`}>
          <LayoutDashboard className="w-4 h-4" /> Dashboard
        </button>
        <button onClick={() => setActiveTab('kanban')} className={`flex flex-col items-center gap-1 text-[9px] ${activeTab === 'kanban' ? 'text-white' : 'text-white/40'}`}>
          <KanbanIcon className="w-4 h-4" /> Kanban
        </button>
        <button onClick={() => setActiveTab('terminal')} className={`flex flex-col items-center gap-1 text-[9px] ${activeTab === 'terminal' ? 'text-white' : 'text-white/40'}`}>
          <Terminal className="w-4 h-4" /> Terminal
        </button>
        <button onClick={() => setActiveTab('crm')} className={`flex flex-col items-center gap-1 text-[9px] ${activeTab === 'crm' ? 'text-white' : 'text-white/40'}`}>
          <Briefcase className="w-4 h-4" /> CRM
        </button>
      </div>

      {/* AGENT FILES MODAL */}
      <AnimatePresence>
        {selectedAgent && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] flex items-end md:items-center justify-center md:p-6"
            onClick={closeAgentFiles}
          >
            {/* Backdrop */}
            <div className="absolute inset-0 bg-black/70 backdrop-blur-md" />

            {/* Modal - fullscreen on mobile, centered on desktop */}
            <motion.div
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 40 }}
              transition={{ type: 'spring', damping: 28, stiffness: 320 }}
              className="relative w-full h-full md:h-[85vh] md:max-w-4xl bg-[#0a0a0a] border-t md:border border-white/[0.08] md:rounded-3xl flex flex-col overflow-hidden shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Modal Header */}
              <div className="h-14 md:h-16 border-b border-white/[0.06] px-3 md:px-6 flex items-center justify-between bg-white/[0.02] shrink-0">
                <div className="flex items-center gap-2 md:gap-3 min-w-0">
                  <button onClick={closeAgentFiles} className="p-2 hover:bg-white/[0.06] rounded-xl transition-all text-white/40 hover:text-white shrink-0">
                    <ChevronLeft className="w-5 h-5" />
                  </button>
                  <div className="w-8 h-8 md:w-9 md:h-9 rounded-xl bg-white/[0.04] flex items-center justify-center border border-white/[0.08] shrink-0">
                    {getIcon(selectedAgent.icon, selectedAgent.color)}
                  </div>
                  <div className="min-w-0">
                    <h2 className="text-[13px] md:text-sm font-semibold text-white/90 truncate">{selectedAgent.name}</h2>
                    <p className="text-[8px] md:text-[9px] text-white/30 uppercase tracking-widest truncate">{selectedAgent.role}</p>
                  </div>
                </div>
                <div className="flex items-center gap-1.5 md:gap-2 shrink-0">
                  <button
                    onClick={saveFile}
                    disabled={fileSaving || !activeFile}
                    className="flex items-center gap-1.5 md:gap-2 px-3 md:px-4 py-2 rounded-full bg-white/90 text-black text-[10px] md:text-[11px] font-semibold tracking-wide hover:bg-white transition-all active:scale-95 shadow-lg shadow-white/10 disabled:opacity-40"
                  >
                    <Save className="w-3 h-3 md:w-3.5 md:h-3.5" /> {fileSaving ? 'Salvando...' : 'Salvar'}
                  </button>
                  <button onClick={closeAgentFiles} className="p-2 hover:bg-white/[0.06] rounded-xl transition-all text-white/40 hover:text-white">
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Mobile: horizontal file tabs */}
              <div className="md:hidden border-b border-white/[0.06] bg-white/[0.01] shrink-0">
                {fileLoading ? (
                  <div className="flex items-center gap-2 px-4 py-3 text-white/30 text-xs">
                    <RefreshCw className="w-3 h-3 animate-spin" /> Carregando...
                  </div>
                ) : (
                  <div className="flex gap-1.5 px-3 py-2.5 overflow-x-auto custom-scrollbar">
                    {Object.keys(agentFiles).map(filename => (
                      <button
                        key={filename}
                        onClick={() => selectFile(filename)}
                        className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-[10px] font-semibold whitespace-nowrap transition-all shrink-0 ${activeFile === filename ? 'bg-neon-purple/20 text-neon-purple border border-neon-purple/20' : 'text-white/40 bg-white/[0.03] border border-white/[0.06] hover:text-white/70'}`}
                      >
                        <FileText className="w-3 h-3" />
                        {filename}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Content: sidebar on desktop, editor only on mobile */}
              <div className="flex-1 flex min-h-0">
                {/* Desktop File Sidebar */}
                <div className="hidden md:flex w-52 border-r border-white/[0.06] bg-white/[0.01] flex-col overflow-y-auto shrink-0 custom-scrollbar">
                  <div className="p-3">
                    <p className="text-[9px] uppercase tracking-widest text-white/25 font-semibold mb-3 px-1">Arquivos</p>
                    {fileLoading ? (
                      <div className="flex items-center gap-2 px-3 py-2 text-white/30 text-xs">
                        <RefreshCw className="w-3 h-3 animate-spin" /> Carregando...
                      </div>
                    ) : Object.keys(agentFiles).length === 0 ? (
                      <p className="text-[10px] text-white/20 px-3 py-2">Nenhum arquivo encontrado</p>
                    ) : (
                      <div className="space-y-1">
                        {Object.keys(agentFiles).map(filename => (
                          <button
                            key={filename}
                            onClick={() => selectFile(filename)}
                            className={`w-full flex items-center gap-2 px-3 py-2.5 rounded-xl text-left text-[11px] font-medium transition-all ${activeFile === filename ? 'bg-neon-purple/20 text-neon-purple border border-neon-purple/20' : 'text-white/50 hover:bg-white/[0.04] hover:text-white/80'}`}
                          >
                            <FileText className="w-3.5 h-3.5 shrink-0" />
                            <span className="truncate">{filename}</span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Editor Area */}
                <div className="flex-1 flex flex-col min-h-0 min-w-0">
                  {activeFile ? (
                    <>
                      {/* File Header */}
                      <div className="h-9 md:h-10 border-b border-white/[0.06] px-3 md:px-4 flex items-center justify-between bg-white/[0.01] shrink-0">
                        <div className="flex items-center gap-2 min-w-0">
                          <Edit3 className="w-3 h-3 md:w-3.5 md:h-3.5 text-neon-purple/60 shrink-0" />
                          <span className="text-[10px] md:text-[11px] font-mono text-white/50 truncate">{activeFile}</span>
                        </div>
                        <span className="text-[8px] md:text-[9px] text-white/20 font-mono shrink-0 ml-2">{fileContent.length} chars</span>
                      </div>
                      {/* Textarea Editor */}
                      <textarea
                        value={fileContent}
                        onChange={(e) => setFileContent(e.target.value)}
                        className="flex-1 w-full bg-transparent text-white/80 text-[12px] md:text-[13px] leading-relaxed font-mono p-3 md:p-6 resize-none outline-none custom-scrollbar placeholder:text-white/15"
                        placeholder="Arquivo vazio..."
                        spellCheck={false}
                      />
                    </>
                  ) : (
                    <div className="flex-1 flex items-center justify-center text-white/20 text-xs md:text-sm px-4 text-center">
                      {fileLoading ? 'Carregando arquivos...' : 'Selecione um arquivo para editar'}
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <style dangerouslySetInnerHTML={{ __html: `
        .text-neon-purple { color: #b47eff; }
        .text-neon-blue { color: #00d4ff; }
        .bg-neon-purple { background-color: #b47eff; }
        .from-neon-purple { --tw-gradient-from: #b47eff; }
        .to-neon-blue { --tw-gradient-to: #00d4ff; }
        .custom-scrollbar::-webkit-scrollbar { height: 4px; width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.06); border-radius: 10px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.1); }
        .styled-scrollbar::-webkit-scrollbar { width: 6px; height: 6px; }
        .styled-scrollbar::-webkit-scrollbar-track { background: rgba(255,255,255,0.02); border-radius: 10px; }
        .styled-scrollbar::-webkit-scrollbar-thumb { background: rgba(180,126,255,0.15); border-radius: 10px; }
        .styled-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(180,126,255,0.3); }
        .styled-scrollbar { scrollbar-width: thin; scrollbar-color: rgba(180,126,255,0.15) transparent; }
        select { appearance: none; cursor: pointer; }
        input[type="time"]::-webkit-calendar-picker-indicator { filter: invert(1); opacity: 0.3; }

        /* iOS safe area */
        @supports (padding: max(0px)) {
          .min-h-screen { min-height: max(100vh, 100dvh); }
        }

        /* Smooth scroll on iOS */
        .custom-scrollbar { -webkit-overflow-scrolling: touch; }

        /* Glass morphism enhancement */
        @supports (backdrop-filter: blur(20px)) {
          .backdrop-blur-xl { backdrop-filter: blur(24px) saturate(180%); }
          .backdrop-blur-2xl { backdrop-filter: blur(40px) saturate(200%); }
        }
      `}} />
    </div>
  )
}

function CrmView({ leads = {} }) {
  const [dateFilter, setDateFilter] = useState('all') // 'all', 'today', 'week', 'month'

  const leadList = Object.entries(leads).map(([jid, data]) => ({
    jid,
    ...data
  }))
  .filter(lead => {
    if (dateFilter === 'all') return true
    if (!lead.last_inbound_at) return false
    const date = new Date(lead.last_inbound_at)
    const now = new Date()
    const diffTime = Math.abs(now - date)
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    
    if (dateFilter === 'today') return diffDays <= 1
    if (dateFilter === 'week') return diffDays <= 7
    if (dateFilter === 'month') return diffDays <= 30
    return true
  })
  .sort((a, b) => (b.last_inbound_at || 0) - (a.last_inbound_at || 0))

  const calculateQuality = (lead) => {
    let score = 0
    if (lead.lead?.name) score += 20
    if (lead.lead?.business) score += 20
    if (lead.lead?.site_type) score += 20
    if (lead.lead?.budget) score += 20
    if (lead.lead?.stage && lead.lead.stage !== 'novo') score += 20
    return score
  }

  const stats = {
    total: leadList.length,
    converted: leadList.filter(l => l.lead?.stage === 'fechamento' || l.lead?.stage === 'pagamento').length,
    highQuality: leadList.filter(l => calculateQuality(l) >= 60).length
  }

  const conversionRate = stats.total > 0 ? Math.round((stats.converted / stats.total) * 100) : 0

  // Chart Data Preparation
  const lineMap = {}
  Object.values(leads).forEach(l => {
    if (!l.last_inbound_at) return
    const d = new Date(l.last_inbound_at).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
    lineMap[d] = (lineMap[d] || 0) + 1
  })
  const lineData = Object.entries(lineMap)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => {
      const [da, ma] = a.name.split('/')
      const [db, mb] = b.name.split('/')
      return new Date(2026, parseInt(ma)-1, parseInt(da)) - new Date(2026, parseInt(mb)-1, parseInt(db))
    })
    .slice(-7)

  const stageMap = {}
  leadList.forEach(l => {
    const s = l.lead?.stage || 'novo'
    stageMap[s] = (stageMap[s] || 0) + 1
  })
  const pieData = Object.entries(stageMap).map(([name, value]) => ({ name: name.toUpperCase(), value }))

  const qualityMap = { '0-20': 0, '21-40': 0, '41-60': 0, '61-80': 0, '81-100': 0 }
  leadList.forEach(l => {
    const q = calculateQuality(l)
    if (q <= 20) qualityMap['0-20']++
    else if (q <= 40) qualityMap['21-40']++
    else if (q <= 60) qualityMap['41-60']++
    else if (q <= 80) qualityMap['61-80']++
    else qualityMap['81-100']++
  })
  const barData = Object.entries(qualityMap).map(([name, count]) => ({ name, count }))

  const COLORS = ['#b47eff', '#00d4ff', '#34d399', '#fb7185', '#facc15', '#a855f7']

  const openWhatsApp = (jid) => {
    const number = jid.split('@')[0]
    window.open(`https://wa.me/${number}`, '_blank')
  }

  return (
    <section className="flex-1 flex flex-col gap-6 min-h-0 overflow-hidden pb-4">
      {/* CRM Stats & Filters */}
      <div className="flex flex-col lg:flex-row gap-6 shrink-0">
        <div className="flex-1 grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-5 rounded-3xl bg-white/[0.03] border border-white/[0.08] backdrop-blur-xl">
            <p className="text-[9px] uppercase tracking-widest text-white/30 mb-1">Total de Leads</p>
            <p className="text-2xl font-bold text-white">{stats.total}</p>
          </div>
          <div className="p-5 rounded-3xl bg-white/[0.03] border border-white/[0.08] backdrop-blur-xl">
            <p className="text-[9px] uppercase tracking-widest text-white/30 mb-1">Alta Qualidade</p>
            <p className="text-2xl font-bold text-neon-purple">{stats.highQuality}</p>
          </div>
          <div className="p-5 rounded-3xl bg-white/[0.03] border border-white/[0.08] backdrop-blur-xl">
            <p className="text-[9px] uppercase tracking-widest text-white/30 mb-1">Conversões</p>
            <p className="text-2xl font-bold text-emerald-400">{stats.converted}</p>
          </div>
          <div className="p-5 rounded-3xl bg-white/[0.03] border border-white/[0.08] backdrop-blur-xl">
            <p className="text-[9px] uppercase tracking-widest text-white/30 mb-1">Taxa de Conversão</p>
            <p className="text-2xl font-bold text-neon-blue">{conversionRate}%</p>
          </div>
        </div>

        {/* Date Filter Panel */}
        <div className="lg:w-48 p-4 rounded-3xl bg-white/[0.03] border border-white/[0.08] backdrop-blur-xl flex flex-col justify-center gap-2">
          <div className="flex items-center gap-2 px-1 mb-1">
            <Calendar className="w-3 h-3 text-white/30" />
            <span className="text-[9px] uppercase tracking-widest text-white/30 font-bold">Filtrar por Data</span>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {[
              { id: 'all', label: 'Tudo' },
              { id: 'today', label: 'Hoje' },
              { id: 'week', label: 'Semana' },
              { id: 'month', label: 'Mês' }
            ].map(f => (
              <button
                key={f.id}
                onClick={() => setDateFilter(f.id)}
                className={`px-3 py-2 rounded-xl text-[10px] font-semibold transition-all ${dateFilter === f.id ? 'bg-neon-purple text-white shadow-lg shadow-neon-purple/20' : 'bg-white/[0.04] text-white/40 hover:bg-white/[0.08] hover:text-white/60'}`}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 shrink-0">
        {/* Line Chart: Leads per Day */}
        <div className="h-[280px] p-5 rounded-3xl bg-white/[0.03] border border-white/[0.08] backdrop-blur-xl flex flex-col">
          <h3 className="text-[10px] font-semibold uppercase tracking-widest text-white/30 mb-4 flex items-center gap-2">
            <Activity className="w-3 h-3" /> Volume de Leads (7 dias)
          </h3>
          <div className="flex-1 min-h-0">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={lineData}>
                <defs>
                  <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00d4ff" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#00d4ff" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="name" stroke="rgba(255,255,255,0.2)" fontSize={10} tickLine={false} axisLine={false} />
                <YAxis stroke="rgba(255,255,255,0.2)" fontSize={10} tickLine={false} axisLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0a0a0a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', fontSize: '10px' }}
                  itemStyle={{ color: '#00d4ff' }}
                />
                <Area type="monotone" dataKey="count" stroke="#00d4ff" strokeWidth={2} fillOpacity={1} fill="url(#colorCount)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Pie Chart: Stage Distribution */}
        <div className="h-[280px] p-5 rounded-3xl bg-white/[0.03] border border-white/[0.08] backdrop-blur-xl flex flex-col">
          <h3 className="text-[10px] font-semibold uppercase tracking-widest text-white/30 mb-4 flex items-center gap-2">
            <Layout className="w-3 h-3" /> Distribuição por Estágio
          </h3>
          <div className="flex-1 min-h-0 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} stroke="rgba(0,0,0,0.2)" />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0a0a0a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', fontSize: '10px' }}
                />
                <Legend iconType="circle" wrapperStyle={{ fontSize: '9px', paddingTop: '10px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Bar Chart: Quality Distribution */}
        <div className="h-[280px] p-5 rounded-3xl bg-white/[0.03] border border-white/[0.08] backdrop-blur-xl flex flex-col">
          <h3 className="text-[10px] font-semibold uppercase tracking-widest text-white/30 mb-4 flex items-center gap-2">
            <Zap className="w-3 h-3" /> Distribuição de Qualidade
          </h3>
          <div className="flex-1 min-h-0">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis dataKey="name" stroke="rgba(255,255,255,0.2)" fontSize={10} tickLine={false} axisLine={false} />
                <YAxis stroke="rgba(255,255,255,0.2)" fontSize={10} tickLine={false} axisLine={false} />
                <Tooltip 
                  cursor={{fill: 'rgba(255,255,255,0.05)'}}
                  contentStyle={{ backgroundColor: '#0a0a0a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', fontSize: '10px' }}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {barData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.name === '81-100' ? '#34d399' : entry.name === '61-80' ? '#b47eff' : '#6b7280'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Leads Table */}
      <div className="flex-1 min-h-0 bg-white/[0.02] border border-white/[0.06] rounded-3xl flex flex-col overflow-hidden backdrop-blur-xl">
        <div className="h-12 border-b border-white/[0.06] px-6 flex items-center justify-between bg-white/[0.02] shrink-0">
          <div className="text-[10px] font-semibold uppercase tracking-[0.15em] text-white/30">Pipeline de Vendas WhatsApp</div>
          <div className="text-[9px] text-white/20 font-mono">{stats.total} contatos</div>
        </div>
        <div className="flex-1 overflow-y-auto custom-scrollbar">
          <table className="w-full text-left border-collapse">
            <thead className="sticky top-0 bg-[#0a0a0a] z-10">
              <tr className="border-b border-white/[0.04]">
                <th className="px-6 py-4 text-[10px] uppercase tracking-widest text-white/20 font-semibold">Nome / Contato</th>
                <th className="px-6 py-4 text-[10px] uppercase tracking-widest text-white/20 font-semibold">Negócio</th>
                <th className="px-6 py-4 text-[10px] uppercase tracking-widest text-white/20 font-semibold">Qualidade</th>
                <th className="px-6 py-4 text-[10px] uppercase tracking-widest text-white/20 font-semibold">Estágio</th>
                <th className="px-6 py-4 text-[10px] uppercase tracking-widest text-white/20 font-semibold text-right">Ações</th>
              </tr>
            </thead>
            <tbody>
              {leadList.map(lead => {
                const quality = calculateQuality(lead)
                const lastSeen = lead.last_inbound_at ? new Date(lead.last_inbound_at).toLocaleDateString() : '—'
                return (
                  <tr key={lead.jid} className="border-b border-white/[0.02] hover:bg-white/[0.02] transition-colors group">
                    <td className="px-6 py-4">
                      <div className="flex flex-col">
                        <span className="text-sm font-semibold text-white/90 group-hover:text-neon-purple transition-colors">{lead.lead?.name || lead.jid.split('@')[0]}</span>
                        <span className="text-[10px] text-white/20 font-mono">{lead.jid}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-xs text-white/60">{lead.lead?.business || '—'}</span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="flex-1 h-1.5 w-24 bg-white/[0.04] rounded-full overflow-hidden">
                          <div 
                            className="h-full rounded-full transition-all duration-1000"
                            style={{ 
                              width: `${quality}%`,
                              background: quality >= 80 ? '#34d399' : quality >= 40 ? '#b47eff' : '#6b7280'
                            }}
                          />
                        </div>
                        <span className="text-[10px] font-mono text-white/30">{quality}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2.5 py-1 rounded-full text-[9px] font-bold uppercase tracking-wider border ${
                        lead.lead?.stage === 'fechamento' ? 'bg-emerald-400/10 border-emerald-400/20 text-emerald-400' :
                        lead.lead?.stage === 'preco' ? 'bg-neon-purple/10 border-neon-purple/20 text-neon-purple' :
                        'bg-white/5 border-white/10 text-white/40'
                      }`}>
                        {lead.lead?.stage || 'novo'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-3">
                        <div className="flex flex-col items-end">
                           <span className="text-[9px] text-white/20 font-mono uppercase">Visto em</span>
                           <span className="text-[10px] text-white/40 font-mono">{lastSeen}</span>
                        </div>
                        <button 
                          onClick={() => openWhatsApp(lead.jid)}
                          className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 hover:bg-emerald-500 hover:text-white transition-all active:scale-95"
                          title="Abrir no WhatsApp"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          {leadList.length === 0 && (
            <div className="py-20 flex flex-col items-center justify-center text-white/20">
              <Search className="w-10 h-10 mb-4 opacity-10" />
              <p className="text-sm font-medium">Nenhum lead encontrado para este filtro</p>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}

function KanbanColumn({ title, status, tasks = [], moveTask, editTask, deleteTask, onCreateTask, agents = [] }) {
  const [showForm, setShowForm] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [newDesc, setNewDesc] = useState('')
  const [newAgent, setNewAgent] = useState('jarvis')

  const columnTasks = (tasks || []).filter(t => t.status === status)
  const accentColor = status === 'in_progress' ? '#00d4ff' : status === 'done' ? '#34d399' : 'rgba(255,255,255,0.3)'

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!newTitle.trim()) return
    onCreateTask(newTitle, newDesc, newAgent)
    setNewTitle('')
    setNewDesc('')
    setNewAgent('jarvis')
    setShowForm(false)
  }

  const timeAgo = (ts) => {
    if (!ts) return null
    const mins = Math.floor((Date.now() - ts) / 60000)
    if (mins < 1) return 'agora'
    if (mins < 60) return `${mins}min`
    const hrs = Math.floor(mins / 60)
    if (hrs < 24) return `${hrs}h`
    return `${Math.floor(hrs / 24)}d`
  }

  return (
    <div className="flex-1 min-w-0 lg:min-w-[320px] bg-white/[0.02] border border-white/[0.06] rounded-2xl md:rounded-3xl flex flex-col backdrop-blur-xl overflow-hidden">
      {/* Column Header */}
      <div className="shrink-0 p-4 md:p-5 pb-3 md:pb-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2.5">
            <span className="w-2.5 h-2.5 rounded-full" style={{ background: accentColor }}></span>
            <h3 className="text-[11px] md:text-xs font-bold uppercase tracking-[0.12em] text-white/50">{title}</h3>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-white/30 font-mono bg-white/[0.04] px-2.5 py-1 rounded-full border border-white/[0.06]">{columnTasks.length}</span>
            {onCreateTask && (
              <button
                onClick={() => setShowForm(!showForm)}
                className={`p-1.5 rounded-lg transition-all active:scale-90 border ${showForm ? 'bg-white/10 border-white/[0.12] text-white' : 'hover:bg-white/[0.06] border-white/[0.06] text-white/40 hover:text-white'}`}
              >
                <Plus className={`w-4 h-4 transition-transform duration-200 ${showForm ? 'rotate-45' : ''}`} />
              </button>
            )}
          </div>
        </div>
        <div className="h-[2px] rounded-full" style={{ background: `linear-gradient(to right, ${accentColor}, transparent)`, opacity: 0.3 }}></div>
      </div>

      {/* Inline Add Form */}
      <AnimatePresence>
        {showForm && onCreateTask && (
          <motion.form
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="shrink-0 overflow-hidden"
            onSubmit={handleSubmit}
          >
            <div className="px-4 md:px-5 pb-4 space-y-2">
              <input
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder="Título da tarefa..."
                className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-3 py-2.5 text-xs text-white placeholder:text-white/20 outline-none focus:border-white/[0.15] transition-colors"
                autoFocus
              />
              <textarea
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                placeholder="Descrição (opcional)..."
                rows={2}
                className="w-full bg-white/[0.04] border border-white/[0.08] rounded-xl px-3 py-2 text-[11px] text-white/70 placeholder:text-white/15 outline-none focus:border-white/[0.15] transition-colors resize-none"
              />
              <div className="flex items-center gap-2">
                <select
                  value={newAgent}
                  onChange={(e) => setNewAgent(e.target.value)}
                  className="flex-1 bg-white/[0.04] border border-white/[0.08] rounded-xl px-3 py-2 text-[10px] text-white/50 outline-none"
                >
                  {agents.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
                  {agents.length === 0 && <option value="jarvis">Jarvis</option>}
                </select>
                <button
                  type="submit"
                  disabled={!newTitle.trim()}
                  className="px-4 py-2 rounded-xl bg-white/90 text-black text-[10px] font-bold tracking-wide hover:bg-white transition-all active:scale-95 disabled:opacity-30"
                >
                  Criar
                </button>
              </div>
            </div>
          </motion.form>
        )}
      </AnimatePresence>

      {/* Task Cards */}
      <div className="flex-1 min-h-0 overflow-y-auto custom-scrollbar px-4 md:px-5 pb-4 md:pb-5 space-y-3">
        {columnTasks.length === 0 && !showForm && (
          <div className="flex flex-col items-center justify-center py-10 text-center">
            <div className="w-10 h-10 rounded-2xl bg-white/[0.03] border border-white/[0.06] flex items-center justify-center mb-3">
              {status === 'todo' && <Circle className="w-4 h-4 text-white/15" />}
              {status === 'in_progress' && <Activity className="w-4 h-4 text-white/15" />}
              {status === 'done' && <CheckCircle2 className="w-4 h-4 text-white/15" />}
            </div>
            <p className="text-[10px] text-white/20 font-medium">Nenhuma tarefa aqui</p>
            {onCreateTask && <p className="text-[9px] text-white/10 mt-1">Clique no + para adicionar</p>}
          </div>
        )}
        {columnTasks.map(task => (
          <motion.div
            layout
            key={task.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="group relative bg-white/[0.02] border border-white/[0.08] rounded-xl md:rounded-2xl overflow-hidden shadow-lg hover:border-white/[0.15] hover:bg-white/[0.04] transition-all duration-200 active:scale-[0.98]"
          >
            {/* Left accent bar */}
            <div className="absolute left-0 top-0 bottom-0 w-[3px] rounded-l-xl" style={{ background: accentColor, opacity: 0.5 }}></div>

            <div className="p-4 md:p-5 pl-5 md:pl-6">
              {/* Title + Actions */}
              <div className="flex justify-between items-start gap-2 mb-1.5">
                <h4 className="text-xs md:text-[13px] font-semibold text-white/85 leading-snug flex-1">{task.title}</h4>
                <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                  {editTask && (
                    <button onClick={() => editTask(task.id)} className="p-1.5 hover:bg-white/[0.08] rounded-lg transition-all" title="Editar">
                      <Edit3 className="w-3 h-3 text-white/30 hover:text-white" />
                    </button>
                  )}
                  {deleteTask && (
                    <button onClick={() => deleteTask(task.id)} className="p-1.5 hover:bg-red-500/10 rounded-lg transition-all" title="Excluir">
                      <X className="w-3 h-3 text-red-400/40 hover:text-red-400" />
                    </button>
                  )}
                </div>
              </div>

              {/* Description */}
              {task.description && (
                <p className="text-[10px] md:text-[11px] text-white/30 leading-relaxed mb-3 font-medium" style={{ display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                  {task.description}
                </p>
              )}

              {/* Footer */}
              <div className="flex items-center justify-between pt-3 border-t border-white/[0.05]">
                <div className="flex items-center gap-2">
                  <div className="w-5 h-5 md:w-6 md:h-6 rounded-lg flex items-center justify-center text-[8px] md:text-[9px] font-bold text-white/40 uppercase border border-white/[0.06]" style={{ background: 'linear-gradient(135deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02))' }}>
                    {task.agent?.[0] || '?'}
                  </div>
                  <span className="text-[9px] md:text-[10px] text-white/25 uppercase tracking-[0.1em] font-semibold">{task.agent}</span>
                  {task.updated_at && (
                    <span className="text-[8px] text-white/15 font-mono">{timeAgo(task.updated_at)}</span>
                  )}
                </div>
                <div className="flex items-center gap-0.5">
                  {status !== 'todo' && (
                    <button onClick={() => moveTask(task.id, 'todo')} className="p-1 hover:bg-white/[0.06] rounded-md transition-all" title="A Fazer">
                      <Circle className="w-3 h-3 text-white/15 hover:text-white/50" />
                    </button>
                  )}
                  {status !== 'in_progress' && (
                    <button onClick={() => moveTask(task.id, 'in_progress')} className="p-1 hover:bg-white/[0.06] rounded-md transition-all" title="Em Andamento">
                      <Activity className="w-3 h-3 text-white/15 hover:text-white/50" />
                    </button>
                  )}
                  {status !== 'done' && (
                    <button onClick={() => moveTask(task.id, 'done')} className="p-1 hover:bg-white/[0.06] rounded-md transition-all" title="Finalizar">
                      <CheckCircle2 className="w-3 h-3 text-white/15 hover:text-emerald-400/70" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
