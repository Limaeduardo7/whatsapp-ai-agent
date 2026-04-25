from __future__ import annotations


def render_marketing_dashboard() -> str:
    return r"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Syncronix · Marketing Ops</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet" />
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: "class",
      theme: {
        extend: {
          fontFamily: { sans: ["Inter", "system-ui", "sans-serif"] },
          colors: {
            brand: {
              50: "#f0fdf4", 100: "#dcfce7", 200: "#bbf7d0",
              400: "#4ade80", 500: "#22c55e", 600: "#25D366",
              700: "#15803d", 800: "#166534", 900: "#14532d",
              950: "#052e16"
            }
          },
          boxShadow: {
            glow: "0 0 24px rgba(37,211,102,0.18)",
            "glow-sm": "0 0 12px rgba(37,211,102,0.12)",
            card: "0 1px 3px rgba(0,0,0,0.05), 0 4px 20px rgba(0,0,0,0.04)"
          }
        }
      }
    };
  </script>
  <style>
    *, *::before, *::after { font-family: "Inter", system-ui, sans-serif; box-sizing: border-box; }

    /* ── Aurora gradient ── */
    @keyframes aurora { 0%,100%{background-position:0% 50%} 50%{background-position:100% 50%} }
    .aurora {
      background: linear-gradient(135deg,#128C7E,#25D366,#0ea5e9,#7c3aed,#25D366);
      background-size: 300% 300%;
      animation: aurora 8s ease infinite;
    }

    /* ── Dot grid ── */
    .dot-grid {
      background-image: radial-gradient(circle, rgba(37,211,102,0.15) 1px, transparent 1px);
      background-size: 22px 22px;
    }

    /* ── Shimmer skeleton ── */
    @keyframes shimmer { 0%{background-position:-200% 0} 100%{background-position:200% 0} }
    .shimmer-bg {
      background: linear-gradient(90deg,rgba(0,0,0,0.04) 25%,rgba(0,0,0,0.08) 50%,rgba(0,0,0,0.04) 75%);
      background-size: 200% 100%;
      animation: shimmer 1.6s infinite;
    }
    .dark .shimmer-bg {
      background: linear-gradient(90deg,rgba(255,255,255,0.03) 25%,rgba(255,255,255,0.07) 50%,rgba(255,255,255,0.03) 75%);
      background-size: 200% 100%;
    }

    /* ── Glow card hover ── */
    .glow-card { transition: box-shadow 0.25s ease, transform 0.2s ease; }
    .glow-card:hover { box-shadow: 0 0 0 1px rgba(37,211,102,0.25), 0 8px 32px rgba(37,211,102,0.14); transform: translateY(-1px); }

    /* ── Gradient text ── */
    .grad-text {
      background: linear-gradient(135deg,#25D366,#0ea5e9);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    }

    /* ── Gradient border ── */
    .grad-border {
      background: linear-gradient(white,white) padding-box,
                  linear-gradient(135deg,#25D366,#0ea5e9) border-box;
      border: 1.5px solid transparent;
    }
    .dark .grad-border {
      background: linear-gradient(#18181b,#18181b) padding-box,
                  linear-gradient(135deg,#25D366,#0ea5e9) border-box;
    }

    /* ── Page fade-in ── */
    @keyframes fadeUp { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
    .page-enter { animation: fadeUp 0.35s ease-out both; }

    /* ── Animated counter ── */
    @keyframes countUp { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }
    .count-up { animation: countUp 0.45s ease-out both; }

    /* ── Toast ── */
    @keyframes toastIn { from{transform:translateX(110%);opacity:0} to{transform:translateX(0);opacity:1} }
    @keyframes toastOut { from{transform:translateX(0);opacity:1} to{transform:translateX(110%);opacity:0} }
    .toast-in  { animation: toastIn  0.3s ease-out both; }
    .toast-out { animation: toastOut 0.25s ease-in  both; }

    /* ── Sidebar mobile slide ── */
    @keyframes sidebarIn { from{transform:translateX(-100%)} to{transform:translateX(0)} }
    .sidebar-in { animation: sidebarIn 0.25s ease-out both; }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 4px; height: 4px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #3f3f46; border-radius: 99px; }

    /* ── Table row hover ── */
    .trow { transition: background 0.12s; }

    /* ── Custom tooltip (recharts) ── */
    .ct {
      background: rgba(9,9,11,0.88);
      border: 1px solid rgba(37,211,102,0.2);
      border-radius: 10px; padding: 8px 12px;
      backdrop-filter: blur(8px);
      font-size: 12px; color: #fff;
      box-shadow: 0 4px 24px rgba(0,0,0,0.4);
    }

    /* ── Metric glow ── */
    .metric-num { text-shadow: 0 0 28px rgba(37,211,102,0.25); }

    /* ── Bottom nav blur ── */
    .bnav { backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px); }
  </style>
</head>
<body class="bg-zinc-50 text-zinc-950 antialiased dark:bg-zinc-950 dark:text-zinc-50 transition-colors duration-300">
<div id="root"></div>

<script crossorigin src="https://unpkg.com/react@18.2.0/umd/react.production.min.js"></script>
<script crossorigin src="https://unpkg.com/react-dom@18.2.0/umd/react-dom.production.min.js"></script>
<script src="https://unpkg.com/prop-types@15.8.1/prop-types.min.js"></script>
<script src="https://unpkg.com/recharts@2.12.7/umd/Recharts.js"></script>
<script src="https://unpkg.com/@babel/standalone@7.25.7/babel.min.js"></script>
<script type="text/babel" data-presets="env,react">
const { useCallback, useEffect, useMemo, useState } = React;
const {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell,
  Defs, LinearGradient, Pie, PieChart,
  ResponsiveContainer, Stop, Tooltip, XAxis, YAxis
} = Recharts;

// ─── Constants ────────────────────────────────────────────────────────────────
const API_URL = "/marketing/dashboard/data";
const ACTIONS = {
  pause:      "/marketing/automation/customers/{phone}/pause",
  reactivate: "/marketing/automation/customers/{phone}/reactivate",
  restart:    "/marketing/automation/customers/{phone}/restart",
  forceNext:  "/marketing/automation/customers/{phone}/force-next",
  optOut:     "/marketing/automation/customers/{phone}/opt-out",
};
const STATUS_COLORS = {
  active:           "#25D366",
  waiting_purchase: "#f59e0b",
  idle:             "#71717a",
  paused:           "#8b5cf6",
  opted_out:        "#ef4444",
  completed:        "#0ea5e9",
  unknown:          "#52525b",
};
const NAV = [
  { key: "overview",  label: "Overview",   icon: "⬡" },
  { key: "contacts",  label: "Contatos",   icon: "◎" },
  { key: "purchases", label: "Compras",    icon: "◈" },
  { key: "messages",  label: "Mensagens",  icon: "◫" },
  { key: "sequences", label: "Sequências", icon: "◩" },
  { key: "system",    label: "Sistema",    icon: "◬" },
];

// ─── Utilities ────────────────────────────────────────────────────────────────
function cn(...p) { return p.filter(Boolean).join(" "); }

function fmtDate(v) {
  if (!v) return "—";
  const d = new Date(v);
  if (isNaN(d)) return v;
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(d);
}
function fmtDay(v) {
  if (!v) return "Sem data";
  const d = new Date(v);
  if (isNaN(d)) return "Sem data";
  return new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "2-digit" }).format(d);
}
function fmtMoney(v) {
  if (v == null) return "Não configurada";
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v);
}
function statusTone(v) {
  if (v === "active") return "success";
  if (v === "waiting_purchase") return "warning";
  if (v === "paused") return "purple";
  if (v === "opted_out" || v === "error" || v === "failed") return "danger";
  return "muted";
}
function severityTone(v) {
  if (v === "error") return "danger";
  if (v === "warning") return "warning";
  return "muted";
}
function providerTone(v) {
  const n = String(v || "").toLowerCase();
  if (n.includes("fail") || n.includes("error") || n.includes("timeout")) return "danger";
  if (!n || n === "unknown") return "muted";
  return "success";
}
function groupCount(rows, fn) {
  const m = new Map();
  for (const r of rows) {
    const k = fn(r) || "Sem valor";
    m.set(k, (m.get(k) || 0) + 1);
  }
  return [...m.entries()].map(([name, value]) => ({ name, value }));
}
function buildDaily(purchases, messages) {
  const m = new Map();
  const add = (items, field) => {
    for (const x of items) {
      const raw = x.created_at || x.approved_at;
      const d = raw ? new Date(raw) : null;
      const key = d && !isNaN(d) ? d.toISOString().slice(0, 10) : "sem-data";
      const cur = m.get(key) || { key, day: fmtDay(raw), compras: 0, mensagens: 0 };
      cur[field] += 1;
      m.set(key, cur);
    }
  };
  add(purchases, "compras");
  add(messages, "mensagens");
  return [...m.values()].sort((a, b) => a.key.localeCompare(b.key)).slice(-14);
}

// ─── Animated Counter (React Bits pattern) ────────────────────────────────────
function AnimNum({ value, prefix = "", suffix = "" }) {
  const [n, setN] = useState(0);
  const num = typeof value === "number" ? value : 0;
  useEffect(() => {
    if (num === 0) { setN(0); return; }
    let cur = 0;
    const step = num / (700 / 16);
    const id = setInterval(() => {
      cur += step;
      if (cur >= num) { setN(num); clearInterval(id); }
      else setN(Math.floor(cur));
    }, 16);
    return () => clearInterval(id);
  }, [num]);
  if (typeof value === "string") return <span>{value}</span>;
  return <span className="count-up">{prefix}{n.toLocaleString("pt-BR")}{suffix}</span>;
}

// ─── Toast System ─────────────────────────────────────────────────────────────
function useToast() {
  const [toasts, setToasts] = useState([]);
  const add = useCallback((msg, type = "info") => {
    const id = Date.now();
    setToasts(p => [...p, { id, msg, type, out: false }]);
    setTimeout(() => {
      setToasts(p => p.map(t => t.id === id ? { ...t, out: true } : t));
      setTimeout(() => setToasts(p => p.filter(t => t.id !== id)), 280);
    }, 4000);
  }, []);
  return { toasts, add };
}
function Toasts({ toasts }) {
  const S = {
    success: "border-brand-600/30 text-brand-300",
    error:   "border-red-500/30   text-red-300",
    warning: "border-amber-500/30 text-amber-300",
    info:    "border-zinc-700     text-zinc-300",
  };
  const IC = { success: "✓", error: "✕", warning: "⚠", info: "ℹ" };
  return (
    <div className="fixed bottom-20 right-4 z-50 flex flex-col gap-2 lg:bottom-4">
      {toasts.map(t => (
        <div key={t.id} className={cn(
          "flex items-center gap-3 rounded-2xl border bg-zinc-950/90 px-4 py-3 text-sm font-medium shadow-2xl backdrop-blur-xl",
          S[t.type] || S.info, t.out ? "toast-out" : "toast-in"
        )}>
          <span className="text-base">{IC[t.type]}</span>
          <span>{t.msg}</span>
        </div>
      ))}
    </div>
  );
}

// ─── Design System ────────────────────────────────────────────────────────────
function Card({ className = "", glow = false, children }) {
  return (
    <div className={cn(
      "rounded-2xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900 transition-all duration-200",
      glow && "glow-card", className
    )}>
      {children}
    </div>
  );
}
function CardH({ children, className = "" }) {
  return <div className={cn("flex flex-col gap-1 p-5 pb-3", className)}>{children}</div>;
}
function CardT({ children, grad = false }) {
  return <h3 className={cn("text-sm font-semibold tracking-tight", grad && "grad-text")}>{children}</h3>;
}
function CardD({ children }) {
  return <p className="text-xs text-zinc-500 dark:text-zinc-400">{children}</p>;
}
function CardC({ className = "", children }) {
  return <div className={cn("p-5 pt-2", className)}>{children}</div>;
}

function Btn({ active, tone = "default", size = "md", className = "", children, ...p }) {
  const sz = { sm: "h-7 px-2.5 text-xs", md: "h-9 px-3.5 text-sm", lg: "h-10 px-4 text-sm" };
  const T = {
    default: active
      ? "bg-brand-600 text-white border-brand-600 shadow-glow-sm"
      : "border-zinc-200 bg-white text-zinc-700 hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800",
    danger: "border-red-200 bg-red-50 text-red-700 hover:bg-red-100 dark:border-red-900 dark:bg-red-950/50 dark:text-red-400",
    ghost:  "border-transparent bg-transparent text-zinc-500 hover:bg-zinc-100 hover:text-zinc-800 dark:hover:bg-zinc-800 dark:hover:text-zinc-200",
    brand:  "border-brand-600 bg-brand-600 text-white hover:bg-brand-700 shadow-glow-sm",
  };
  return (
    <button className={cn(
      "inline-flex items-center justify-center gap-1.5 rounded-xl border font-medium transition-all duration-150 active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-50",
      sz[size] || sz.md, T[tone] || T.default, className
    )} {...p}>{children}</button>
  );
}

function Badge({ tone = "muted", children }) {
  const T = {
    default: "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900",
    muted:   "bg-zinc-100 text-zinc-600 ring-1 ring-zinc-300/60 dark:bg-zinc-800 dark:text-zinc-400 dark:ring-zinc-700/60",
    success: "bg-brand-50 text-brand-700 ring-1 ring-brand-600/20 dark:bg-brand-950/30 dark:text-brand-300 dark:ring-brand-600/20",
    warning: "bg-amber-50 text-amber-700 ring-1 ring-amber-500/20 dark:bg-amber-950/30 dark:text-amber-300 dark:ring-amber-500/20",
    danger:  "bg-red-50 text-red-700 ring-1 ring-red-500/20 dark:bg-red-950/30 dark:text-red-300 dark:ring-red-500/20",
    purple:  "bg-purple-50 text-purple-700 ring-1 ring-purple-500/20 dark:bg-purple-950/30 dark:text-purple-300 dark:ring-purple-500/20",
    info:    "bg-sky-50 text-sky-700 ring-1 ring-sky-500/20 dark:bg-sky-950/30 dark:text-sky-300 dark:ring-sky-500/20",
  };
  return <span className={cn("inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-semibold leading-4", T[tone] || T.muted)}>{children}</span>;
}

function Input({ className = "", ...p }) {
  return (
    <input className={cn(
      "h-9 w-full rounded-xl border border-zinc-200 bg-white px-3 text-sm text-zinc-900 placeholder:text-zinc-400",
      "outline-none transition-all focus:border-brand-600/40 focus:ring-2 focus:ring-brand-600/15",
      "dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-100 dark:placeholder:text-zinc-600 dark:focus:border-brand-600/40 dark:focus:ring-brand-600/15",
      className
    )} {...p} />
  );
}

function Select({ className = "", ...p }) {
  return (
    <select className={cn(
      "h-9 rounded-xl border border-zinc-200 bg-white px-3 text-sm text-zinc-900 outline-none cursor-pointer",
      "transition-all focus:border-brand-600/40 focus:ring-2 focus:ring-brand-600/15",
      "dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-100",
      className
    )} {...p} />
  );
}

function Empty({ title, desc }) {
  return (
    <div className="flex min-h-[180px] flex-col items-center justify-center rounded-xl border border-dashed border-zinc-200 dark:border-zinc-800 p-8 text-center">
      <div className="mb-2 text-3xl opacity-20">◎</div>
      <div className="text-sm font-medium text-zinc-700 dark:text-zinc-300">{title}</div>
      {desc && <div className="mt-1 max-w-xs text-xs text-zinc-400">{desc}</div>}
    </div>
  );
}

function Skeleton({ rows = 6 }) {
  return (
    <div className="space-y-2.5">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="relative h-10 overflow-hidden rounded-xl bg-zinc-100 dark:bg-zinc-800" style={{ width: `${80 + (i % 3) * 7}%` }}>
          <div className="shimmer-bg absolute inset-0" />
        </div>
      ))}
    </div>
  );
}

// ─── Chart Tooltip (React Bits dark tooltip) ──────────────────────────────────
function CTip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="ct">
      {label && <div className="mb-1.5 text-[11px] text-zinc-400">{label}</div>}
      {payload.map((p, i) => (
        <div key={i} className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full flex-shrink-0" style={{ background: p.color }} />
          <span className="text-zinc-400 text-[11px]">{p.name}:</span>
          <span className="font-semibold">{typeof p.value === "number" ? p.value.toLocaleString("pt-BR") : p.value}</span>
        </div>
      ))}
    </div>
  );
}

// ─── DataTable ────────────────────────────────────────────────────────────────
function Table({ columns, rows, empty, emptyDesc, onRow, selKey }) {
  if (!rows.length) return <Empty title={empty} desc={emptyDesc} />;
  return (
    <div className="overflow-hidden rounded-xl border border-zinc-200 dark:border-zinc-800">
      <div className="max-h-[520px] overflow-auto">
        <table className="w-full border-collapse text-sm">
          <thead className="sticky top-0 z-10">
            <tr className="bg-zinc-50/95 dark:bg-zinc-900/95 backdrop-blur-sm">
              {columns.map(c => (
                <th key={c.key} className="border-b border-zinc-200 dark:border-zinc-800 px-3 py-2.5 text-left text-[10px] font-bold uppercase tracking-widest text-zinc-400 dark:text-zinc-500">
                  {c.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => {
              const key = row.id || row.purchase_id || `${row.phone}-${i}`;
              const sel = selKey && selKey === row.phone;
              return (
                <tr key={key} onClick={() => onRow && onRow(row)}
                  className={cn(
                    "trow border-b border-zinc-100 last:border-0 dark:border-zinc-800/60",
                    "hover:bg-zinc-50 dark:hover:bg-zinc-800/40",
                    onRow && "cursor-pointer",
                    sel && "bg-brand-50/60 dark:bg-brand-950/20 border-l-2 border-l-brand-600"
                  )}
                >
                  {columns.map(c => (
                    <td key={c.key} className="max-w-[300px] px-3 py-2.5 align-middle text-xs text-zinc-700 dark:text-zinc-300">
                      {c.render ? c.render(row) : row[c.key] ?? "—"}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="flex items-center border-t border-zinc-200 dark:border-zinc-800 bg-zinc-50/60 dark:bg-zinc-900/50 px-4 py-1.5">
        <span className="text-[11px] text-zinc-400">{rows.length.toLocaleString("pt-BR")} registros</span>
      </div>
    </div>
  );
}

// ─── Metric Card (React Bits: glow + dot grid + aurora accent + counter) ──────
function Metric({ label, value, detail, tone = "default", icon }) {
  const num = {
    default: "text-zinc-900 dark:text-zinc-50",
    success: "grad-text metric-num",
    warning: "text-amber-600 dark:text-amber-400",
    danger:  "text-red-600 dark:text-red-400",
    info:    "text-sky-600 dark:text-sky-400",
    purple:  "text-purple-600 dark:text-purple-400",
  }[tone] || "text-zinc-900 dark:text-zinc-50";
  return (
    <Card glow className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 dot-grid opacity-50 dark:opacity-20" />
      <CardC className="pt-5 relative z-10">
        <div className="flex items-start justify-between mb-2.5">
          <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 dark:text-zinc-500">{label}</p>
          {icon && <span className="text-xl opacity-25">{icon}</span>}
        </div>
        <div className={cn("text-3xl font-extrabold tracking-tight leading-none", num)}>
          <AnimNum value={value} />
        </div>
        {detail && <div className="mt-2 text-[11px] text-zinc-400 dark:text-zinc-500">{detail}</div>}
        {tone === "success" && <div className="absolute bottom-0 left-0 right-0 h-0.5 aurora opacity-70" />}
      </CardC>
    </Card>
  );
}

// ─── Page Header ──────────────────────────────────────────────────────────────
function PH({ title, desc, children }) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h2 className="text-xl font-extrabold tracking-tight text-zinc-900 dark:text-zinc-50">{title}</h2>
        {desc && <p className="mt-0.5 text-sm text-zinc-500 dark:text-zinc-400">{desc}</p>}
      </div>
      {children}
    </div>
  );
}

// ─── Controls Bar ─────────────────────────────────────────────────────────────
function Controls({ query, setQuery, statusFilter, setStatusFilter, customers, showStatus, onRefresh, refreshing }) {
  return (
    <div className={cn("grid gap-2.5", showStatus ? "sm:grid-cols-[1fr_160px_auto]" : "sm:grid-cols-[1fr_auto]")}>
      <div className="relative">
        <svg className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-zinc-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <Input value={query} onChange={e => setQuery(e.target.value)} placeholder="Buscar por telefone, produto ou sequência…" className="pl-8" />
      </div>
      {showStatus && (
        <Select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
          <option value="all">Todos os status</option>
          {[...new Set(customers.map(r => r.status).filter(Boolean))].map(s => (
            <option key={s} value={s}>{s}</option>
          ))}
        </Select>
      )}
      <Btn onClick={onRefresh} disabled={refreshing} className="whitespace-nowrap">
        {refreshing
          ? <><svg className="animate-spin h-3.5 w-3.5" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="31.4 62.8" /></svg> Atualizando</>
          : "↻ Atualizar"}
      </Btn>
    </div>
  );
}

// ─── Sidebar ──────────────────────────────────────────────────────────────────
function Sidebar({ page, setPage, dark, setDark, open, setOpen }) {
  const inner = (
    <div className="flex h-full flex-col">
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-zinc-200/60 dark:border-zinc-800/60">
        <div className="h-8 w-8 flex-shrink-0 rounded-xl aurora flex items-center justify-center text-white text-xs font-extrabold shadow-glow">S</div>
        <div>
          <div className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">Syncronix</div>
          <div className="text-sm font-extrabold text-zinc-900 dark:text-zinc-50 leading-tight">Marketing Ops</div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        <div className="mb-2 px-2 text-[10px] font-bold uppercase tracking-widest text-zinc-400">Navegação</div>
        {NAV.map(({ key, label, icon }) => (
          <button key={key} onClick={() => { setPage(key); setOpen(false); }}
            className={cn(
              "w-full flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-150 text-left",
              page === key
                ? "bg-brand-600 text-white shadow-glow-sm"
                : "text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 hover:text-zinc-900 dark:hover:text-zinc-200"
            )}
          >
            <span className="w-5 text-center text-base opacity-70">{icon}</span>
            <span>{label}</span>
            {page === key && <span className="ml-auto text-white/50 text-[10px]">●</span>}
          </button>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-3 pb-5 pt-3 space-y-2 border-t border-zinc-200/60 dark:border-zinc-800/60">
        <button onClick={() => setDark(!dark)}
          className="w-full flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-800 hover:text-zinc-800 dark:hover:text-zinc-200 transition-all">
          <span className="w-5 text-center">{dark ? "☀" : "☽"}</span>
          <span>{dark ? "Tema claro" : "Tema escuro"}</span>
        </button>
        <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950/60 p-3 text-[11px] text-zinc-400 leading-relaxed">
          Visão pública · Ações exigem chave admin.
        </div>
      </div>
    </div>
  );
  return (
    <>
      {/* Desktop */}
      <aside className="hidden lg:flex lg:fixed lg:inset-y-0 lg:left-0 lg:w-64 lg:flex-col z-30 border-r border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
        {inner}
      </aside>
      {/* Mobile overlay */}
      {open && (
        <div className="lg:hidden fixed inset-0 z-40 flex">
          <div className="fixed inset-0 bg-zinc-950/60 backdrop-blur-sm" onClick={() => setOpen(false)} />
          <aside className="relative w-72 flex flex-col bg-white dark:bg-zinc-900 sidebar-in shadow-2xl">
            {inner}
          </aside>
        </div>
      )}
    </>
  );
}

function MobileTopBar({ page, open, setOpen, dark, setDark }) {
  const cur = NAV.find(n => n.key === page);
  return (
    <div className="lg:hidden fixed top-0 inset-x-0 z-30 flex h-14 items-center justify-between border-b border-zinc-200 dark:border-zinc-800 bg-white/90 dark:bg-zinc-900/90 backdrop-blur-xl px-4">
      <button onClick={() => setOpen(!open)}
        className="h-9 w-9 flex items-center justify-center rounded-xl text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
          <line x1="2" y1="5" x2="16" y2="5" /><line x1="2" y1="9" x2="16" y2="9" /><line x1="2" y1="13" x2="16" y2="13" />
        </svg>
      </button>
      <div className="flex items-center gap-2">
        <span className="text-base opacity-40">{cur?.icon}</span>
        <span className="text-sm font-bold text-zinc-900 dark:text-zinc-50">{cur?.label}</span>
      </div>
      <button onClick={() => setDark(!dark)}
        className="h-9 w-9 flex items-center justify-center rounded-xl text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-800">
        {dark ? "☀" : "☽"}
      </button>
    </div>
  );
}

function BottomNav({ page, setPage }) {
  return (
    <div className="lg:hidden fixed bottom-0 inset-x-0 z-30 bnav border-t border-zinc-200 dark:border-zinc-800 bg-white/90 dark:bg-zinc-900/90">
      <div className="flex">
        {NAV.slice(0, 5).map(({ key, label, icon }) => (
          <button key={key} onClick={() => setPage(key)}
            className={cn("flex flex-1 flex-col items-center gap-0.5 py-2 text-[10px] font-semibold transition-all",
              page === key ? "text-brand-600" : "text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300")}>
            <span className={cn("text-lg leading-none transition-transform", page === key && "scale-110")}>{icon}</span>
            <span className="leading-none">{label}</span>
            {page === key && <div className="h-0.5 w-4 rounded-full bg-brand-600" />}
          </button>
        ))}
      </div>
    </div>
  );
}

// ─── Status Bar ───────────────────────────────────────────────────────────────
function StatusBar({ error, refreshing, health, lastUpdate, onRefresh }) {
  const cfg = error
    ? { label: "Falha de leitura", tone: "danger",  dot: "bg-red-500" }
    : refreshing
    ? { label: "Atualizando",      tone: "warning", dot: "bg-amber-400 animate-pulse" }
    : health?.status === "attention"
    ? { label: "Atenção",          tone: "warning", dot: "bg-amber-400 animate-pulse" }
    : { label: "Operacional",      tone: "success", dot: "bg-brand-600" };
  return (
    <div className="flex items-center justify-between rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-4 py-2.5">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className={cn("h-2 w-2 rounded-full", cfg.dot)} />
          <Badge tone={cfg.tone}>{cfg.label}</Badge>
        </div>
        {lastUpdate && (
          <span className="hidden sm:block text-xs text-zinc-400 dark:text-zinc-500">
            {fmtDate(lastUpdate)}
          </span>
        )}
      </div>
      <Btn size="sm" onClick={onRefresh} disabled={refreshing}>
        {refreshing ? <><svg className="animate-spin h-3 w-3" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="31.4 62.8" /></svg> Atualizando</> : "↻ Atualizar"}
      </Btn>
    </div>
  );
}

// ─── Contact Detail ───────────────────────────────────────────────────────────
function ContactDetail({ c, purchases, messages, adminKey, setAdminKey, onAction, loading }) {
  if (!c) return (
    <Card className="h-full">
      <CardC className="flex h-full min-h-[260px] items-center justify-center pt-5">
        <Empty title="Selecione um contato" desc="Clique em qualquer linha da tabela para ver detalhes e ações." />
      </CardC>
    </Card>
  );
  const rows = [
    { l: "Status",        v: <Badge tone={statusTone(c.status)}>{c.status || "—"}</Badge> },
    { l: "Sequência",     v: c.current_sequence_id || "—" },
    { l: "Step",          v: c.current_step ?? "—" },
    { l: "Próximo envio", v: fmtDate(c.next_send_at) },
    { l: "Último produto",v: c.last_product_bought || "—" },
    { l: "Opt-out",       v: c.opted_out ? <Badge tone="danger">Sim</Badge> : <Badge tone="muted">Não</Badge> },
  ];
  return (
    <Card className="grad-border">
      <CardH>
        <div className="flex items-center gap-2.5">
          <div className="h-9 w-9 rounded-xl aurora flex items-center justify-center text-white font-bold text-sm shadow-glow-sm">
            {(c.name || c.phone || "?")[0].toUpperCase()}
          </div>
          <div>
            <CardT grad>{c.name || c.phone}</CardT>
            {c.name && <CardD>{c.phone}</CardD>}
          </div>
        </div>
      </CardH>
      <CardC className="space-y-4">
        <div className="grid gap-1.5">
          {rows.map(({ l, v }) => (
            <div key={l} className="flex items-center justify-between rounded-xl bg-zinc-50 dark:bg-zinc-800/50 px-3 py-2">
              <span className="text-xs text-zinc-500 dark:text-zinc-400">{l}</span>
              <span className="text-xs text-zinc-800 dark:text-zinc-200 text-right">{v}</span>
            </div>
          ))}
        </div>

        <div className="space-y-1.5">
          <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">Chave admin</label>
          <Input value={adminKey} onChange={e => setAdminKey(e.target.value)} placeholder="x-admin-api-key" type="password" />
        </div>

        <div className="grid grid-cols-2 gap-2">
          <Btn size="sm" onClick={() => onAction("pause", c.phone)} disabled={loading}>Pausar</Btn>
          <Btn size="sm" onClick={() => onAction("reactivate", c.phone)} disabled={loading}>Reativar</Btn>
          <Btn size="sm" onClick={() => onAction("restart", c.phone)} disabled={loading}>Reiniciar</Btn>
          <Btn size="sm" onClick={() => onAction("forceNext", c.phone)} disabled={loading}>Forçar envio</Btn>
          <Btn size="sm" tone="danger" className="col-span-2" onClick={() => onAction("optOut", c.phone)} disabled={loading}>Marcar opt-out</Btn>
        </div>

        {purchases.length > 0 && (
          <div>
            <div className="mb-1.5 text-[10px] font-bold uppercase tracking-widest text-zinc-400">Compras</div>
            <div className="space-y-1.5">
              {purchases.slice(0, 4).map(r => (
                <div key={r.purchase_id || r.created_at} className="rounded-xl border border-zinc-100 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-800/40 px-3 py-2 text-xs">
                  <div className="font-semibold text-zinc-800 dark:text-zinc-200">{r.product || "—"}</div>
                  <div className="text-zinc-400 mt-0.5">{fmtDate(r.created_at || r.approved_at)}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {messages.length > 0 && (
          <div>
            <div className="mb-1.5 text-[10px] font-bold uppercase tracking-widest text-zinc-400">Mensagens recentes</div>
            <div className="space-y-1.5">
              {messages.slice(0, 4).map(r => (
                <div key={r.id || r.created_at} className="rounded-xl border border-zinc-100 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-800/40 px-3 py-2 text-xs">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-zinc-500">{r.sequence_id} · step {r.step_index}</span>
                    <Badge tone={providerTone(r.provider_status)}>{r.provider_status || "—"}</Badge>
                  </div>
                  <div className="mt-1 text-zinc-400 leading-relaxed">{(r.text || "").slice(0, 100)}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardC>
    </Card>
  );
}

// ─── Dashboard ────────────────────────────────────────────────────────────────
function Dashboard() {
  const [data, setData]           = useState(null);
  const [lastGood, setLastGood]   = useState(null);
  const [loading, setLoading]     = useState(true);
  const [refreshing, setRef]      = useState(false);
  const [error, setError]         = useState("");
  const [page, setPage]           = useState("overview");
  const [query, setQuery]         = useState("");
  const [statusFilter, setSF]     = useState("all");
  const [selPhone, setSelPhone]   = useState("");
  const [adminKey, setAdminKey]   = useState(() => localStorage.getItem("mk_admin") || "");
  const [dark, setDark]           = useState(() => localStorage.getItem("mk_theme") === "dark");
  const [mobileOpen, setMOpen]    = useState(false);
  const [actLoading, setActLoad]  = useState(false);
  const { toasts, add: toast }    = useToast();

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("mk_theme", dark ? "dark" : "light");
  }, [dark]);

  const vd = data || lastGood || { stats: {}, customers: [], purchases: [], messages: [], sequences: [], analytics: { funnel: [], health: {}, performance: {}, failures: [], sequence_issues: [] } };

  async function refresh({ initial = false } = {}) {
    if (initial) setLoading(true);
    setRef(true); setError("");
    try {
      const r = await fetch(API_URL, { cache: "no-store" });
      if (!r.ok) throw new Error(`Falha ${r.status}: ${r.statusText}`);
      const d = await r.json();
      setData(d); setLastGood(d);
    } catch (e) {
      const m = e.message || "Não foi possível carregar o dashboard.";
      setError(m); toast(m, "error");
    } finally {
      setLoading(false); setRef(false);
    }
  }

  async function runAction(action, phone) {
    if (!adminKey.trim()) { toast("Informe a chave admin.", "warning"); return; }
    const labels = { pause: "pausar", reactivate: "reativar", restart: "reiniciar", forceNext: "forçar envio", optOut: "opt-out" };
    if (!window.confirm(`Confirmar: ${labels[action]} para ${phone}?`)) return;
    localStorage.setItem("mk_admin", adminKey);
    setActLoad(true);
    try {
      const r = await fetch(ACTIONS[action].replace("{phone}", encodeURIComponent(phone)), {
        method: "POST", headers: { "x-admin-api-key": adminKey }
      });
      if (!r.ok) throw new Error(`Falha ${r.status}`);
      toast("Ação executada com sucesso.", "success");
      await refresh();
    } catch (e) {
      toast(e.message || "Não foi possível executar a ação.", "error");
    } finally {
      setActLoad(false);
    }
  }

  useEffect(() => {
    refresh({ initial: true });
    const id = setInterval(refresh, 30000);
    return () => clearInterval(id);
  }, []);

  const customers  = vd.customers  || [];
  const purchases  = vd.purchases  || [];
  const messages   = vd.messages   || [];
  const sequences  = vd.sequences  || [];
  const analytics  = vd.analytics  || {};
  const stats      = vd.stats      || {};
  const health     = analytics.health      || {};
  const perf       = analytics.performance || {};
  const failures   = analytics.failures    || [];
  const seqIssues  = analytics.sequence_issues || [];
  const attrByCur  = perf.attributed_real_revenue_by_currency || [];
  const attrBRL    = (attrByCur.find(r => r.currency === "BRL") || {}).value;
  const attrLabel  = attrByCur.length ? attrByCur.map(r => `${r.currency} ${r.value}`).join(" | ") : "Sem receita atribuída ainda";

  const selCustomer = customers.find(r => r.phone === selPhone) || customers[0] || null;
  const selPurchases = selCustomer ? purchases.filter(r => r.phone === selCustomer.phone) : [];
  const selMessages  = selCustomer ? messages.filter(r => r.phone === selCustomer.phone)  : [];

  const filtC = useMemo(() => customers.filter(r => {
    const ms = statusFilter === "all" || r.status === statusFilter;
    const hay = `${r.phone || ""} ${r.name || ""} ${r.current_sequence_id || ""} ${r.last_product_bought || ""}`.toLowerCase();
    return ms && hay.includes(query.toLowerCase());
  }), [customers, query, statusFilter]);

  const filtP = useMemo(() => purchases.filter(r =>
    `${r.phone||""} ${r.purchase_id||""} ${r.product||""}`.toLowerCase().includes(query.toLowerCase())
  ), [purchases, query]);

  const filtM = useMemo(() => messages.filter(r =>
    `${r.phone||""} ${r.sequence_id||""} ${r.provider_status||""} ${r.text||""}`.toLowerCase().includes(query.toLowerCase())
  ), [messages, query]);

  const statusChart = useMemo(() => groupCount(customers, r => r.status || "unknown"), [customers]);
  const dailySeries = useMemo(() => buildDaily(purchases, messages), [purchases, messages]);
  const topSeq = (perf.customers_by_sequence || []).slice(0, 8).map(r => ({ name: r.sequence_id, value: r.customers }));

  const colC = [
    { key: "phone",               label: "Telefone" },
    { key: "status",              label: "Status",       render: r => <Badge tone={statusTone(r.status)}>{r.status || "—"}</Badge> },
    { key: "current_sequence_id", label: "Sequência" },
    { key: "current_step",        label: "Step" },
    { key: "next_send_at",        label: "Próx. envio",  render: r => fmtDate(r.next_send_at) },
    { key: "last_product_bought", label: "Produto" },
    { key: "opted_out",           label: "Opt-out",      render: r => r.opted_out ? <Badge tone="danger">Sim</Badge> : <Badge tone="muted">Não</Badge> },
  ];
  const colP = [
    { key: "purchase_id", label: "ID" },
    { key: "phone",       label: "Telefone" },
    { key: "product",     label: "Produto" },
    { key: "approved_at", label: "Aprovado",  render: r => fmtDate(r.approved_at) },
    { key: "created_at",  label: "Criado em", render: r => fmtDate(r.created_at) },
  ];
  const colM = [
    { key: "phone",           label: "Telefone" },
    { key: "sequence_id",     label: "Sequência" },
    { key: "step_index",      label: "Step" },
    { key: "provider_status", label: "Status",  render: r => <Badge tone={providerTone(r.provider_status)}>{r.provider_status || "—"}</Badge> },
    { key: "created_at",      label: "Criado",  render: r => fmtDate(r.created_at) },
    { key: "text",            label: "Texto",   render: r => <span className="text-zinc-400" title={r.text || ""}>{(r.text || "").slice(0, 100)}</span> },
  ];

  // ── Gradient defs shared ──
  const GD = (
    <Defs>
      <LinearGradient id="gA" x1="0" y1="0" x2="1" y2="0"><Stop offset="0%" stopColor="#25D366" stopOpacity={0.85} /><Stop offset="100%" stopColor="#0ea5e9" stopOpacity={0.9} /></LinearGradient>
      <LinearGradient id="gB" x1="0" y1="0" x2="1" y2="0"><Stop offset="0%" stopColor="#8b5cf6" stopOpacity={0.85} /><Stop offset="100%" stopColor="#25D366" stopOpacity={0.9} /></LinearGradient>
      <LinearGradient id="areaC" x1="0" y1="0" x2="0" y2="1"><Stop offset="5%" stopColor="#25D366" stopOpacity={0.35} /><Stop offset="95%" stopColor="#25D366" stopOpacity={0} /></LinearGradient>
      <LinearGradient id="areaM" x1="0" y1="0" x2="0" y2="1"><Stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.35} /><Stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} /></LinearGradient>
    </Defs>
  );
  const gridProps = { strokeDasharray: "3 3", stroke: "#27272a", strokeOpacity: 0.5 };
  const axisProps = { stroke: "#52525b", fontSize: 11, tick: { fill: "#71717a" }, axisLine: false, tickLine: false };

  function renderPage() {
    if (loading) return <div className="page-enter"><Skeleton rows={14} /></div>;

    // ── Overview ──
    if (page === "overview") return (
      <div className="space-y-5 page-enter">
        <PH title="Overview" desc="Indicadores executivos, funil e saúde da automação." />

        <section className="grid gap-3 grid-cols-2 md:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-7">
          <Metric label="Clientes"        value={stats.customers_total}                  detail="Base monitorada"        icon="◎" />
          <Metric label="Ativos"          value={stats.customers_active}                 detail="Em sequência"           tone="success" icon="▲" />
          <Metric label="Aguard. compra"  value={stats.customers_waiting_purchase}       detail="Fim da jornada"         tone="warning" icon="◷" />
          <Metric label="Compras"         value={stats.purchases_total}                  detail="Eventos Hotmart"        icon="◈" />
          <Metric label="Mensagens"       value={stats.messages_sent_total}              detail={`${health.failed_messages || 0} falhas`} tone={(health.failed_messages || 0) > 0 ? "danger" : "default"} icon="◫" />
          <Metric label="Vendas WA"       value={perf.attributed_sales_whatsapp || 0}   detail="via UTM/SCK"            tone="success" icon="◉" />
          <Metric label="Receita WA"      value={typeof attrBRL === "number" ? attrBRL : null} detail={attrLabel}       tone="info"    icon="◆" />
        </section>

        <section className="grid gap-4 xl:grid-cols-[1.3fr_0.7fr]">
          <Card glow>
            <CardH><CardT grad>Funil da automação</CardT><CardD>Etapas da jornada pós-compra</CardD></CardH>
            <CardC className="h-[280px]">
              {loading ? <Skeleton rows={5} /> : (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={analytics.funnel || []} layout="vertical" margin={{ left: 0, right: 16, top: 4, bottom: 4 }}>
                    {GD}
                    <CartesianGrid {...gridProps} horizontal={false} />
                    <XAxis type="number" allowDecimals={false} {...axisProps} />
                    <YAxis type="category" dataKey="stage" width={140} {...axisProps} />
                    <Tooltip content={<CTip />} />
                    <Bar dataKey="value" fill="url(#gA)" radius={[0, 8, 8, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardC>
          </Card>

          <Card>
            <CardH><CardT>Saúde do sistema</CardT><CardD>Status operacional em tempo real</CardD></CardH>
            <CardC className="space-y-2">
              {[
                { l: "Marketing",     v: <Badge tone={health.marketing_enabled ? "success" : "warning"}>{health.marketing_enabled ? "ligado" : "desligado"}</Badge> },
                { l: "Scheduler",     v: <span className="font-mono text-xs">{health.scheduler_interval_seconds || "—"}s</span> },
                { l: "Sequências",    v: <span className="font-bold">{health.sequences_count || 0}</span> },
                { l: "Última compra", v: <span className="text-[11px]">{fmtDate(health.last_purchase_at)}</span> },
                { l: "Último envio",  v: <span className="text-[11px]">{fmtDate(health.last_message_at)}</span> },
                { l: "Falhas",        v: <Badge tone={(health.failed_messages || 0) > 0 ? "danger" : "success"}>{health.failed_messages || 0}</Badge> },
              ].map(({ l, v }) => (
                <div key={l} className="flex items-center justify-between rounded-xl bg-zinc-50 dark:bg-zinc-800/50 px-3 py-2">
                  <span className="text-xs text-zinc-500 dark:text-zinc-400">{l}</span>
                  <span className="text-xs">{v}</span>
                </div>
              ))}
            </CardC>
          </Card>
        </section>

        <section className="grid gap-4 xl:grid-cols-2">
          <Card glow>
            <CardH><CardT grad>Volume diário</CardT><CardD>Compras e mensagens — últimos 14 dias</CardD></CardH>
            <CardC className="h-[260px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={dailySeries} margin={{ top: 4, right: 4, bottom: 0, left: -22 }}>
                  {GD}
                  <CartesianGrid {...gridProps} />
                  <XAxis dataKey="day" {...axisProps} />
                  <YAxis allowDecimals={false} {...axisProps} />
                  <Tooltip content={<CTip />} />
                  <Area type="monotone" dataKey="compras"   name="Compras"   stroke="#25D366" strokeWidth={2} fill="url(#areaC)" dot={false} />
                  <Area type="monotone" dataKey="mensagens" name="Mensagens" stroke="#0ea5e9" strokeWidth={2} fill="url(#areaM)" dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </CardC>
          </Card>

          <Card>
            <CardH><CardT>Status dos clientes</CardT><CardD>Distribuição atual da base</CardD></CardH>
            <CardC className="h-[260px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={statusChart} dataKey="value" nameKey="name" innerRadius={68} outerRadius={108} paddingAngle={4} strokeWidth={0}>
                    {statusChart.map(e => <Cell key={e.name} fill={STATUS_COLORS[e.name] || STATUS_COLORS.unknown} />)}
                  </Pie>
                  <Tooltip content={<CTip />} />
                </PieChart>
              </ResponsiveContainer>
            </CardC>
          </Card>
        </section>
      </div>
    );

    // ── Contacts ──
    if (page === "contacts") return (
      <div className="space-y-4 page-enter">
        <PH title="Contatos" desc="Operação por contato, histórico e ações manuais." />
        <Controls query={query} setQuery={setQuery} statusFilter={statusFilter} setStatusFilter={setSF} customers={customers} showStatus onRefresh={refresh} refreshing={refreshing} />
        <div className="grid gap-4 xl:grid-cols-[1.4fr_0.8fr]">
          <Card>
            <CardH><CardT>Base de contatos</CardT><CardD>{filtC.length} encontrados</CardD></CardH>
            <CardC>
              <Table columns={colC} rows={filtC} selKey={selPhone} onRow={r => setSelPhone(r.phone)}
                empty="Nenhum contato encontrado" emptyDesc="Ajuste os filtros ou aguarde novos eventos." />
            </CardC>
          </Card>
          <ContactDetail c={selCustomer} purchases={selPurchases} messages={selMessages}
            adminKey={adminKey} setAdminKey={setAdminKey} onAction={runAction} loading={actLoading} />
        </div>
      </div>
    );

    // ── Purchases ──
    if (page === "purchases") return (
      <div className="space-y-4 page-enter">
        <PH title="Compras" desc="Eventos Hotmart recebidos e produtos comprados." />
        <Controls query={query} setQuery={setQuery} statusFilter={statusFilter} setStatusFilter={setSF} customers={customers} showStatus={false} onRefresh={refresh} refreshing={refreshing} />
        <div className="grid gap-4 xl:grid-cols-[1fr_0.9fr]">
          <Card>
            <CardH><CardT>Compras recentes</CardT><CardD>{filtP.length} registros</CardD></CardH>
            <CardC><Table columns={colP} rows={filtP} empty="Nenhuma compra" emptyDesc="Compras aprovadas aparecerão aqui." /></CardC>
          </Card>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <Card glow>
                <CardC className="pt-5">
                  <div className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 mb-1.5">Vendas WA</div>
                  <div className="text-2xl font-extrabold grad-text"><AnimNum value={perf.attributed_sales_whatsapp || 0} /></div>
                </CardC>
              </Card>
              <Card glow>
                <CardC className="pt-5">
                  <div className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 mb-1.5">Receita WA</div>
                  <div className="text-base font-bold text-sky-600 dark:text-sky-400">{fmtMoney(attrBRL)}</div>
                  <div className="text-[10px] text-zinc-400 mt-0.5 truncate">{attrLabel}</div>
                </CardC>
              </Card>
            </div>
            <Card>
              <CardH><CardT grad>Compras por produto</CardT></CardH>
              <CardC className="h-[260px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={(perf.purchases_by_product || []).slice(0, 8)} layout="vertical">
                    {GD}
                    <CartesianGrid {...gridProps} horizontal={false} />
                    <XAxis type="number" allowDecimals={false} {...axisProps} />
                    <YAxis type="category" dataKey="product" width={120} {...axisProps} fontSize={10} />
                    <Tooltip content={<CTip />} />
                    <Bar dataKey="count" name="Compras" fill="url(#gA)" radius={[0, 6, 6, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardC>
            </Card>
            <Card>
              <CardH><CardT>Top origens de tracking</CardT></CardH>
              <CardC className="space-y-1.5">
                {(perf.purchases_by_tracking_source || []).slice(0, 5).map(r => (
                  <div key={r.source} className="flex items-center justify-between rounded-xl bg-zinc-50 dark:bg-zinc-800/50 px-3 py-2 text-xs">
                    <span className="text-zinc-600 dark:text-zinc-400 truncate pr-2">{r.source}</span>
                    <Badge tone="muted">{r.count}</Badge>
                  </div>
                ))}
                {!(perf.purchases_by_tracking_source || []).length && <Empty title="Sem dados" />}
              </CardC>
            </Card>
          </div>
        </div>
      </div>
    );

    // ── Messages ──
    if (page === "messages") return (
      <div className="space-y-4 page-enter">
        <PH title="Mensagens" desc="Envios recentes, status e falhas." />
        <Controls query={query} setQuery={setQuery} statusFilter={statusFilter} setStatusFilter={setSF} customers={customers} showStatus onRefresh={refresh} refreshing={refreshing} />
        <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
          <Card>
            <CardH><CardT>Mensagens recentes</CardT><CardD>{filtM.length} registros</CardD></CardH>
            <CardC><Table columns={colM} rows={filtM} empty="Nenhuma mensagem" emptyDesc="Mensagens enviadas aparecerão aqui." /></CardC>
          </Card>
          <Card>
            <CardH><CardT>Painel de falhas</CardT><CardD>Mensagens com status problemático</CardD></CardH>
            <CardC>
              {failures.length ? (
                <div className="space-y-2 max-h-[480px] overflow-y-auto">
                  {failures.map(r => (
                    <div key={r.id || `${r.phone}-${r.created_at}`} className="rounded-xl border border-red-200/60 dark:border-red-900/40 bg-red-50 dark:bg-red-950/20 p-3">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm font-bold text-red-700 dark:text-red-400">{r.phone}</span>
                        <Badge tone="danger">{r.provider_status || "falha"}</Badge>
                      </div>
                      <div className="mt-1 text-[11px] text-zinc-500">{r.sequence_id} · step {r.step_index} · {fmtDate(r.created_at)}</div>
                      <div className="mt-1.5 text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">{(r.text || "").slice(0, 160)}</div>
                    </div>
                  ))}
                </div>
              ) : <Empty title="Sem falhas recentes" desc="Nenhuma mensagem problemática nos últimos registros." />}
            </CardC>
          </Card>
        </div>
      </div>
    );

    // ── Sequences ──
    if (page === "sequences") return (
      <div className="space-y-4 page-enter">
        <PH title="Sequências" desc="Preview, performance e validações da esteira." />
        <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
          <Card glow>
            <CardH><CardT grad>Performance por sequência</CardT><CardD>Clientes por jornada</CardD></CardH>
            <CardC className="h-[380px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={topSeq} layout="vertical" margin={{ left: 0, right: 16 }}>
                  {GD}
                  <CartesianGrid {...gridProps} horizontal={false} />
                  <XAxis type="number" allowDecimals={false} {...axisProps} />
                  <YAxis type="category" dataKey="name" width={150} {...axisProps} fontSize={10} />
                  <Tooltip content={<CTip />} />
                  <Bar dataKey="value" name="Clientes" fill="url(#gB)" radius={[0, 8, 8, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardC>
          </Card>
          <Card>
            <CardH><CardT>Validador comercial</CardT><CardD>Regras de idioma, tamanho e estrutura</CardD></CardH>
            <CardC>
              {seqIssues.length ? (
                <div className="space-y-2 max-h-[360px] overflow-y-auto">
                  {seqIssues.map((issue, i) => (
                    <div key={i} className="flex items-start justify-between gap-3 rounded-xl border border-zinc-200 dark:border-zinc-800 p-3">
                      <div>
                        <div className="text-sm font-semibold text-zinc-800 dark:text-zinc-200">{issue.sequence_id}{issue.step !== undefined ? ` · step ${issue.step + 1}` : ""}</div>
                        <div className="mt-0.5 text-xs text-zinc-500">{issue.message}</div>
                      </div>
                      <Badge tone={severityTone(issue.severity)}>{issue.severity}</Badge>
                    </div>
                  ))}
                </div>
              ) : <Empty title="Sem alertas" desc="Nenhuma inconsistência nas regras atuais." />}
            </CardC>
          </Card>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {sequences.map(seq => (
            <Card key={seq.id} className="hover:border-brand-600/30 transition-colors">
              <CardH>
                <div className="flex items-start justify-between gap-2">
                  <CardT grad>{seq.name || seq.id}</CardT>
                  <Badge tone="muted">{(seq.steps || []).length} steps</Badge>
                </div>
                <CardD>{seq.language || "—"} · {seq.target_product || "—"}</CardD>
              </CardH>
              <CardC className="space-y-2">
                {(seq.steps || []).map((step, i) => (
                  <div key={i} className="rounded-xl bg-zinc-50 dark:bg-zinc-800/50 p-3">
                    <div className="mb-1.5 flex justify-between text-[10px] font-bold text-zinc-400 uppercase tracking-wider">
                      <span>Step {i + 1}</span><span>{(step.text || "").length} chars</span>
                    </div>
                    <div className="whitespace-pre-wrap text-xs leading-relaxed text-zinc-600 dark:text-zinc-400">{step.text}</div>
                  </div>
                ))}
              </CardC>
            </Card>
          ))}
        </div>
      </div>
    );

    // ── System ──
    if (page === "system") return (
      <div className="space-y-4 page-enter">
        <PH title="Sistema" desc="Configuração operacional e leituras técnicas." />
        <div className="grid gap-3 grid-cols-2 xl:grid-cols-4">
          <Metric label="Scheduler"     value={health.scheduler_interval_seconds ? `${health.scheduler_interval_seconds}s` : "—"} detail="Intervalo de execução" />
          <Metric label="Sequências"    value={health.sequences_count}  detail="Jornadas carregadas" />
          <Metric label="Última compra" value={fmtDate(health.last_purchase_at)} detail="Webhook registrado" />
          <Metric label="Último envio"  value={fmtDate(health.last_message_at)}  detail="Mensagem enviada" />
        </div>
        <div className="grid gap-4 xl:grid-cols-2">
          <Card>
            <CardH><CardT grad>Configuração</CardT><CardD>Flags lidas pelo processo atual</CardD></CardH>
            <CardC className="space-y-2">
              {[
                { l: "Marketing automation", v: <Badge tone={health.marketing_enabled ? "success" : "warning"}>{String(!!health.marketing_enabled)}</Badge> },
                { l: "AI agent",             v: <Badge tone={health.ai_agent_enabled  ? "success" : "warning"}>{String(!!health.ai_agent_enabled)}</Badge> },
                { l: "Receita real tracking",v: <Badge tone={attrByCur.length ? "success" : "muted"}>{attrByCur.length ? "recebendo" : "sem atribuição"}</Badge> },
              ].map(({ l, v }) => (
                <div key={l} className="flex items-center justify-between rounded-xl bg-zinc-50 dark:bg-zinc-800/50 px-3 py-2.5 text-sm">
                  <span className="text-zinc-500 dark:text-zinc-400">{l}</span>
                  {v}
                </div>
              ))}
            </CardC>
          </Card>
          <Card>
            <CardH><CardT>Endpoints</CardT><CardD>Rotas úteis para operação</CardD></CardH>
            <CardC className="space-y-1.5">
              {["/marketing/dashboard", "/marketing/dashboard/data", "/marketing/automation/stats", "/marketing/automation/run-once", "/marketing/hotmart/webhook"].map(ep => (
                <div key={ep} className="flex items-center gap-2 rounded-xl bg-zinc-50 dark:bg-zinc-800/50 px-3 py-2 font-mono text-xs text-zinc-600 dark:text-zinc-400 hover:bg-brand-50 dark:hover:bg-brand-950/20 transition-colors cursor-default">
                  <span className="text-brand-600 dark:text-brand-400 opacity-70 font-bold">GET</span>
                  <span>{ep}</span>
                </div>
              ))}
            </CardC>
          </Card>
        </div>
      </div>
    );

    return null;
  }

  return (
    <div className="min-h-screen">
      <Sidebar page={page} setPage={setPage} dark={dark} setDark={setDark} open={mobileOpen} setOpen={setMOpen} />
      <MobileTopBar page={page} open={mobileOpen} setOpen={setMOpen} dark={dark} setDark={setDark} />

      <main className="lg:ml-64 min-h-screen pt-14 pb-20 lg:pt-0 lg:pb-0">
        <div className="mx-auto max-w-[1400px] space-y-5 px-4 py-5 lg:px-6 lg:py-6">
          {error && (
            <div className="flex items-start gap-3 rounded-2xl border border-red-200 dark:border-red-900/40 bg-red-50 dark:bg-red-950/20 px-4 py-3 text-sm text-red-700 dark:text-red-400">
              <span className="text-lg mt-0.5">⚠</span>
              <div>
                <div className="font-semibold">Não foi possível atualizar os dados.</div>
                <div className="text-xs mt-0.5 opacity-75">{error}{lastGood && " · Exibindo última leitura válida."}</div>
              </div>
            </div>
          )}
          <StatusBar error={error} refreshing={refreshing} health={health} lastUpdate={vd.generated_at} onRefresh={refresh} />
          {renderPage()}
        </div>
      </main>

      <BottomNav page={page} setPage={setPage} />
      <Toasts toasts={toasts} />
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<Dashboard />);
</script>
</body>
</html>"""
