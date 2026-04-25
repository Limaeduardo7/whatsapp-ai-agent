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
              50:"#f0fdf4",100:"#dcfce7",200:"#bbf7d0",
              400:"#4ade80",500:"#22c55e",600:"#25D366",
              700:"#15803d",800:"#166534",950:"#052e16"
            }
          },
          boxShadow: {
            glow: "0 0 24px rgba(37,211,102,0.18)",
            "glow-sm": "0 0 12px rgba(37,211,102,0.12)"
          }
        }
      }
    };
  </script>
  <style>
    *, *::before, *::after { font-family:"Inter",system-ui,sans-serif; box-sizing:border-box; }

    @keyframes aurora { 0%,100%{background-position:0% 50%} 50%{background-position:100% 50%} }
    .aurora { background:linear-gradient(135deg,#128C7E,#25D366,#0ea5e9,#7c3aed,#25D366); background-size:300% 300%; animation:aurora 8s ease infinite; }

    .dot-grid { background-image:radial-gradient(circle,rgba(37,211,102,0.15) 1px,transparent 1px); background-size:22px 22px; }

    @keyframes shimmer { 0%{background-position:-200% 0} 100%{background-position:200% 0} }
    .shimmer-bg { background:linear-gradient(90deg,rgba(0,0,0,0.04) 25%,rgba(0,0,0,0.08) 50%,rgba(0,0,0,0.04) 75%); background-size:200% 100%; animation:shimmer 1.6s infinite; }
    .dark .shimmer-bg { background:linear-gradient(90deg,rgba(255,255,255,0.03) 25%,rgba(255,255,255,0.07) 50%,rgba(255,255,255,0.03) 75%); background-size:200% 100%; }

    .glow-card { transition:box-shadow 0.25s ease,transform 0.2s ease; }
    .glow-card:hover { box-shadow:0 0 0 1px rgba(37,211,102,0.25),0 8px 32px rgba(37,211,102,0.14); transform:translateY(-1px); }

    .grad-text { background:linear-gradient(135deg,#25D366,#0ea5e9); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }

    .grad-border { background:linear-gradient(white,white) padding-box, linear-gradient(135deg,#25D366,#0ea5e9) border-box; border:1.5px solid transparent; }
    .dark .grad-border { background:linear-gradient(#18181b,#18181b) padding-box, linear-gradient(135deg,#25D366,#0ea5e9) border-box; }

    @keyframes fadeUp { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
    .page-enter { animation:fadeUp 0.35s ease-out both; }

    @keyframes countUp { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }
    .count-up { animation:countUp 0.45s ease-out both; }

    @keyframes toastIn { from{transform:translateX(110%);opacity:0} to{transform:translateX(0);opacity:1} }
    @keyframes toastOut { from{transform:translateX(0);opacity:1} to{transform:translateX(110%);opacity:0} }
    .toast-in { animation:toastIn 0.3s ease-out both; }
    .toast-out { animation:toastOut 0.25s ease-in both; }

    @keyframes sidebarIn { from{transform:translateX(-100%)} to{transform:translateX(0)} }
    .sidebar-in { animation:sidebarIn 0.25s ease-out both; }

    ::-webkit-scrollbar { width:4px; height:4px; }
    ::-webkit-scrollbar-track { background:transparent; }
    ::-webkit-scrollbar-thumb { background:#3f3f46; border-radius:99px; }

    .trow { transition:background 0.12s; }
    .bnav { backdrop-filter:blur(14px); -webkit-backdrop-filter:blur(14px); }
  </style>
</head>
<body class="bg-zinc-50 text-zinc-950 antialiased dark:bg-zinc-950 dark:text-zinc-50 transition-colors duration-300">
<div id="root"></div>

<script crossorigin src="https://unpkg.com/react@18.2.0/umd/react.production.min.js"></script>
<script crossorigin src="https://unpkg.com/react-dom@18.2.0/umd/react-dom.production.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js"></script>
<script src="https://unpkg.com/@babel/standalone@7.25.7/babel.min.js"></script>
<script type="text/babel" data-presets="env,react">
const { useCallback, useEffect, useMemo, useRef, useState } = React;

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
  active:"#25D366", waiting_purchase:"#f59e0b", idle:"#71717a",
  paused:"#8b5cf6", opted_out:"#ef4444", completed:"#0ea5e9", unknown:"#52525b",
};
const PALETTE = ["#25D366","#0ea5e9","#8b5cf6","#f59e0b","#ef4444","#06b6d4","#84cc16","#f97316"];
const NAV = [
  { key:"overview",   label:"Overview",   icon:"⬡" },
  { key:"analytics",  label:"Analytics",  icon:"◈" },
  { key:"contacts",   label:"Contatos",   icon:"◎" },
  { key:"purchases",  label:"Compras",    icon:"◇" },
  { key:"messages",   label:"Mensagens",  icon:"◫" },
  { key:"sequences",  label:"Sequências", icon:"◩" },
  { key:"system",     label:"Sistema",    icon:"◬" },
];

// ─── Utilities ────────────────────────────────────────────────────────────────
function cn(...p) { return p.filter(Boolean).join(" "); }
function fmtDate(v) {
  if (!v) return "—";
  const d = new Date(v);
  if (isNaN(d)) return v;
  return new Intl.DateTimeFormat("pt-BR",{dateStyle:"short",timeStyle:"short"}).format(d);
}
function fmtDay(v) {
  if (!v) return "—";
  const d = new Date(v);
  if (isNaN(d)) return "—";
  return new Intl.DateTimeFormat("pt-BR",{day:"2-digit",month:"2-digit"}).format(d);
}
function fmtMoney(v) {
  if (v == null) return "Não configurada";
  return new Intl.NumberFormat("pt-BR",{style:"currency",currency:"BRL"}).format(v);
}
function statusTone(v) {
  if (v==="active") return "success";
  if (v==="waiting_purchase") return "warning";
  if (v==="paused") return "purple";
  if (v==="opted_out"||v==="error"||v==="failed") return "danger";
  return "muted";
}
function providerTone(v) {
  const n=String(v||"").toLowerCase();
  if (n.includes("fail")||n.includes("error")||n.includes("timeout")) return "danger";
  if (!n||n==="unknown") return "muted";
  return "success";
}
function severityTone(v) {
  if (v==="error") return "danger";
  if (v==="warning") return "warning";
  return "muted";
}
function groupCount(rows, fn) {
  const m=new Map();
  for(const r of rows){const k=fn(r)||"Sem valor";m.set(k,(m.get(k)||0)+1);}
  return [...m.entries()].map(([name,value])=>({name,value}));
}
function isInRange(dateStr, range) {
  if (range==="all") return true;
  const d=new Date(dateStr);
  if (isNaN(d)) return false;
  return d >= new Date(Date.now()-parseInt(range)*86400000);
}
function buildDaily(purchases, messages) {
  const m=new Map();
  const add=(items,field)=>{
    for(const x of items){
      const raw=x.created_at||x.approved_at;
      const d=raw?new Date(raw):null;
      const key=d&&!isNaN(d)?d.toISOString().slice(0,10):"sem-data";
      const cur=m.get(key)||{key,day:fmtDay(raw),compras:0,mensagens:0};
      cur[field]+=1; m.set(key,cur);
    }
  };
  add(purchases,"compras"); add(messages,"mensagens");
  return [...m.values()].sort((a,b)=>a.key.localeCompare(b.key)).slice(-14);
}

// ─── ECharts theme factory ────────────────────────────────────────────────────
function ecTheme(dark) {
  const gridLine = dark ? "#1f1f23" : "#f4f4f5";
  const axisLine = dark ? "#27272a" : "#e4e4e7";
  const label    = dark ? "#71717a" : "#52525b";
  return {
    backgroundColor: "transparent",
    color: PALETTE,
    textStyle:{ color:label, fontFamily:"Inter,system-ui,sans-serif", fontSize:11 },
    grid:{ left:12, right:16, top:28, bottom:8, containLabel:true },
    tooltip:{
      backgroundColor: dark ? "rgba(9,9,11,0.94)" : "rgba(255,255,255,0.97)",
      borderColor: dark ? "rgba(37,211,102,0.2)" : "#e4e4e7",
      textStyle:{ color: dark ? "#fff" : "#09090b", fontSize:12, fontFamily:"Inter,system-ui,sans-serif" },
      extraCssText:"backdrop-filter:blur(8px);border-radius:10px;box-shadow:0 4px 24px rgba(0,0,0,0.3);",
    },
    xAxis:{
      axisLine:{ lineStyle:{ color:axisLine } },
      axisTick:{ show:false },
      axisLabel:{ color:label, fontSize:11 },
      splitLine:{ lineStyle:{ color:gridLine, type:"dashed" } },
    },
    yAxis:{
      axisLine:{ show:false },
      axisTick:{ show:false },
      axisLabel:{ color:label, fontSize:11 },
      splitLine:{ lineStyle:{ color:gridLine, type:"dashed" } },
    },
  };
}

// ─── ECharts React wrapper ────────────────────────────────────────────────────
function EChart({ option, height=260, dark=false, className="" }) {
  const ref  = useRef(null);
  const inst = useRef(null);
  const key  = useRef(0);

  // re-init when dark mode changes
  useEffect(() => {
    if (inst.current) { echarts.dispose(inst.current); inst.current=null; }
    if (!ref.current) return;
    inst.current = echarts.init(ref.current, null, { renderer:"canvas" });
    inst.current.setOption({ ...ecTheme(dark), ...option }, { notMerge:true, lazyUpdate:false });
  }, [dark]);

  useEffect(() => {
    if (!inst.current) return;
    inst.current.setOption({ ...ecTheme(dark), ...option }, { notMerge:true });
  }, [JSON.stringify(option)]);

  useEffect(() => {
    const onResize = () => inst.current?.resize();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  return <div ref={ref} style={{ width:"100%", height }} className={className} />;
}

// ─── Animated counter (React Bits) ───────────────────────────────────────────
function AnimNum({ value }) {
  const [n, setN] = useState(0);
  const num = typeof value === "number" ? value : 0;
  useEffect(() => {
    if (num === 0) { setN(0); return; }
    let cur = 0; const step = num / (700/16);
    const id = setInterval(() => {
      cur += step;
      if (cur >= num) { setN(num); clearInterval(id); } else setN(Math.floor(cur));
    }, 16);
    return () => clearInterval(id);
  }, [num]);
  if (typeof value === "string") return <span>{value}</span>;
  return <span className="count-up">{n.toLocaleString("pt-BR")}</span>;
}

// ─── Toast ────────────────────────────────────────────────────────────────────
function useToast() {
  const [toasts, setToasts] = useState([]);
  const add = useCallback((msg, type="info") => {
    const id = Date.now();
    setToasts(p => [...p,{id,msg,type,out:false}]);
    setTimeout(()=>{
      setToasts(p=>p.map(t=>t.id===id?{...t,out:true}:t));
      setTimeout(()=>setToasts(p=>p.filter(t=>t.id!==id)),280);
    }, 4000);
  },[]);
  return {toasts,add};
}
function Toasts({toasts}) {
  const S={success:"border-brand-600/30 text-brand-300",error:"border-red-500/30 text-red-300",warning:"border-amber-500/30 text-amber-300",info:"border-zinc-700 text-zinc-300"};
  const IC={success:"✓",error:"✕",warning:"⚠",info:"ℹ"};
  return (
    <div className="fixed bottom-20 right-4 z-50 flex flex-col gap-2 lg:bottom-4">
      {toasts.map(t=>(
        <div key={t.id} className={cn("flex items-center gap-3 rounded-2xl border bg-zinc-950/90 px-4 py-3 text-sm font-medium shadow-2xl backdrop-blur-xl",S[t.type]||S.info,t.out?"toast-out":"toast-in")}>
          <span>{IC[t.type]}</span><span>{t.msg}</span>
        </div>
      ))}
    </div>
  );
}

// ─── Design System ────────────────────────────────────────────────────────────
function Card({className="",glow=false,children}) {
  return <div className={cn("rounded-2xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900 transition-all duration-200",glow&&"glow-card",className)}>{children}</div>;
}
function CardH({children,className=""}) { return <div className={cn("flex flex-col gap-1 p-5 pb-3",className)}>{children}</div>; }
function CardT({children,grad=false}) { return <h3 className={cn("text-sm font-semibold tracking-tight",grad&&"grad-text")}>{children}</h3>; }
function CardD({children}) { return <p className="text-xs text-zinc-500 dark:text-zinc-400">{children}</p>; }
function CardC({className="",children}) { return <div className={cn("p-5 pt-2",className)}>{children}</div>; }

function Btn({active,tone="default",size="md",className="",children,...p}) {
  const sz={sm:"h-7 px-2.5 text-xs",md:"h-9 px-3.5 text-sm",lg:"h-10 px-4 text-sm"};
  const T={
    default:active?"bg-brand-600 text-white border-brand-600 shadow-glow-sm":"border-zinc-200 bg-white text-zinc-700 hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800",
    danger:"border-red-200 bg-red-50 text-red-700 hover:bg-red-100 dark:border-red-900 dark:bg-red-950/50 dark:text-red-400",
    ghost:"border-transparent bg-transparent text-zinc-500 hover:bg-zinc-100 hover:text-zinc-800 dark:hover:bg-zinc-800 dark:hover:text-zinc-200",
    brand:"border-brand-600 bg-brand-600 text-white hover:bg-brand-700 shadow-glow-sm",
  };
  return <button className={cn("inline-flex items-center justify-center gap-1.5 rounded-xl border font-medium transition-all duration-150 active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-50",sz[size]||sz.md,T[tone]||T.default,className)} {...p}>{children}</button>;
}

function Badge({tone="muted",children}) {
  const T={
    default:"bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900",
    muted:"bg-zinc-100 text-zinc-600 ring-1 ring-zinc-300/60 dark:bg-zinc-800 dark:text-zinc-400 dark:ring-zinc-700/60",
    success:"bg-brand-50 text-brand-700 ring-1 ring-brand-600/20 dark:bg-brand-950/30 dark:text-brand-300",
    warning:"bg-amber-50 text-amber-700 ring-1 ring-amber-500/20 dark:bg-amber-950/30 dark:text-amber-300",
    danger:"bg-red-50 text-red-700 ring-1 ring-red-500/20 dark:bg-red-950/30 dark:text-red-300",
    purple:"bg-purple-50 text-purple-700 ring-1 ring-purple-500/20 dark:bg-purple-950/30 dark:text-purple-300",
    info:"bg-sky-50 text-sky-700 ring-1 ring-sky-500/20 dark:bg-sky-950/30 dark:text-sky-300",
  };
  return <span className={cn("inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-semibold leading-4",T[tone]||T.muted)}>{children}</span>;
}

function Input({className="",...p}) {
  return <input className={cn("h-9 w-full rounded-xl border border-zinc-200 bg-white px-3 text-sm text-zinc-900 placeholder:text-zinc-400 outline-none transition-all focus:border-brand-600/40 focus:ring-2 focus:ring-brand-600/15 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-100 dark:placeholder:text-zinc-600",className)} {...p} />;
}
function Select({className="",...p}) {
  return <select className={cn("h-9 rounded-xl border border-zinc-200 bg-white px-3 text-sm text-zinc-900 outline-none cursor-pointer transition-all focus:border-brand-600/40 focus:ring-2 focus:ring-brand-600/15 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-100",className)} {...p} />;
}

function Empty({title,desc}) {
  return (
    <div className="flex min-h-[180px] flex-col items-center justify-center rounded-xl border border-dashed border-zinc-200 dark:border-zinc-800 p-8 text-center">
      <div className="mb-2 text-3xl opacity-20">◎</div>
      <div className="text-sm font-medium text-zinc-700 dark:text-zinc-300">{title}</div>
      {desc&&<div className="mt-1 max-w-xs text-xs text-zinc-400">{desc}</div>}
    </div>
  );
}

function Skeleton({rows=6}) {
  return (
    <div className="space-y-2.5">
      {Array.from({length:rows}).map((_,i)=>(
        <div key={i} className="relative h-10 overflow-hidden rounded-xl bg-zinc-100 dark:bg-zinc-800" style={{width:`${80+(i%3)*7}%`}}>
          <div className="shimmer-bg absolute inset-0"/>
        </div>
      ))}
    </div>
  );
}

// ─── DataTable ────────────────────────────────────────────────────────────────
function Table({columns,rows,empty,emptyDesc,onRow,selKey}) {
  if (!rows.length) return <Empty title={empty} desc={emptyDesc}/>;
  return (
    <div className="overflow-hidden rounded-xl border border-zinc-200 dark:border-zinc-800">
      <div className="max-h-[520px] overflow-auto">
        <table className="w-full border-collapse text-sm">
          <thead className="sticky top-0 z-10">
            <tr className="bg-zinc-50/95 dark:bg-zinc-900/95 backdrop-blur-sm">
              {columns.map(c=>(
                <th key={c.key} className="border-b border-zinc-200 dark:border-zinc-800 px-3 py-2.5 text-left text-[10px] font-bold uppercase tracking-widest text-zinc-400 dark:text-zinc-500">
                  {c.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row,i)=>{
              const key=row.id||row.purchase_id||`${row.phone}-${i}`;
              const sel=selKey&&selKey===row.phone;
              return (
                <tr key={key} onClick={()=>onRow&&onRow(row)}
                  className={cn("trow border-b border-zinc-100 last:border-0 dark:border-zinc-800/60 hover:bg-zinc-50 dark:hover:bg-zinc-800/40",onRow&&"cursor-pointer",sel&&"bg-brand-50/60 dark:bg-brand-950/20 border-l-2 border-l-brand-600")}>
                  {columns.map(c=>(
                    <td key={c.key} className="max-w-[300px] px-3 py-2.5 align-middle text-xs text-zinc-700 dark:text-zinc-300">
                      {c.render?c.render(row):row[c.key]??"—"}
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

// ─── Metric Card ──────────────────────────────────────────────────────────────
function Metric({label,value,detail,tone="default",icon,sub}) {
  const num={
    default:"text-zinc-900 dark:text-zinc-50",
    success:"grad-text",warning:"text-amber-600 dark:text-amber-400",
    danger:"text-red-600 dark:text-red-400",info:"text-sky-600 dark:text-sky-400",
  }[tone]||"text-zinc-900 dark:text-zinc-50";
  return (
    <Card glow className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 dot-grid opacity-50 dark:opacity-20"/>
      <CardC className="pt-5 relative z-10">
        <div className="flex items-start justify-between mb-2.5">
          <p className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 dark:text-zinc-500">{label}</p>
          {icon&&<span className="text-xl opacity-25">{icon}</span>}
        </div>
        <div className={cn("text-3xl font-extrabold tracking-tight leading-none",num)}>
          <AnimNum value={value}/>
        </div>
        {detail&&<div className="mt-2 text-[11px] text-zinc-400 dark:text-zinc-500">{detail}</div>}
        {sub&&<div className="mt-1 text-[10px] text-zinc-300 dark:text-zinc-600">{sub}</div>}
        {tone==="success"&&<div className="absolute bottom-0 left-0 right-0 h-0.5 aurora opacity-70"/>}
      </CardC>
    </Card>
  );
}

function PH({title,desc,children}) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h2 className="text-xl font-extrabold tracking-tight text-zinc-900 dark:text-zinc-50">{title}</h2>
        {desc&&<p className="mt-0.5 text-sm text-zinc-500 dark:text-zinc-400">{desc}</p>}
      </div>
      {children}
    </div>
  );
}

function Controls({query,setQuery,statusFilter,setStatusFilter,customers,showStatus,onRefresh,refreshing,dateRange,setDateRange,seqFilter,setSeqFilter,sequences,showDateRange,showSeqFilter}) {
  const seqIds=useMemo(()=>[...new Set((sequences||[]).map(s=>s.id).filter(Boolean))],[sequences]);
  const cols=["1fr", showStatus&&"160px", showSeqFilter&&"160px", showDateRange&&"130px", "auto"].filter(Boolean).join(" ");
  return (
    <div className="flex flex-wrap gap-2">
      <div className="relative flex-1 min-w-[180px]">
        <svg className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-zinc-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <Input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Buscar…" className="pl-8"/>
      </div>
      {showStatus&&(
        <Select value={statusFilter} onChange={e=>setStatusFilter(e.target.value)} className="w-40">
          <option value="all">Todos os status</option>
          {[...new Set(customers.map(r=>r.status).filter(Boolean))].map(s=><option key={s} value={s}>{s}</option>)}
        </Select>
      )}
      {showSeqFilter&&(
        <Select value={seqFilter} onChange={e=>setSeqFilter(e.target.value)} className="w-44">
          <option value="all">Todas as sequências</option>
          {seqIds.map(id=><option key={id} value={id}>{id}</option>)}
        </Select>
      )}
      {showDateRange&&(
        <Select value={dateRange} onChange={e=>setDateRange(e.target.value)} className="w-36">
          <option value="all">Qualquer data</option>
          <option value="7">Últimos 7 dias</option>
          <option value="14">Últimos 14 dias</option>
          <option value="30">Últimos 30 dias</option>
        </Select>
      )}
      <Btn onClick={onRefresh} disabled={refreshing}>
        {refreshing?<><svg className="animate-spin h-3.5 w-3.5" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="31.4 62.8"/></svg> Atualizando</>:"↻ Atualizar"}
      </Btn>
    </div>
  );
}

// ─── Sidebar ──────────────────────────────────────────────────────────────────
function Sidebar({page,setPage,dark,setDark,open,setOpen,collapsed,setCollapsed}) {
  const inner=(
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-3 px-5 py-5 border-b border-zinc-200/60 dark:border-zinc-800/60">
        <div className="h-8 w-8 flex-shrink-0 rounded-xl aurora flex items-center justify-center text-white text-xs font-extrabold shadow-glow">S</div>
        <div className="flex-1 min-w-0">
          <div className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">Syncronix</div>
          <div className="text-sm font-extrabold text-zinc-900 dark:text-zinc-50 leading-tight">Marketing Ops</div>
        </div>
        <button onClick={()=>setCollapsed(true)} title="Recolher menu" className="hidden lg:flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-lg text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-all">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"><polyline points="9,2 4,7 9,12"/></svg>
        </button>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        <div className="mb-2 px-2 text-[10px] font-bold uppercase tracking-widest text-zinc-400">Navegação</div>
        {NAV.map(({key,label,icon})=>(
          <button key={key} onClick={()=>{setPage(key);setOpen(false);}}
            className={cn("w-full flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-150 text-left",page===key?"bg-brand-600 text-white shadow-glow-sm":"text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 hover:text-zinc-900 dark:hover:text-zinc-200")}>
            <span className="w-5 text-center text-base opacity-70">{icon}</span>
            <span>{label}</span>
            {page===key&&<span className="ml-auto text-white/50 text-[10px]">●</span>}
          </button>
        ))}
      </nav>
      <div className="px-3 pb-5 pt-3 space-y-2 border-t border-zinc-200/60 dark:border-zinc-800/60">
        <button onClick={()=>setDark(!dark)} className="w-full flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-800 hover:text-zinc-800 dark:hover:text-zinc-200 transition-all">
          <span className="w-5 text-center">{dark?"☀":"☽"}</span>
          <span>{dark?"Tema claro":"Tema escuro"}</span>
        </button>
        <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950/60 p-3 text-[11px] text-zinc-400 leading-relaxed">
          Visão pública · Ações exigem chave admin.
        </div>
      </div>
    </div>
  );
  return (
    <>
      <aside className={cn("hidden lg:flex lg:fixed lg:inset-y-0 lg:left-0 lg:w-64 lg:flex-col z-30 border-r border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 transition-all",collapsed&&"lg:hidden")}>{inner}</aside>
      {open&&(
        <div className="lg:hidden fixed inset-0 z-40 flex">
          <div className="fixed inset-0 bg-zinc-950/60 backdrop-blur-sm" onClick={()=>setOpen(false)}/>
          <aside className="relative w-72 flex flex-col bg-white dark:bg-zinc-900 sidebar-in shadow-2xl">{inner}</aside>
        </div>
      )}
    </>
  );
}

function MobileTopBar({page,open,setOpen,dark,setDark}) {
  const cur=NAV.find(n=>n.key===page);
  return (
    <div className="lg:hidden fixed top-0 inset-x-0 z-30 flex h-14 items-center justify-between border-b border-zinc-200 dark:border-zinc-800 bg-white/90 dark:bg-zinc-900/90 backdrop-blur-xl px-4">
      <button onClick={()=>setOpen(!open)} className="h-9 w-9 flex items-center justify-center rounded-xl text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
          <line x1="2" y1="5" x2="16" y2="5"/><line x1="2" y1="9" x2="16" y2="9"/><line x1="2" y1="13" x2="16" y2="13"/>
        </svg>
      </button>
      <div className="flex items-center gap-2">
        <span className="text-base opacity-40">{cur?.icon}</span>
        <span className="text-sm font-bold text-zinc-900 dark:text-zinc-50">{cur?.label}</span>
      </div>
      <button onClick={()=>setDark(!dark)} className="h-9 w-9 flex items-center justify-center rounded-xl text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-800">{dark?"☀":"☽"}</button>
    </div>
  );
}

function BottomNav({page,setPage}) {
  return (
    <div className="lg:hidden fixed bottom-0 inset-x-0 z-30 bnav border-t border-zinc-200 dark:border-zinc-800 bg-white/90 dark:bg-zinc-900/90">
      <div className="flex">
        {NAV.slice(0,5).map(({key,label,icon})=>(
          <button key={key} onClick={()=>setPage(key)}
            className={cn("flex flex-1 flex-col items-center gap-0.5 py-2 text-[10px] font-semibold transition-all",page===key?"text-brand-600":"text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300")}>
            <span className={cn("text-lg leading-none transition-transform",page===key&&"scale-110")}>{icon}</span>
            <span className="leading-none">{label}</span>
            {page===key&&<div className="h-0.5 w-4 rounded-full bg-brand-600"/>}
          </button>
        ))}
      </div>
    </div>
  );
}

function StatusBar({error,refreshing,health,lastUpdate,onRefresh}) {
  const cfg=error?{label:"Falha",tone:"danger",dot:"bg-red-500"}
    :refreshing?{label:"Atualizando",tone:"warning",dot:"bg-amber-400 animate-pulse"}
    :health?.status==="attention"?{label:"Atenção",tone:"warning",dot:"bg-amber-400 animate-pulse"}
    :{label:"Operacional",tone:"success",dot:"bg-brand-600"};
  return (
    <div className="flex items-center justify-between rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-4 py-2.5">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className={cn("h-2 w-2 rounded-full",cfg.dot)}/>
          <Badge tone={cfg.tone}>{cfg.label}</Badge>
        </div>
        {lastUpdate&&<span className="hidden sm:block text-xs text-zinc-400">{fmtDate(lastUpdate)}</span>}
      </div>
      <Btn size="sm" onClick={onRefresh} disabled={refreshing}>
        {refreshing?<><svg className="animate-spin h-3 w-3" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeDasharray="31.4 62.8"/></svg> Aguarde</>:"↻ Atualizar"}
      </Btn>
    </div>
  );
}

// ─── Contact Detail ───────────────────────────────────────────────────────────
function ContactDetail({c,purchases,messages,adminKey,setAdminKey,onAction,loading}) {
  if (!c) return (
    <Card className="h-full"><CardC className="flex h-full min-h-[260px] items-center justify-center pt-5"><Empty title="Selecione um contato" desc="Clique em qualquer linha para ver detalhes e ações."/></CardC></Card>
  );
  return (
    <Card className="grad-border">
      <CardH>
        <div className="flex items-center gap-2.5">
          <div className="h-9 w-9 rounded-xl aurora flex items-center justify-center text-white font-bold text-sm shadow-glow-sm">
            {(c.name||c.phone||"?")[0].toUpperCase()}
          </div>
          <div><CardT grad>{c.name||c.phone}</CardT>{c.name&&<CardD>{c.phone}</CardD>}</div>
          {c.engagement_score!=null&&<div className="ml-auto text-right"><div className="text-[10px] text-zinc-400">Engajamento</div><div className="text-lg font-bold grad-text">{c.engagement_score}</div></div>}
        </div>
      </CardH>
      <CardC className="space-y-4">
        <div className="grid gap-1.5">
          {[
            {l:"Status",v:<Badge tone={statusTone(c.status)}>{c.status||"—"}</Badge>},
            {l:"Sequência",v:c.current_sequence_id||"—"},
            {l:"Step",v:c.current_step??"—"},
            {l:"Próximo envio",v:fmtDate(c.next_send_at)},
            {l:"Último produto",v:c.last_product_bought||"—"},
            {l:"Opt-out",v:c.opted_out?<Badge tone="danger">Sim</Badge>:<Badge tone="muted">Não</Badge>},
          ].map(({l,v})=>(
            <div key={l} className="flex items-center justify-between rounded-xl bg-zinc-50 dark:bg-zinc-800/50 px-3 py-2">
              <span className="text-xs text-zinc-500 dark:text-zinc-400">{l}</span>
              <span className="text-xs">{v}</span>
            </div>
          ))}
        </div>
        <div className="space-y-1.5">
          <label className="text-[10px] font-bold uppercase tracking-widest text-zinc-400">Chave admin</label>
          <Input value={adminKey} onChange={e=>setAdminKey(e.target.value)} placeholder="x-admin-api-key" type="password"/>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <Btn size="sm" onClick={()=>onAction("pause",c.phone)} disabled={loading}>Pausar</Btn>
          <Btn size="sm" onClick={()=>onAction("reactivate",c.phone)} disabled={loading}>Reativar</Btn>
          <Btn size="sm" onClick={()=>onAction("restart",c.phone)} disabled={loading}>Reiniciar</Btn>
          <Btn size="sm" onClick={()=>onAction("forceNext",c.phone)} disabled={loading}>Forçar envio</Btn>
          <Btn size="sm" tone="danger" className="col-span-2" onClick={()=>onAction("optOut",c.phone)} disabled={loading}>Marcar opt-out</Btn>
        </div>
        {purchases.length>0&&(
          <div>
            <div className="mb-1.5 text-[10px] font-bold uppercase tracking-widest text-zinc-400">Compras</div>
            <div className="space-y-1.5">
              {purchases.slice(0,4).map(r=>(
                <div key={r.purchase_id||r.created_at} className="rounded-xl border border-zinc-100 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-800/40 px-3 py-2 text-xs">
                  <div className="font-semibold text-zinc-800 dark:text-zinc-200">{r.product||"—"}</div>
                  <div className="text-zinc-400 mt-0.5">{fmtDate(r.created_at||r.approved_at)}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardC>
    </Card>
  );
}

// ─── Pages ────────────────────────────────────────────────────────────────────

function OverviewPage({stats,analytics,health,perf,loading,attrBRL,attrLabel,customers,purchases,messages,dark}) {
  const statusChart = useMemo(()=>groupCount(customers,r=>r.status||"unknown"),[customers]);
  const daily = useMemo(()=>buildDaily(purchases,messages),[purchases,messages]);
  const funnel = analytics.funnel||[];

  const funnelOpt = {
    tooltip:{ trigger:"item", formatter:p=>`${p.name}<br/><b>${p.value}</b> (${p.data.rate_vs_top}% do topo · ${p.data.step_rate}% do anterior)` },
    series:[{
      type:"funnel", sort:"none", gap:3,
      width:"80%", left:"10%",
      label:{ show:true, position:"inside", fontSize:11, color:"#fff", formatter:p=>`${p.data.value}\n${p.data.rate_vs_top}%` },
      data: funnel.map((s,i)=>({name:s.stage,value:s.value,rate_vs_top:s.rate_vs_top,step_rate:s.step_rate,itemStyle:{color:PALETTE[i%PALETTE.length]}})),
    }],
  };

  const areaOpt = {
    tooltip:{ trigger:"axis" },
    legend:{ data:["Compras","Mensagens"], top:0, right:0, textStyle:{fontSize:11} },
    xAxis:{ type:"category", data:daily.map(d=>d.day) },
    yAxis:{ type:"value", minInterval:1 },
    series:[
      { name:"Compras",  type:"line", smooth:true, data:daily.map(d=>d.compras),  areaStyle:{color:{type:"linear",x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:"rgba(37,211,102,0.35)"},{offset:1,color:"rgba(37,211,102,0)"}]}}, lineStyle:{color:"#25D366",width:2}, itemStyle:{color:"#25D366"}, symbol:"none" },
      { name:"Mensagens",type:"line", smooth:true, data:daily.map(d=>d.mensagens),areaStyle:{color:{type:"linear",x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:"rgba(14,165,233,0.3)"},{offset:1,color:"rgba(14,165,233,0)"}]}}, lineStyle:{color:"#0ea5e9",width:2}, itemStyle:{color:"#0ea5e9"}, symbol:"none" },
    ],
  };

  const pieOpt = {
    tooltip:{ trigger:"item", formatter:"{b}: {c} ({d}%)" },
    series:[{
      type:"pie", radius:["50%","80%"], padAngle:3,
      label:{ show:true, position:"outside", fontSize:10, formatter:"{b}\n{c}" },
      data: statusChart.map(s=>({name:s.name,value:s.value,itemStyle:{color:STATUS_COLORS[s.name]||"#52525b"}})),
    }],
  };

  const failTrend = analytics.failure_trend||[];
  const failOpt = {
    tooltip:{ trigger:"axis" },
    xAxis:{ type:"category", data:failTrend.map(d=>d.day) },
    yAxis:[{type:"value",name:"Msgs",nameTextStyle:{fontSize:9}},{type:"value",name:"%",nameTextStyle:{fontSize:9},max:100,axisLabel:{formatter:v=>`${v}%`}}],
    series:[
      { name:"Enviadas", type:"bar",  data:failTrend.map(d=>d.total),  itemStyle:{color:"rgba(37,211,102,0.7)"}, barMaxWidth:18 },
      { name:"Falhas",   type:"bar",  data:failTrend.map(d=>d.failed), itemStyle:{color:"rgba(239,68,68,0.85)"}, barMaxWidth:18 },
      { name:"Taxa falha %", type:"line", yAxisIndex:1, data:failTrend.map(d=>d.rate), lineStyle:{color:"#f59e0b",width:2}, itemStyle:{color:"#f59e0b"}, symbol:"circle", symbolSize:5 },
    ],
  };

  return (
    <div className="space-y-5 page-enter">
      <PH title="Overview" desc="Indicadores executivos, funil e saúde da automação."/>
      <section className="grid gap-3 grid-cols-2 md:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-7">
        <Metric label="Clientes"       value={stats.customers_total}               detail="Base monitorada"      icon="◎"/>
        <Metric label="Ativos"         value={stats.customers_active}              detail="Em sequência"         tone="success" icon="▲"/>
        <Metric label="Aguard. compra" value={stats.customers_waiting_purchase}    detail="Fim da jornada"       tone="warning" icon="◷"/>
        <Metric label="Compras"        value={stats.purchases_total}               detail="Eventos Hotmart"      icon="◈"/>
        <Metric label="Mensagens"      value={stats.messages_sent_total}           detail={`${health.failed_messages||0} falhas`} tone={(health.failed_messages||0)>0?"danger":"default"} icon="◫"/>
        <Metric label="Vendas WA"      value={perf.attributed_sales_whatsapp||0}  detail="via UTM/SCK"          tone="success" icon="◉"/>
        <Metric label="Receita WA"     value={typeof attrBRL==="number"?attrBRL:null} detail={attrLabel}        tone="info"    icon="◆"/>
      </section>

      <section className="grid gap-4 xl:grid-cols-[1fr_1fr]">
        <Card glow>
          <CardH><CardT grad>Funil de conversão</CardT><CardD>Etapas com taxas de conversão acumuladas e step-a-step</CardD></CardH>
          <CardC>{loading?<Skeleton rows={6}/>:<EChart option={funnelOpt} height={300} dark={dark}/>}</CardC>
        </Card>
        <div className="grid gap-4 sm:grid-cols-2">
          {[
            {l:"Marketing",     v:<Badge tone={health.marketing_enabled?"success":"warning"}>{health.marketing_enabled?"ligado":"desligado"}</Badge>},
            {l:"Scheduler",     v:<span className="font-mono text-xs">{health.scheduler_interval_seconds||"—"}s</span>},
            {l:"Sequências",    v:<span className="font-bold">{health.sequences_count||0}</span>},
            {l:"Concluídas",    v:<span className="font-bold grad-text">{health.completed_customers||0}</span>},
            {l:"Última compra", v:<span className="text-[11px]">{fmtDate(health.last_purchase_at)}</span>},
            {l:"Falhas",        v:<Badge tone={(health.failed_messages||0)>0?"danger":"success"}>{health.failed_messages||0}</Badge>},
          ].map(({l,v},i)=>(
            <Card key={i} className="flex items-center justify-between px-4 py-3 gap-2">
              <span className="text-xs text-zinc-500 dark:text-zinc-400">{l}</span>
              <span className="text-xs font-medium">{v}</span>
            </Card>
          ))}
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.4fr_1fr]">
        <Card glow>
          <CardH><CardT grad>Volume diário</CardT><CardD>Compras e mensagens — últimos 14 dias</CardD></CardH>
          <CardC>{loading?<Skeleton rows={4}/>:<EChart option={areaOpt} height={240} dark={dark}/>}</CardC>
        </Card>
        <Card>
          <CardH><CardT>Distribuição de status</CardT><CardD>Clientes por estado atual</CardD></CardH>
          <CardC>{loading?<Skeleton rows={4}/>:<EChart option={pieOpt} height={240} dark={dark}/>}</CardC>
        </Card>
      </section>

      <Card>
        <CardH><CardT>Tendência de falhas — 7 dias</CardT><CardD>Volume enviado vs falhas vs taxa percentual</CardD></CardH>
        <CardC>{loading?<Skeleton rows={3}/>:<EChart option={failOpt} height={200} dark={dark}/>}</CardC>
      </Card>
    </div>
  );
}

// ─── Analytics Page ───────────────────────────────────────────────────────────
function AnalyticsPage({analytics,dark,loading}) {
  const seqAna   = analytics.sequence_analytics||[];
  const cohort   = analytics.cohort_data||{x_labels:[],y_labels:[],data:[]};
  const ttc      = analytics.time_to_conversion||{available:false};
  const engDist  = analytics.engagement_distribution||[];
  const attr     = analytics.attribution_comparison||{first_touch:[],last_touch:[]};

  // ── Cohort heatmap ──
  const cohortOpt = {
    tooltip:{ formatter:p=>{
      if(!Array.isArray(p.data)) return "";
      const [wi,si,rate]=p.data;
      return `${cohort.y_labels[wi]||""} × ${cohort.x_labels[si]||""}<br/><b>${rate}%</b> alcançaram este step`;
    }},
    grid:{left:80,right:40,top:40,bottom:40},
    xAxis:{type:"category",data:cohort.x_labels,splitArea:{show:true}},
    yAxis:{type:"category",data:cohort.y_labels,splitArea:{show:true}},
    visualMap:{min:0,max:100,calculable:true,orient:"horizontal",left:"center",bottom:0,inRange:{color:["#052e16","#15803d","#25D366","#bbf7d0"]},textStyle:{fontSize:10}},
    series:[{
      type:"heatmap",
      data:cohort.data,
      label:{show:true,formatter:p=>Array.isArray(p.data)?`${p.data[2]}%`:"",fontSize:10,color:"#fff"},
    }],
  };

  // ── Sequence conversion ranking ──
  const seqConvOpt = {
    tooltip:{ trigger:"axis" },
    xAxis:{type:"value",max:100,axisLabel:{formatter:v=>`${v}%`}},
    yAxis:{type:"category",data:seqAna.map(s=>s.name||s.id),axisLabel:{fontSize:10,width:120,overflow:"truncate"}},
    series:[
      { type:"bar",name:"Taxa de conversão (%)",data:seqAna.map(s=>({value:s.conversion_rate,itemStyle:{color:s.conversion_rate>=50?"#25D366":s.conversion_rate>=25?"#0ea5e9":"#8b5cf6"}})),barMaxWidth:20,label:{show:true,position:"right",formatter:p=>`${p.value}%`,fontSize:10} },
    ],
  };

  // ── Step completion rates (first sequence) ──
  const topSeq = seqAna[0];
  const stepRatesOpt = topSeq ? {
    tooltip:{trigger:"axis"},
    xAxis:{type:"category",data:(topSeq.step_rates||[]).map(s=>`Step ${s.step}`)},
    yAxis:{type:"value",max:100,axisLabel:{formatter:v=>`${v}%`}},
    series:[{
      type:"bar",name:"Completion rate",
      data:(topSeq.step_rates||[]).map(s=>({value:s.rate,itemStyle:{color:{type:"linear",x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:"#25D366"},{offset:1,color:"#0ea5e9"}]}}})),
      barMaxWidth:28,
      label:{show:true,position:"top",formatter:p=>`${p.value}%`,fontSize:10},
      markLine:{data:[{type:"average",name:"Média",label:{formatter:"avg {c}%",fontSize:10}}],lineStyle:{color:"#f59e0b",type:"dashed"}},
    }],
  } : {};

  // ── Time to conversion distribution ──
  const ttcOpt = ttc.available ? {
    tooltip:{trigger:"axis"},
    xAxis:{type:"category",data:(ttc.distribution||[]).map(b=>b.label)},
    yAxis:{type:"value",minInterval:1},
    series:[{
      type:"bar",name:"Clientes",
      data:(ttc.distribution||[]).map(b=>({value:b.count,itemStyle:{color:{type:"linear",x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:"#8b5cf6"},{offset:1,color:"#0ea5e9"}]}}})),
      barMaxWidth:28,
      label:{show:true,position:"top",fontSize:10},
      markLine:{data:[
        {xAxis:ttc.median!=null?String(Math.round(ttc.median))+" dias":undefined,name:"Mediana",label:{formatter:`p50: ${ttc.median}d`,fontSize:10}},
      ],lineStyle:{color:"#25D366",type:"dashed"}},
    }],
  } : {};

  // ── Engagement distribution ──
  const engOpt = {
    tooltip:{trigger:"axis",formatter:p=>`Score ${p[0].name}: <b>${p[0].value}</b> clientes`},
    xAxis:{type:"category",data:engDist.map(b=>b.range)},
    yAxis:{type:"value",minInterval:1},
    series:[{
      type:"bar",name:"Clientes",
      data:engDist.map(b=>({value:b.count,itemStyle:{color:{type:"linear",x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:b.count>0?"#25D366":"#27272a"},{offset:1,color:b.count>0?"#0ea5e9":"#18181b"}]}}})),
      barMaxWidth:22,
      label:{show:true,position:"top",fontSize:10,formatter:p=>p.value>0?p.value:""},
    }],
  };

  // ── Attribution comparison ──
  const attrSources = [...new Set([...attr.first_touch.map(x=>x.source),...attr.last_touch.map(x=>x.source)])].slice(0,8);
  const attrOpt = {
    tooltip:{trigger:"axis"},
    legend:{data:["First-touch","Last-touch"],top:0,right:0,textStyle:{fontSize:11}},
    xAxis:{type:"value"},
    yAxis:{type:"category",data:attrSources,axisLabel:{fontSize:10,width:100,overflow:"truncate"}},
    series:[
      { name:"First-touch", type:"bar", data:attrSources.map(s=>(attr.first_touch.find(x=>x.source===s)||{count:0}).count), itemStyle:{color:"rgba(37,211,102,0.8)"}, barMaxWidth:14 },
      { name:"Last-touch",  type:"bar", data:attrSources.map(s=>(attr.last_touch.find(x=>x.source===s)||{count:0}).count),  itemStyle:{color:"rgba(14,165,233,0.8)"}, barMaxWidth:14 },
    ],
  };

  return (
    <div className="space-y-5 page-enter">
      <PH title="Analytics" desc="Coortes, conversão por sequência, engajamento e atribuição avançada."/>

      {/* KPIs analíticos */}
      <section className="grid gap-3 grid-cols-2 md:grid-cols-4">
        <Metric label="Melhor sequência"  value={seqAna[0]?.conversion_rate??0} detail={seqAna[0]?.name||"—"} tone="success" sub="% conversão"/>
        <Metric label="Mediana conversão" value={ttc.available?ttc.median:null}  detail="dias do 1º purchase" tone="info"/>
        <Metric label="Clientes analisados" value={Object.keys(analytics.engagement_scores||{}).length} detail="com score de engajamento"/>
        <Metric label="Coortes ativas"    value={cohort.y_labels?.length||0}     detail="semanas com dados"/>
      </section>

      {/* Cohort heatmap */}
      <Card glow>
        <CardH><CardT grad>Coorte semanal de conversão</CardT><CardD>% de clientes que alcançaram cada step, por semana de entrada</CardD></CardH>
        <CardC>
          {loading?<Skeleton rows={6}/>:cohort.data?.length
            ?<EChart option={cohortOpt} height={Math.max(200, cohort.y_labels.length*44+80)} dark={dark}/>
            :<Empty title="Sem dados de coorte" desc="Necessário pelo menos uma semana de dados para gerar a matriz."/>}
        </CardC>
      </Card>

      {/* Sequence conversion + step rates */}
      <section className="grid gap-4 xl:grid-cols-[1fr_1fr]">
        <Card glow>
          <CardH><CardT grad>Ranking de conversão por sequência</CardT><CardD>% de clientes que chegaram ao status waiting_purchase</CardD></CardH>
          <CardC>
            {loading?<Skeleton rows={4}/>:seqAna.length
              ?<EChart option={seqConvOpt} height={Math.max(200,seqAna.length*36+60)} dark={dark}/>
              :<Empty title="Sem sequências" desc="Nenhum cliente em sequência ainda."/>}
          </CardC>
        </Card>
        <Card>
          <CardH>
            <CardT>Completion rate por step</CardT>
            <CardD>{topSeq?`${topSeq.name} (${topSeq.total_customers} clientes)`:"Sequência com mais conversões"}</CardD>
          </CardH>
          <CardC>
            {loading?<Skeleton rows={4}/>:topSeq
              ?<EChart option={stepRatesOpt} height={220} dark={dark}/>
              :<Empty title="Sem dados" desc="Nenhuma sequência com clientes ainda."/>}
          </CardC>
        </Card>
      </section>

      {/* Time to conversion + engagement */}
      <section className="grid gap-4 xl:grid-cols-[1fr_1fr]">
        <Card>
          <CardH><CardT>Tempo até conversão</CardT><CardD>Distribuição de dias entre 1ª compra e sequência concluída</CardD></CardH>
          <CardC>
            {loading?<Skeleton rows={4}/>:ttc.available
              ?(<>
                  <div className="grid grid-cols-4 gap-2 mb-3">
                    {[{l:"Min",v:`${ttc.min}d`},{l:"P25",v:`${ttc.p25}d`},{l:"Mediana",v:`${ttc.median}d`},{l:"P75",v:`${ttc.p75}d`}].map(({l,v})=>(
                      <div key={l} className="rounded-xl bg-zinc-50 dark:bg-zinc-800/50 px-2 py-2 text-center">
                        <div className="text-[10px] text-zinc-400">{l}</div>
                        <div className="text-sm font-bold grad-text">{v}</div>
                      </div>
                    ))}
                  </div>
                  <EChart option={ttcOpt} height={180} dark={dark}/>
                </>)
              :<Empty title="Sem dados" desc="Necessário clientes com sequência concluída."/>}
          </CardC>
        </Card>
        <Card>
          <CardH><CardT>Distribuição de engajamento</CardT><CardD>Score 0–100 por cliente (completion + recência + status)</CardD></CardH>
          <CardC>
            {loading?<Skeleton rows={4}/>:<EChart option={engOpt} height={240} dark={dark}/>}
          </CardC>
        </Card>
      </section>

      {/* Attribution */}
      <Card glow>
        <CardH><CardT grad>Atribuição first-touch vs last-touch</CardT><CardD>Comparação de modelos de atribuição por origem</CardD></CardH>
        <CardC>
          {loading?<Skeleton rows={4}/>:attrSources.length
            ?<EChart option={attrOpt} height={Math.max(200,attrSources.length*32+60)} dark={dark}/>
            :<Empty title="Sem dados de tracking" desc="Nenhuma origem registrada nos purchases."/>}
        </CardC>
      </Card>

      {/* Sequence detail cards */}
      {seqAna.length>0&&(
        <div>
          <PH title="Detalhe por sequência" desc="Métricas individuais de cada jornada configurada."/>
          <div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {seqAna.map(s=>(
              <Card key={s.id} className="hover:border-brand-600/30 transition-colors">
                <CardH>
                  <div className="flex items-start justify-between gap-2">
                    <CardT grad>{s.name||s.id}</CardT>
                    <Badge tone={s.conversion_rate>=50?"success":s.conversion_rate>=20?"warning":"danger"}>{s.conversion_rate}%</Badge>
                  </div>
                  <CardD>{s.language||"—"} · {s.n_steps} steps · {s.total_customers} clientes</CardD>
                </CardH>
                <CardC className="space-y-2">
                  {[
                    {l:"Convertidos",v:s.converted},
                    {l:"Avg dias p/ concluir",v:s.avg_days_to_complete!=null?`${s.avg_days_to_complete}d`:"—"},
                  ].map(({l,v})=>(
                    <div key={l} className="flex items-center justify-between rounded-xl bg-zinc-50 dark:bg-zinc-800/50 px-3 py-1.5 text-xs">
                      <span className="text-zinc-500">{l}</span><span className="font-semibold">{v}</span>
                    </div>
                  ))}
                  <div className="space-y-1 mt-1">
                    {(s.step_rates||[]).map(sr=>(
                      <div key={sr.step} className="flex items-center gap-2">
                        <span className="text-[10px] text-zinc-400 w-10">Step {sr.step}</span>
                        <div className="flex-1 h-1.5 rounded-full bg-zinc-100 dark:bg-zinc-800 overflow-hidden">
                          <div className="h-full rounded-full aurora" style={{width:`${sr.rate}%`}}/>
                        </div>
                        <span className="text-[10px] text-zinc-400 w-8 text-right">{sr.rate}%</span>
                      </div>
                    ))}
                  </div>
                </CardC>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Dashboard root ───────────────────────────────────────────────────────────
function Dashboard() {
  const [data,setData]        = useState(null);
  const [lastGood,setLastGood]= useState(null);
  const [loading,setLoading]  = useState(true);
  const [refreshing,setRef]   = useState(false);
  const [error,setError]      = useState("");
  const [page,setPage]        = useState("overview");
  const [query,setQuery]      = useState("");
  const [statusFilter,setSF]  = useState("all");
  const [dateRange,setDateRange] = useState("all");
  const [seqFilter,setSeqFilter] = useState("all");
  const [sidebarCollapsed,setCollapsed] = useState(false);
  const [selPhone,setSelPhone]= useState("");
  const [adminKey,setAdminKey]= useState(()=>localStorage.getItem("mk_admin")||"");
  const [dark,setDark]        = useState(()=>localStorage.getItem("mk_theme")!=="light");
  const [mobileOpen,setMOpen] = useState(false);
  const [actLoad,setActLoad]  = useState(false);
  const {toasts,add:toast}    = useToast();

  useEffect(()=>{ document.documentElement.classList.toggle("dark",dark); localStorage.setItem("mk_theme",dark?"dark":"light"); },[dark]);

  const vd = data||lastGood||{stats:{},customers:[],purchases:[],messages:[],sequences:[],analytics:{funnel:[],health:{},performance:{},failures:[],sequence_issues:[],engagement_scores:{},engagement_distribution:[],cohort_data:{},sequence_analytics:[],attribution_comparison:{},time_to_conversion:{},failure_trend:[]}};

  async function refresh({initial=false}={}) {
    if(initial) setLoading(true);
    setRef(true); setError("");
    try {
      const r=await fetch(API_URL,{cache:"no-store"});
      if(!r.ok) throw new Error(`Falha ${r.status}: ${r.statusText}`);
      const d=await r.json();
      setData(d); setLastGood(d);
    } catch(e) {
      const m=e.message||"Não foi possível carregar o dashboard.";
      setError(m); toast(m,"error");
    } finally { setLoading(false); setRef(false); }
  }

  async function runAction(action,phone) {
    if(!adminKey.trim()){toast("Informe a chave admin.","warning");return;}
    const labels={pause:"pausar",reactivate:"reativar",restart:"reiniciar",forceNext:"forçar envio",optOut:"opt-out"};
    if(!window.confirm(`Confirmar: ${labels[action]} para ${phone}?`)) return;
    localStorage.setItem("mk_admin",adminKey); setActLoad(true);
    try {
      const r=await fetch(ACTIONS[action].replace("{phone}",encodeURIComponent(phone)),{method:"POST",headers:{"x-admin-api-key":adminKey}});
      if(!r.ok) throw new Error(`Falha ${r.status}`);
      toast("Ação executada com sucesso.","success");
      await refresh();
    } catch(e){ toast(e.message||"Não foi possível executar.","error"); }
    finally { setActLoad(false); }
  }

  useEffect(()=>{ refresh({initial:true}); const id=setInterval(refresh,30000); return()=>clearInterval(id); },[]);

  const customers = vd.customers||[];
  const purchases = vd.purchases||[];
  const messages  = vd.messages||[];
  const sequences = vd.sequences||[];
  const analytics = vd.analytics||{};
  const stats     = vd.stats||{};
  const health    = analytics.health||{};
  const perf      = analytics.performance||{};
  const failures  = analytics.failures||[];
  const seqIssues = analytics.sequence_issues||[];
  const attrByCur = perf.attributed_real_revenue_by_currency||[];
  const attrBRL   = (attrByCur.find(r=>r.currency==="BRL")||{}).value;
  const attrLabel = attrByCur.length?attrByCur.map(r=>`${r.currency} ${r.value}`).join(" | "):"Sem receita atribuída ainda";

  const selCust    = customers.find(r=>r.phone===selPhone)||customers[0]||null;
  const selPurch   = selCust?purchases.filter(r=>r.phone===selCust.phone):[];
  const selMsgs    = selCust?messages.filter(r=>r.phone===selCust.phone):[];

  const filtC = useMemo(()=>customers.filter(r=>{
    const ms=statusFilter==="all"||r.status===statusFilter;
    const sq=seqFilter==="all"||r.current_sequence_id===seqFilter;
    const hay=`${r.phone||""} ${r.name||""} ${r.current_sequence_id||""} ${r.last_product_bought||""}`.toLowerCase();
    return ms&&sq&&hay.includes(query.toLowerCase());
  }),[customers,query,statusFilter,seqFilter]);
  const filtP = useMemo(()=>purchases.filter(r=>{
    const text=`${r.phone||""} ${r.purchase_id||""} ${r.product||""}`.toLowerCase().includes(query.toLowerCase());
    return text&&isInRange(r.approved_at||r.created_at,dateRange);
  }),[purchases,query,dateRange]);
  const filtM = useMemo(()=>messages.filter(r=>{
    const text=`${r.phone||""} ${r.sequence_id||""} ${r.provider_status||""} ${r.text||""}`.toLowerCase().includes(query.toLowerCase());
    const sq=seqFilter==="all"||r.sequence_id===seqFilter;
    return text&&sq&&isInRange(r.created_at,dateRange);
  }),[messages,query,seqFilter,dateRange]);

  const topSeqData=(perf.customers_by_sequence||[]).slice(0,8).map(r=>({name:r.sequence_id,value:r.customers}));

  const colC=[
    {key:"phone",label:"Telefone"},
    {key:"status",label:"Status",render:r=><Badge tone={statusTone(r.status)}>{r.status||"—"}</Badge>},
    {key:"engagement_score",label:"Score",render:r=><span className={cn("font-bold text-xs",r.engagement_score>=70?"grad-text":r.engagement_score>=40?"text-amber-500":"text-zinc-400")}>{r.engagement_score??"—"}</span>},
    {key:"current_sequence_id",label:"Sequência"},
    {key:"current_step",label:"Step"},
    {key:"next_send_at",label:"Próx. envio",render:r=>fmtDate(r.next_send_at)},
    {key:"last_product_bought",label:"Produto"},
    {key:"opted_out",label:"Opt-out",render:r=>r.opted_out?<Badge tone="danger">Sim</Badge>:<Badge tone="muted">Não</Badge>},
  ];
  const colP=[
    {key:"purchase_id",label:"ID"},
    {key:"phone",label:"Telefone"},
    {key:"product",label:"Produto"},
    {key:"approved_at",label:"Aprovado",render:r=>fmtDate(r.approved_at)},
    {key:"created_at",label:"Criado",render:r=>fmtDate(r.created_at)},
  ];
  const colM=[
    {key:"phone",label:"Telefone"},
    {key:"sequence_id",label:"Sequência"},
    {key:"step_index",label:"Step"},
    {key:"provider_status",label:"Status",render:r=><Badge tone={providerTone(r.provider_status)}>{r.provider_status||"—"}</Badge>},
    {key:"created_at",label:"Criado",render:r=>fmtDate(r.created_at)},
    {key:"text",label:"Texto",render:r=><span className="text-zinc-400" title={r.text||""}>{(r.text||"").slice(0,100)}</span>},
  ];

  function renderPage() {
    if(loading) return <div className="page-enter"><Skeleton rows={14}/></div>;

    if(page==="overview") return <OverviewPage stats={stats} analytics={analytics} health={health} perf={perf} loading={loading} attrBRL={attrBRL} attrLabel={attrLabel} customers={customers} purchases={purchases} messages={messages} dark={dark}/>;

    if(page==="analytics") return <AnalyticsPage analytics={analytics} dark={dark} loading={loading}/>;

    if(page==="contacts") return (
      <div className="space-y-4 page-enter">
        <PH title="Contatos" desc="Operação por contato, histórico e ações manuais."/>
        <Controls query={query} setQuery={setQuery} statusFilter={statusFilter} setStatusFilter={setSF} customers={customers} showStatus sequences={sequences} seqFilter={seqFilter} setSeqFilter={setSeqFilter} showSeqFilter onRefresh={refresh} refreshing={refreshing}/>
        <div className="grid gap-4 xl:grid-cols-[1.4fr_0.8fr]">
          <Card>
            <CardH><CardT>Base de contatos</CardT><CardD>{filtC.length} encontrados · coluna Score = engajamento 0–100</CardD></CardH>
            <CardC><Table columns={colC} rows={filtC} selKey={selPhone} onRow={r=>setSelPhone(r.phone)} empty="Nenhum contato" emptyDesc="Ajuste filtros ou aguarde eventos."/></CardC>
          </Card>
          <ContactDetail c={selCust} purchases={selPurch} messages={selMsgs} adminKey={adminKey} setAdminKey={setAdminKey} onAction={runAction} loading={actLoad}/>
        </div>
      </div>
    );

    if(page==="purchases") {
      const byProdOpt={
        tooltip:{trigger:"axis"},
        xAxis:{type:"value"},
        yAxis:{type:"category",data:(perf.purchases_by_product||[]).slice(0,8).map(r=>r.product),axisLabel:{fontSize:10,width:120,overflow:"truncate"}},
        series:[{type:"bar",name:"Compras",data:(perf.purchases_by_product||[]).slice(0,8).map(r=>r.count),itemStyle:{color:{type:"linear",x:0,y:0,x2:1,y2:0,colorStops:[{offset:0,color:"#25D366"},{offset:1,color:"#0ea5e9"}]}},barMaxWidth:18,label:{show:true,position:"right",fontSize:10}}],
      };
      return (
        <div className="space-y-4 page-enter">
          <PH title="Compras" desc="Eventos Hotmart recebidos e produtos comprados."/>
          <Controls query={query} setQuery={setQuery} statusFilter={statusFilter} setStatusFilter={setSF} customers={customers} showStatus={false} sequences={sequences} dateRange={dateRange} setDateRange={setDateRange} showDateRange onRefresh={refresh} refreshing={refreshing}/>
          <div className="grid gap-4 xl:grid-cols-[1fr_0.9fr]">
            <Card><CardH><CardT>Compras recentes</CardT><CardD>{filtP.length} registros</CardD></CardH><CardC><Table columns={colP} rows={filtP} empty="Nenhuma compra" emptyDesc="Aguarde eventos."/></CardC></Card>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <Card glow><CardC className="pt-5"><div className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 mb-1.5">Vendas WA</div><div className="text-2xl font-extrabold grad-text"><AnimNum value={perf.attributed_sales_whatsapp||0}/></div></CardC></Card>
                <Card glow><CardC className="pt-5"><div className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 mb-1.5">Receita WA</div><div className="text-base font-bold text-sky-600 dark:text-sky-400">{fmtMoney(attrBRL)}</div><div className="text-[10px] text-zinc-400 mt-0.5 truncate">{attrLabel}</div></CardC></Card>
              </div>
              <Card><CardH><CardT grad>Compras por produto</CardT></CardH><CardC><EChart option={byProdOpt} height={260} dark={dark}/></CardC></Card>
              <Card>
                <CardH><CardT>Top origens de tracking</CardT></CardH>
                <CardC className="space-y-1.5">
                  {(perf.purchases_by_tracking_source||[]).slice(0,6).map(r=>(
                    <div key={r.source} className="flex items-center justify-between rounded-xl bg-zinc-50 dark:bg-zinc-800/50 px-3 py-2 text-xs">
                      <span className="text-zinc-600 dark:text-zinc-400 truncate pr-2">{r.source}</span>
                      <Badge tone="muted">{r.count}</Badge>
                    </div>
                  ))}
                  {!(perf.purchases_by_tracking_source||[]).length&&<Empty title="Sem dados"/>}
                </CardC>
              </Card>
            </div>
          </div>
        </div>
      );
    }

    if(page==="messages") return (
      <div className="space-y-4 page-enter">
        <PH title="Mensagens" desc="Envios recentes, status e falhas."/>
        <Controls query={query} setQuery={setQuery} statusFilter={statusFilter} setStatusFilter={setSF} customers={customers} showStatus sequences={sequences} seqFilter={seqFilter} setSeqFilter={setSeqFilter} showSeqFilter dateRange={dateRange} setDateRange={setDateRange} showDateRange onRefresh={refresh} refreshing={refreshing}/>
        <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
          <Card><CardH><CardT>Mensagens recentes</CardT><CardD>{filtM.length} registros</CardD></CardH><CardC><Table columns={colM} rows={filtM} empty="Nenhuma mensagem" emptyDesc="Aguarde eventos."/></CardC></Card>
          <Card>
            <CardH><CardT>Painel de falhas</CardT><CardD>Mensagens com status problemático</CardD></CardH>
            <CardC>
              {failures.length?(
                <div className="space-y-2 max-h-[480px] overflow-y-auto">
                  {failures.map(r=>(
                    <div key={r.id||`${r.phone}-${r.created_at}`} className="rounded-xl border border-red-200/60 dark:border-red-900/40 bg-red-50 dark:bg-red-950/20 p-3">
                      <div className="flex items-center justify-between gap-2"><span className="text-sm font-bold text-red-700 dark:text-red-400">{r.phone}</span><Badge tone="danger">{r.provider_status||"falha"}</Badge></div>
                      <div className="mt-1 text-[11px] text-zinc-500">{r.sequence_id} · step {r.step_index} · {fmtDate(r.created_at)}</div>
                      <div className="mt-1.5 text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">{(r.text||"").slice(0,160)}</div>
                    </div>
                  ))}
                </div>
              ):<Empty title="Sem falhas recentes" desc="Nenhuma mensagem problemática."/>}
            </CardC>
          </Card>
        </div>
      </div>
    );

    if(page==="sequences") {
      const seqBarOpt={
        tooltip:{trigger:"axis"},
        xAxis:{type:"value"},
        yAxis:{type:"category",data:topSeqData.map(r=>r.name),axisLabel:{fontSize:10,width:150,overflow:"truncate"}},
        series:[{type:"bar",name:"Clientes",data:topSeqData.map(r=>({value:r.value,itemStyle:{color:{type:"linear",x:0,y:0,x2:1,y2:0,colorStops:[{offset:0,color:"#8b5cf6"},{offset:1,color:"#25D366"}]}}})),barMaxWidth:18,label:{show:true,position:"right",fontSize:10}}],
      };
      return (
        <div className="space-y-4 page-enter">
          <PH title="Sequências" desc="Preview, performance e validações da esteira."/>
          <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
            <Card glow>
              <CardH><CardT grad>Clientes por sequência</CardT></CardH>
              <CardC><EChart option={seqBarOpt} height={Math.max(200,topSeqData.length*36+60)} dark={dark}/></CardC>
            </Card>
            <Card>
              <CardH><CardT>Validador comercial</CardT><CardD>Regras de idioma, tamanho e estrutura</CardD></CardH>
              <CardC>
                {seqIssues.length?(
                  <div className="space-y-2 max-h-[360px] overflow-y-auto">
                    {seqIssues.map((issue,i)=>(
                      <div key={i} className="flex items-start justify-between gap-3 rounded-xl border border-zinc-200 dark:border-zinc-800 p-3">
                        <div>
                          <div className="text-sm font-semibold text-zinc-800 dark:text-zinc-200">{issue.sequence_id}{issue.step!==undefined?` · step ${issue.step+1}`:""}</div>
                          <div className="mt-0.5 text-xs text-zinc-500">{issue.message}</div>
                        </div>
                        <Badge tone={severityTone(issue.severity)}>{issue.severity}</Badge>
                      </div>
                    ))}
                  </div>
                ):<Empty title="Sem alertas" desc="Nenhuma inconsistência encontrada."/>}
              </CardC>
            </Card>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {sequences.map(seq=>(
              <Card key={seq.id} className="hover:border-brand-600/30 transition-colors">
                <CardH>
                  <div className="flex items-start justify-between gap-2"><CardT grad>{seq.name||seq.id}</CardT><Badge tone="muted">{(seq.steps||[]).length} steps</Badge></div>
                  <CardD>{seq.language||"—"} · {seq.target_product||"—"}</CardD>
                </CardH>
                <CardC className="space-y-2">
                  {(seq.steps||[]).map((step,i)=>(
                    <div key={i} className="rounded-xl bg-zinc-50 dark:bg-zinc-800/50 p-3">
                      <div className="mb-1.5 flex justify-between text-[10px] font-bold text-zinc-400 uppercase tracking-wider"><span>Step {i+1}</span><span>{(step.text||"").length} chars</span></div>
                      <div className="whitespace-pre-wrap break-words text-xs leading-relaxed text-zinc-600 dark:text-zinc-400 overflow-hidden max-h-40 overflow-y-auto">{step.text}</div>
                    </div>
                  ))}
                </CardC>
              </Card>
            ))}
          </div>
        </div>
      );
    }

    if(page==="system") {
      const attrByCurAll = perf.attributed_real_revenue_by_currency||[];
      return (
        <div className="space-y-4 page-enter">
          <PH title="Sistema" desc="Configuração operacional e leituras técnicas."/>
          <div className="grid gap-3 grid-cols-2 xl:grid-cols-4">
            <Metric label="Scheduler"     value={health.scheduler_interval_seconds?`${health.scheduler_interval_seconds}s`:"—"} detail="Intervalo de execução"/>
            <Metric label="Sequências"    value={health.sequences_count}  detail="Jornadas carregadas"/>
            <Metric label="Última compra" value={fmtDate(health.last_purchase_at)} detail="Webhook registrado"/>
            <Metric label="Último envio"  value={fmtDate(health.last_message_at)}  detail="Mensagem enviada"/>
          </div>
          <div className="grid gap-4 xl:grid-cols-2">
            <Card>
              <CardH><CardT grad>Configuração</CardT><CardD>Flags lidas pelo processo</CardD></CardH>
              <CardC className="space-y-2">
                {[
                  {l:"Marketing automation",v:<Badge tone={health.marketing_enabled?"success":"warning"}>{String(!!health.marketing_enabled)}</Badge>},
                  {l:"AI agent",            v:<Badge tone={health.ai_agent_enabled?"success":"warning"}>{String(!!health.ai_agent_enabled)}</Badge>},
                  {l:"Receita real tracking",v:<Badge tone={attrByCurAll.length?"success":"muted"}>{attrByCurAll.length?"recebendo":"sem atribuição"}</Badge>},
                ].map(({l,v})=>(
                  <div key={l} className="flex items-center justify-between rounded-xl bg-zinc-50 dark:bg-zinc-800/50 px-3 py-2.5 text-sm">
                    <span className="text-zinc-500 dark:text-zinc-400">{l}</span>{v}
                  </div>
                ))}
              </CardC>
            </Card>
            <Card>
              <CardH><CardT>Endpoints</CardT><CardD>Rotas úteis para operação</CardD></CardH>
              <CardC className="space-y-1.5">
                {["/marketing/dashboard","/marketing/dashboard/data","/marketing/automation/stats","/marketing/automation/run-once","/marketing/hotmart/webhook"].map(ep=>(
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
    }

    return null;
  }

  return (
    <div className="min-h-screen">
      <Sidebar page={page} setPage={setPage} dark={dark} setDark={setDark} open={mobileOpen} setOpen={setMOpen} collapsed={sidebarCollapsed} setCollapsed={setCollapsed}/>
      {/* Botão flutuante para expandir sidebar (desktop, só quando colapsado) */}
      {sidebarCollapsed&&(
        <button onClick={()=>setCollapsed(false)} title="Expandir menu" className="hidden lg:flex fixed top-4 left-4 z-40 h-9 w-9 items-center justify-center rounded-xl bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 shadow-lg hover:scale-105 transition-transform">
          <svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"><polyline points="5,2 10,7 5,12"/></svg>
        </button>
      )}
      <MobileTopBar page={page} open={mobileOpen} setOpen={setMOpen} dark={dark} setDark={setDark}/>
      <main className={cn("min-h-screen pt-14 pb-20 lg:pt-0 lg:pb-0 transition-all duration-300", sidebarCollapsed?"lg:ml-0":"lg:ml-64")}>
        <div className="mx-auto max-w-[1400px] space-y-5 px-4 py-5 lg:px-6 lg:py-6">
          {error&&(
            <div className="flex items-start gap-3 rounded-2xl border border-red-200 dark:border-red-900/40 bg-red-50 dark:bg-red-950/20 px-4 py-3 text-sm text-red-700 dark:text-red-400">
              <span className="text-lg mt-0.5">⚠</span>
              <div><div className="font-semibold">Não foi possível atualizar.</div><div className="text-xs mt-0.5 opacity-75">{error}{lastGood&&" · Última leitura válida exibida."}</div></div>
            </div>
          )}
          <StatusBar error={error} refreshing={refreshing} health={health} lastUpdate={vd.generated_at} onRefresh={refresh}/>
          {renderPage()}
        </div>
      </main>
      <BottomNav page={page} setPage={setPage}/>
      <Toasts toasts={toasts}/>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<Dashboard/>);
</script>
</body>
</html>"""
