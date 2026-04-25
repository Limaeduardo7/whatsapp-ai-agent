from __future__ import annotations


def render_marketing_dashboard() -> str:
    return """
<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Syncronix Marketing Dashboard</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: "class",
      theme: {
        extend: {
          colors: {
            border: "hsl(214.3 31.8% 91.4%)",
            muted: { DEFAULT: "hsl(210 40% 96.1%)", foreground: "hsl(215.4 16.3% 46.9%)" },
            primary: { DEFAULT: "hsl(222.2 47.4% 11.2%)", foreground: "hsl(210 40% 98%)" }
          },
          boxShadow: { soft: "0 14px 45px rgba(15, 23, 42, 0.08)" }
        }
      }
    };
  </script>
</head>
<body class="bg-slate-50 text-slate-950 antialiased dark:bg-slate-950 dark:text-slate-50">
  <div id="root"></div>

  <script crossorigin src="https://unpkg.com/react@18.2.0/umd/react.production.min.js"></script>
  <script crossorigin src="https://unpkg.com/react-dom@18.2.0/umd/react-dom.production.min.js"></script>
  <script src="https://unpkg.com/prop-types@15.8.1/prop-types.min.js"></script>
  <script src="https://unpkg.com/recharts@2.12.7/umd/Recharts.js"></script>
  <script src="https://unpkg.com/@babel/standalone@7.25.7/babel.min.js"></script>
  <script type="text/babel" data-presets="env,react">
    const { useEffect, useMemo, useState } = React;
    const {
      Bar, BarChart, CartesianGrid, Cell, Line, LineChart, Pie, PieChart,
      ResponsiveContainer, Tooltip, XAxis, YAxis
    } = Recharts;

    const API_URL = "/marketing/dashboard/data";
    const ACTIONS = {
      pause: "/marketing/automation/customers/{phone}/pause",
      reactivate: "/marketing/automation/customers/{phone}/reactivate",
      restart: "/marketing/automation/customers/{phone}/restart",
      forceNext: "/marketing/automation/customers/{phone}/force-next",
      optOut: "/marketing/automation/customers/{phone}/opt-out"
    };
    const STATUS_COLORS = {
      active: "#2563eb",
      waiting_purchase: "#f59e0b",
      idle: "#64748b",
      paused: "#9333ea",
      opted_out: "#ef4444",
      completed: "#16a34a",
      unknown: "#94a3b8"
    };

    function cn(...parts) {
      return parts.filter(Boolean).join(" ");
    }

    function Card({ className = "", children }) {
      return <div className={cn("rounded-lg border border-slate-200 bg-white shadow-soft dark:border-slate-800 dark:bg-slate-900", className)}>{children}</div>;
    }

    function CardHeader({ children, className = "" }) {
      return <div className={cn("flex flex-col gap-1.5 p-5 pb-2", className)}>{children}</div>;
    }

    function CardTitle({ children }) {
      return <h3 className="text-sm font-semibold leading-none tracking-normal">{children}</h3>;
    }

    function CardDescription({ children }) {
      return <p className="text-sm text-slate-500 dark:text-slate-400">{children}</p>;
    }

    function CardContent({ className = "", children }) {
      return <div className={cn("p-5 pt-2", className)}>{children}</div>;
    }

    function Button({ active, tone = "default", className = "", children, ...props }) {
      const tones = {
        default: active
          ? "border-slate-900 bg-slate-900 text-white dark:border-white dark:bg-white dark:text-slate-950"
          : "border-slate-200 bg-white text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800",
        danger: "border-red-200 bg-red-50 text-red-700 hover:bg-red-100 dark:border-red-900 dark:bg-red-950 dark:text-red-200",
        ghost: "border-transparent bg-transparent text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
      };
      return (
        <button
          className={cn("inline-flex h-9 items-center justify-center rounded-md border px-3 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50", tones[tone], className)}
          {...props}
        >
          {children}
        </button>
      );
    }

    function Badge({ tone = "default", children }) {
      const tones = {
        default: "bg-slate-900 text-white dark:bg-white dark:text-slate-950",
        muted: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200",
        success: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-200",
        warning: "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-200",
        danger: "bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-200",
        info: "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-200"
      };
      return <span className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold", tones[tone])}>{children}</span>;
    }

    function Input(props) {
      return <input className="h-9 w-full rounded-md border border-slate-200 bg-white px-3 text-sm outline-none placeholder:text-slate-400 focus:ring-2 focus:ring-slate-300 dark:border-slate-700 dark:bg-slate-950 dark:focus:ring-slate-700" {...props} />;
    }

    function Select(props) {
      return <select className="h-9 rounded-md border border-slate-200 bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-slate-300 dark:border-slate-700 dark:bg-slate-950 dark:focus:ring-slate-700" {...props} />;
    }

    function EmptyState({ title, description }) {
      return (
        <div className="flex min-h-[180px] flex-col items-center justify-center rounded-lg border border-dashed border-slate-200 bg-slate-50 p-8 text-center dark:border-slate-800 dark:bg-slate-950">
          <div className="text-sm font-medium">{title}</div>
          <div className="mt-1 max-w-md text-sm text-slate-500 dark:text-slate-400">{description}</div>
        </div>
      );
    }

    function SkeletonBlock({ rows = 8 }) {
      return (
        <div className="space-y-2">
          {Array.from({ length: rows }).map((_, index) => <div key={index} className="h-10 animate-pulse rounded-md bg-slate-100 dark:bg-slate-800" />)}
        </div>
      );
    }

    function formatDate(value) {
      if (!value) return "-";
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return value;
      return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(date);
    }

    function formatDay(value) {
      if (!value) return "Sem data";
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return "Sem data";
      return new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "2-digit" }).format(date);
    }

    function formatMoney(value) {
      if (value === null || value === undefined) return "Não configurada";
      return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value);
    }

    function statusTone(value) {
      if (value === "active") return "success";
      if (value === "waiting_purchase") return "warning";
      if (value === "paused") return "info";
      if (value === "opted_out" || value === "error" || value === "failed") return "danger";
      return "muted";
    }

    function severityTone(value) {
      if (value === "error") return "danger";
      if (value === "warning") return "warning";
      if (value === "info") return "info";
      return "muted";
    }

    function providerTone(value) {
      const normalized = String(value || "").toLowerCase();
      if (normalized.includes("fail") || normalized.includes("error") || normalized.includes("timeout")) return "danger";
      if (!normalized || normalized === "unknown") return "muted";
      return "success";
    }

    function groupCount(rows, getter) {
      const map = new Map();
      for (const row of rows) {
        const key = getter(row) || "Sem valor";
        map.set(key, (map.get(key) || 0) + 1);
      }
      return Array.from(map.entries()).map(([name, value]) => ({ name, value }));
    }

    function buildDailySeries(purchases, messages) {
      const map = new Map();
      for (const item of purchases) {
        const rawDate = item.created_at || item.approved_at;
        const date = rawDate ? new Date(rawDate) : null;
        const key = date && !Number.isNaN(date.getTime()) ? date.toISOString().slice(0, 10) : "sem-data";
        const current = map.get(key) || { key, day: formatDay(rawDate), compras: 0, mensagens: 0 };
        current.compras += 1;
        map.set(key, current);
      }
      for (const item of messages) {
        const rawDate = item.created_at;
        const date = rawDate ? new Date(rawDate) : null;
        const key = date && !Number.isNaN(date.getTime()) ? date.toISOString().slice(0, 10) : "sem-data";
        const current = map.get(key) || { key, day: formatDay(rawDate), compras: 0, mensagens: 0 };
        current.mensagens += 1;
        map.set(key, current);
      }
      return Array.from(map.values()).sort((a, b) => a.key.localeCompare(b.key)).slice(-14);
    }

    function DataTable({ columns, rows, emptyTitle, emptyDescription, onRowClick, selectedKey }) {
      if (!rows.length) return <EmptyState title={emptyTitle} description={emptyDescription} />;
      return (
        <div className="overflow-hidden rounded-md border border-slate-200 dark:border-slate-800">
          <div className="max-h-[520px] overflow-auto">
            <table className="w-full border-collapse text-sm">
              <thead className="sticky top-0 z-10 bg-slate-50 dark:bg-slate-900">
                <tr>
                  {columns.map((column) => (
                    <th key={column.key} className="border-b border-slate-200 px-3 py-3 text-left font-medium text-slate-500 dark:border-slate-800 dark:text-slate-400">
                      {column.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, index) => {
                  const key = row.id || row.purchase_id || `${row.phone}-${index}`;
                  return (
                    <tr
                      key={key}
                      onClick={() => onRowClick && onRowClick(row)}
                      className={cn(
                        "border-b border-slate-100 last:border-0 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50",
                        onRowClick && "cursor-pointer",
                        selectedKey && selectedKey === row.phone && "bg-blue-50 dark:bg-blue-950/40"
                      )}
                    >
                      {columns.map((column) => (
                        <td key={column.key} className="max-w-[360px] px-3 py-3 align-top">
                          {column.render ? column.render(row) : row[column.key] || "-"}
                        </td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      );
    }

    function MetricCard({ label, value, detail, tone = "default" }) {
      const toneClass = {
        default: "text-slate-950 dark:text-white",
        success: "text-emerald-700 dark:text-emerald-300",
        warning: "text-amber-700 dark:text-amber-300",
        danger: "text-red-700 dark:text-red-300",
        info: "text-blue-700 dark:text-blue-300"
      }[tone];
      return (
        <Card>
          <CardHeader>
            <CardDescription>{label}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className={cn("text-3xl font-semibold tracking-normal", toneClass)}>{value ?? 0}</div>
            <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">{detail}</div>
          </CardContent>
        </Card>
      );
    }

    function PageTitle({ title, description, children }) {
      return (
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h2 className="text-2xl font-semibold tracking-normal">{title}</h2>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{description}</p>
          </div>
          {children}
        </div>
      );
    }

    function Sidebar({ page, setPage, darkMode, setDarkMode }) {
      const items = [
        ["overview", "Overview"],
        ["contacts", "Contatos"],
        ["purchases", "Compras"],
        ["messages", "Mensagens"],
        ["sequences", "Sequências"],
        ["system", "Sistema"]
      ];
      return (
        <aside className="border-b border-slate-200 bg-white px-4 py-4 dark:border-slate-800 dark:bg-slate-900 lg:fixed lg:inset-y-0 lg:left-0 lg:w-72 lg:border-b-0 lg:border-r">
          <div className="flex items-center justify-between lg:block">
            <div>
              <div className="text-xs font-medium uppercase tracking-normal text-slate-500">Syncronix</div>
              <div className="mt-1 text-xl font-semibold">Marketing Ops</div>
            </div>
            <Button className="lg:hidden" onClick={() => setDarkMode(!darkMode)}>{darkMode ? "Claro" : "Escuro"}</Button>
          </div>
          <nav className="mt-5 grid grid-cols-2 gap-2 lg:grid-cols-1">
            {items.map(([key, label]) => (
              <Button key={key} active={page === key} className="justify-start" onClick={() => setPage(key)}>
                {label}
              </Button>
            ))}
          </nav>
          <div className="mt-6 hidden lg:block">
            <Button tone="ghost" onClick={() => setDarkMode(!darkMode)}>{darkMode ? "Tema claro" : "Tema escuro"}</Button>
          </div>
          <div className="mt-6 rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-500 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-400">
            Visão pública. Ações operacionais exigem chave admin.
          </div>
        </aside>
      );
    }

    function Dashboard() {
      const [data, setData] = useState(null);
      const [lastGoodData, setLastGoodData] = useState(null);
      const [loading, setLoading] = useState(true);
      const [refreshing, setRefreshing] = useState(false);
      const [error, setError] = useState("");
      const [page, setPage] = useState("overview");
      const [query, setQuery] = useState("");
      const [statusFilter, setStatusFilter] = useState("all");
      const [selectedPhone, setSelectedPhone] = useState("");
      const [adminKey, setAdminKey] = useState(localStorage.getItem("marketing_admin_key") || "");
      const [actionMessage, setActionMessage] = useState("");
      const [darkMode, setDarkMode] = useState(localStorage.getItem("marketing_theme") === "dark");

      useEffect(() => {
        document.documentElement.classList.toggle("dark", darkMode);
        localStorage.setItem("marketing_theme", darkMode ? "dark" : "light");
      }, [darkMode]);

      const visibleData = data || lastGoodData || {
        stats: {},
        customers: [],
        purchases: [],
        messages: [],
        sequences: [],
        analytics: { funnel: [], health: {}, performance: {}, failures: [], sequence_issues: [] }
      };

      async function refreshData({ initial = false } = {}) {
        if (initial) setLoading(true);
        setRefreshing(true);
        setError("");
        try {
          const response = await fetch(API_URL, { cache: "no-store" });
          if (!response.ok) throw new Error(`Falha ${response.status}: ${response.statusText || "erro ao carregar dados"}`);
          const nextData = await response.json();
          setData(nextData);
          setLastGoodData(nextData);
        } catch (err) {
          setError(err.message || "Não foi possível carregar o dashboard.");
        } finally {
          setLoading(false);
          setRefreshing(false);
        }
      }

      async function runAction(action, phone) {
        if (!adminKey.trim()) {
          setActionMessage("Informe a chave admin para executar ações operacionais.");
          return;
        }
        const labels = {
          pause: "pausar contato",
          reactivate: "reativar contato",
          restart: "reiniciar sequência",
          forceNext: "forçar próximo envio",
          optOut: "marcar opt-out"
        };
        if (!window.confirm(`Confirmar ação: ${labels[action]} para ${phone}?`)) return;
        localStorage.setItem("marketing_admin_key", adminKey);
        setActionMessage("Executando ação...");
        try {
          const response = await fetch(ACTIONS[action].replace("{phone}", encodeURIComponent(phone)), {
            method: "POST",
            headers: { "x-admin-api-key": adminKey }
          });
          if (!response.ok) throw new Error(`Falha ${response.status}`);
          setActionMessage("Ação executada com sucesso.");
          await refreshData();
        } catch (err) {
          setActionMessage(err.message || "Não foi possível executar a ação.");
        }
      }

      useEffect(() => {
        refreshData({ initial: true });
        const id = setInterval(() => refreshData(), 30000);
        return () => clearInterval(id);
      }, []);

      const customers = visibleData.customers || [];
      const purchases = visibleData.purchases || [];
      const messages = visibleData.messages || [];
      const sequences = visibleData.sequences || [];
      const analytics = visibleData.analytics || {};
      const stats = visibleData.stats || {};
      const health = analytics.health || {};
      const performance = analytics.performance || {};
      const failures = analytics.failures || [];
      const sequenceIssues = analytics.sequence_issues || [];

      const selectedCustomer = customers.find((row) => row.phone === selectedPhone) || customers[0] || null;
      const selectedCustomerPurchases = selectedCustomer ? purchases.filter((row) => row.phone === selectedCustomer.phone) : [];
      const selectedCustomerMessages = selectedCustomer ? messages.filter((row) => row.phone === selectedCustomer.phone) : [];

      const filteredCustomers = useMemo(() => {
        return customers.filter((row) => {
          const matchesStatus = statusFilter === "all" || row.status === statusFilter;
          const haystack = `${row.phone || ""} ${row.name || ""} ${row.current_sequence_id || ""} ${row.last_product_bought || ""}`.toLowerCase();
          return matchesStatus && haystack.includes(query.toLowerCase());
        });
      }, [customers, query, statusFilter]);

      const filteredPurchases = useMemo(() => {
        return purchases.filter((row) => `${row.phone || ""} ${row.purchase_id || ""} ${row.product || ""}`.toLowerCase().includes(query.toLowerCase()));
      }, [purchases, query]);

      const filteredMessages = useMemo(() => {
        return messages.filter((row) => `${row.phone || ""} ${row.sequence_id || ""} ${row.provider_status || ""} ${row.text || ""}`.toLowerCase().includes(query.toLowerCase()));
      }, [messages, query]);

      const statusChart = useMemo(() => groupCount(customers, (row) => row.status || "unknown"), [customers]);
      const dailySeries = useMemo(() => buildDailySeries(purchases, messages), [purchases, messages]);

      const customerColumns = [
        { key: "phone", label: "Telefone" },
        { key: "status", label: "Status", render: (row) => <Badge tone={statusTone(row.status)}>{row.status || "-"}</Badge> },
        { key: "current_sequence_id", label: "Sequência" },
        { key: "current_step", label: "Step" },
        { key: "next_send_at", label: "Próximo envio", render: (row) => formatDate(row.next_send_at) },
        { key: "last_product_bought", label: "Último produto" },
        { key: "opted_out", label: "Opt-out", render: (row) => row.opted_out ? <Badge tone="danger">Sim</Badge> : <Badge tone="muted">Não</Badge> },
        { key: "updated_at", label: "Atualizado", render: (row) => formatDate(row.updated_at) }
      ];
      const purchaseColumns = [
        { key: "purchase_id", label: "Purchase ID" },
        { key: "phone", label: "Telefone" },
        { key: "product", label: "Produto" },
        { key: "approved_at", label: "Aprovado em", render: (row) => formatDate(row.approved_at) },
        { key: "created_at", label: "Criado em", render: (row) => formatDate(row.created_at) }
      ];
      const messageColumns = [
        { key: "phone", label: "Telefone" },
        { key: "sequence_id", label: "Sequência" },
        { key: "step_index", label: "Step" },
        { key: "provider_status", label: "Status", render: (row) => <Badge tone={providerTone(row.provider_status)}>{row.provider_status || "-"}</Badge> },
        { key: "created_at", label: "Criado em", render: (row) => formatDate(row.created_at) },
        { key: "text", label: "Texto", render: (row) => <span title={row.text || ""}>{(row.text || "").slice(0, 160)}</span> }
      ];

      const topSequenceData = (performance.customers_by_sequence || []).slice(0, 8).map((row) => ({
        name: row.sequence_id,
        value: row.customers
      }));

      function ControlsBar({ showStatus = true }) {
        return (
          <div className={cn("grid gap-3", showStatus ? "md:grid-cols-[1fr_180px_auto]" : "md:grid-cols-[1fr_auto]")}>
            <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Buscar por telefone, produto, sequência ou status" />
            {showStatus && (
              <Select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
                <option value="all">Todos os status</option>
                {Array.from(new Set(customers.map((row) => row.status).filter(Boolean))).map((status) => (
                  <option key={status} value={status}>{status}</option>
                ))}
              </Select>
            )}
            <Button onClick={() => refreshData()}>{refreshing ? "Atualizando..." : "Atualizar"}</Button>
          </div>
        );
      }

      function OverviewPage() {
        return (
          <div className="space-y-5">
            <PageTitle title="Overview" description="Indicadores executivos, funil e saúde geral da automação.">
              <Badge tone={error ? "danger" : refreshing ? "warning" : health.status === "attention" ? "warning" : "success"}>
                {error ? "Falha de leitura" : refreshing ? "Atualizando" : health.status === "attention" ? "Atenção" : "Operacional"}
              </Badge>
            </PageTitle>
            {error && (
              <Card className="border-red-200 bg-red-50 text-red-900 dark:border-red-900 dark:bg-red-950 dark:text-red-100">
                <CardContent className="pt-5">
                  <div className="font-medium">Não foi possível atualizar os dados.</div>
                  <div className="text-sm">{error}</div>
                  {lastGoodData && <div className="mt-1 text-xs">Mantendo a última leitura válida na tela.</div>}
                </CardContent>
              </Card>
            )}
            <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-6">
              <MetricCard label="Clientes" value={stats.customers_total} detail="Base monitorada" />
              <MetricCard label="Ativos" value={stats.customers_active} detail="Sequência em andamento" tone="success" />
              <MetricCard label="Aguardando compra" value={stats.customers_waiting_purchase} detail="Fim da jornada" tone="warning" />
              <MetricCard label="Compras" value={stats.purchases_total} detail="Eventos registrados" />
              <MetricCard label="Mensagens" value={stats.messages_sent_total} detail={`${health.failed_messages || 0} falhas`} tone={(health.failed_messages || 0) > 0 ? "danger" : "default"} />
              <MetricCard label="Receita estimada" value={formatMoney(performance.estimated_revenue)} detail={performance.revenue_configured ? "PRODUCT_PRICE_MAP ativo" : "Configure PRODUCT_PRICE_MAP"} tone="info" />
            </section>
            <section className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
              <Card>
                <CardHeader>
                  <CardTitle>Funil da automação</CardTitle>
                  <CardDescription>Etapas principais da jornada pós-compra.</CardDescription>
                </CardHeader>
                <CardContent className="h-[330px]">
                  {loading ? <SkeletonBlock /> : (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={analytics.funnel || []} layout="vertical" margin={{ left: 8, right: 18 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                        <XAxis type="number" allowDecimals={false} stroke="#64748b" fontSize={12} />
                        <YAxis type="category" dataKey="stage" width={150} stroke="#64748b" fontSize={11} />
                        <Tooltip />
                        <Bar dataKey="value" fill="#2563eb" radius={[0, 6, 6, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Saúde do sistema</CardTitle>
                  <CardDescription>Últimos eventos e alertas operacionais.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center justify-between"><span className="text-sm text-slate-500">Marketing</span><Badge tone={health.marketing_enabled ? "success" : "warning"}>{health.marketing_enabled ? "ligado" : "desligado"}</Badge></div>
                  <div className="flex items-center justify-between"><span className="text-sm text-slate-500">Scheduler</span><span className="text-sm">{health.scheduler_interval_seconds || "-"}s</span></div>
                  <div className="flex items-center justify-between"><span className="text-sm text-slate-500">Sequências</span><span className="text-sm">{health.sequences_count || 0}</span></div>
                  <div className="flex items-center justify-between"><span className="text-sm text-slate-500">Última compra</span><span className="text-sm">{formatDate(health.last_purchase_at)}</span></div>
                  <div className="flex items-center justify-between"><span className="text-sm text-slate-500">Último envio</span><span className="text-sm">{formatDate(health.last_message_at)}</span></div>
                  <div className="flex items-center justify-between"><span className="text-sm text-slate-500">Falhas</span><Badge tone={(health.failed_messages || 0) > 0 ? "danger" : "success"}>{health.failed_messages || 0}</Badge></div>
                </CardContent>
              </Card>
            </section>
            <section className="grid gap-4 xl:grid-cols-[1fr_1fr]">
              <Card>
                <CardHeader>
                  <CardTitle>Volume diário</CardTitle>
                  <CardDescription>Compras e mensagens nos últimos registros.</CardDescription>
                </CardHeader>
                <CardContent className="h-[300px]">
                  {loading ? <SkeletonBlock /> : (
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={dailySeries}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                        <XAxis dataKey="day" stroke="#64748b" fontSize={12} />
                        <YAxis allowDecimals={false} stroke="#64748b" fontSize={12} />
                        <Tooltip />
                        <Line type="monotone" dataKey="compras" stroke="#2563eb" strokeWidth={2} dot={false} />
                        <Line type="monotone" dataKey="mensagens" stroke="#16a34a" strokeWidth={2} dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  )}
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Status dos clientes</CardTitle>
                  <CardDescription>Distribuição atual da base.</CardDescription>
                </CardHeader>
                <CardContent className="h-[300px]">
                  {loading ? <SkeletonBlock /> : (
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie data={statusChart} dataKey="value" nameKey="name" innerRadius={58} outerRadius={98} paddingAngle={3}>
                          {statusChart.map((entry) => <Cell key={entry.name} fill={STATUS_COLORS[entry.name] || STATUS_COLORS.unknown} />)}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  )}
                </CardContent>
              </Card>
            </section>
          </div>
        );
      }

      function ContactDetail({ customer }) {
        if (!customer) return <EmptyState title="Nenhum contato selecionado" description="Selecione um contato na tabela para ver detalhes." />;
        return (
          <Card>
            <CardHeader>
              <CardTitle>Detalhe do contato</CardTitle>
              <CardDescription>{customer.phone}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-3 text-sm">
                <div className="flex justify-between"><span className="text-slate-500">Status</span><Badge tone={statusTone(customer.status)}>{customer.status || "-"}</Badge></div>
                <div className="flex justify-between"><span className="text-slate-500">Sequência</span><span className="text-right">{customer.current_sequence_id || "-"}</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Step</span><span>{customer.current_step ?? "-"}</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Próximo envio</span><span>{formatDate(customer.next_send_at)}</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Último produto</span><span className="text-right">{customer.last_product_bought || "-"}</span></div>
                <div className="flex justify-between"><span className="text-slate-500">Opt-out</span>{customer.opted_out ? <Badge tone="danger">Sim</Badge> : <Badge tone="muted">Não</Badge>}</div>
              </div>
              <div className="space-y-2">
                <label className="text-xs font-medium text-slate-500">Chave admin para ações</label>
                <Input value={adminKey} onChange={(event) => setAdminKey(event.target.value)} placeholder="x-admin-api-key" type="password" />
                {actionMessage && <div className="text-xs text-slate-500">{actionMessage}</div>}
              </div>
              <div className="grid grid-cols-2 gap-2">
                <Button onClick={() => runAction("pause", customer.phone)}>Pausar</Button>
                <Button onClick={() => runAction("reactivate", customer.phone)}>Reativar</Button>
                <Button onClick={() => runAction("restart", customer.phone)}>Reiniciar</Button>
                <Button onClick={() => runAction("forceNext", customer.phone)}>Forçar envio</Button>
                <Button tone="danger" className="col-span-2" onClick={() => runAction("optOut", customer.phone)}>Marcar opt-out</Button>
              </div>
              <div>
                <div className="mb-2 text-sm font-medium">Compras do contato</div>
                <div className="space-y-2">
                  {selectedCustomerPurchases.slice(0, 5).map((row) => (
                    <div key={row.purchase_id || row.created_at} className="rounded-md bg-slate-50 p-2 text-xs dark:bg-slate-950">
                      <div className="font-medium">{row.product || "-"}</div>
                      <div className="text-slate-500">{formatDate(row.created_at || row.approved_at)}</div>
                    </div>
                  ))}
                  {!selectedCustomerPurchases.length && <div className="text-xs text-slate-500">Sem compras vinculadas.</div>}
                </div>
              </div>
              <div>
                <div className="mb-2 text-sm font-medium">Últimas mensagens</div>
                <div className="space-y-2">
                  {selectedCustomerMessages.slice(0, 5).map((row) => (
                    <div key={row.id || row.created_at} className="rounded-md bg-slate-50 p-2 text-xs dark:bg-slate-950">
                      <div className="flex justify-between gap-2"><span>{row.sequence_id}</span><Badge tone={providerTone(row.provider_status)}>{row.provider_status || "-"}</Badge></div>
                      <div className="mt-1 text-slate-500">{(row.text || "").slice(0, 120)}</div>
                    </div>
                  ))}
                  {!selectedCustomerMessages.length && <div className="text-xs text-slate-500">Sem mensagens enviadas.</div>}
                </div>
              </div>
            </CardContent>
          </Card>
        );
      }

      function ContactsPage() {
        return (
          <div className="space-y-5">
            <PageTitle title="Contatos" description="Operação por contato, histórico e ações manuais." />
            <ControlsBar showStatus={false} />
            <section className="grid gap-4 xl:grid-cols-[1.4fr_0.8fr]">
              <Card>
                <CardHeader><CardTitle>Base de contatos</CardTitle><CardDescription>{filteredCustomers.length} contatos encontrados</CardDescription></CardHeader>
                <CardContent>{loading ? <SkeletonBlock /> : <DataTable columns={customerColumns} rows={filteredCustomers} selectedKey={selectedPhone} onRowClick={(row) => setSelectedPhone(row.phone)} emptyTitle="Nenhum contato encontrado" emptyDescription="Ajuste os filtros ou aguarde novos eventos." />}</CardContent>
              </Card>
              <ContactDetail customer={selectedCustomer} />
            </section>
          </div>
        );
      }

      function PurchasesPage() {
        return (
          <div className="space-y-5">
            <PageTitle title="Compras" description="Eventos Hotmart recebidos e produtos comprados." />
            <ControlsBar showStatus={false} />
            <section className="grid gap-4 xl:grid-cols-[1fr_0.8fr]">
              <Card>
                <CardHeader><CardTitle>Compras recentes</CardTitle><CardDescription>{filteredPurchases.length} registros</CardDescription></CardHeader>
                <CardContent>{loading ? <SkeletonBlock /> : <DataTable columns={purchaseColumns} rows={filteredPurchases} emptyTitle="Nenhuma compra encontrada" emptyDescription="Compras aprovadas aparecerão aqui." />}</CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle>Produtos</CardTitle><CardDescription>Volume e receita estimada quando configurada.</CardDescription></CardHeader>
                <CardContent className="h-[420px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={(performance.purchases_by_product || []).slice(0, 10)} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis type="number" allowDecimals={false} stroke="#64748b" fontSize={12} />
                      <YAxis type="category" dataKey="product" width={170} stroke="#64748b" fontSize={11} />
                      <Tooltip />
                      <Bar dataKey="count" fill="#2563eb" radius={[0, 6, 6, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </section>
          </div>
        );
      }

      function MessagesPage() {
        return (
          <div className="space-y-5">
            <PageTitle title="Mensagens" description="Envios recentes, status e falhas." />
            <ControlsBar />
            <section className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
              <Card>
                <CardHeader><CardTitle>Mensagens recentes</CardTitle><CardDescription>{filteredMessages.length} registros</CardDescription></CardHeader>
                <CardContent>{loading ? <SkeletonBlock /> : <DataTable columns={messageColumns} rows={filteredMessages} emptyTitle="Nenhuma mensagem encontrada" emptyDescription="Mensagens enviadas aparecerão aqui." />}</CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle>Painel de falhas</CardTitle><CardDescription>Mensagens com status problemático.</CardDescription></CardHeader>
                <CardContent>
                  {(failures || []).length ? (
                    <div className="space-y-2">
                      {failures.map((row) => (
                        <div key={row.id || `${row.phone}-${row.created_at}`} className="rounded-md border border-red-100 bg-red-50 p-3 text-sm dark:border-red-900 dark:bg-red-950">
                          <div className="flex justify-between gap-2"><span className="font-medium">{row.phone}</span><Badge tone="danger">{row.provider_status || "falha"}</Badge></div>
                          <div className="mt-1 text-xs text-slate-500">{row.sequence_id} · step {row.step_index} · {formatDate(row.created_at)}</div>
                          <div className="mt-2 text-xs">{(row.text || "").slice(0, 160)}</div>
                        </div>
                      ))}
                    </div>
                  ) : <EmptyState title="Sem falhas recentes" description="Nenhuma mensagem problemática nos últimos registros." />}
                </CardContent>
              </Card>
            </section>
          </div>
        );
      }

      function SequencesPage() {
        return (
          <div className="space-y-5">
            <PageTitle title="Sequências" description="Preview, performance e validações da esteira." />
            <section className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
              <Card>
                <CardHeader><CardTitle>Performance por sequência</CardTitle><CardDescription>Clientes e envios por jornada.</CardDescription></CardHeader>
                <CardContent className="h-[420px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={topSequenceData} layout="vertical" margin={{ left: 8, right: 18 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis type="number" allowDecimals={false} stroke="#64748b" fontSize={12} />
                      <YAxis type="category" dataKey="name" width={170} stroke="#64748b" fontSize={11} />
                      <Tooltip />
                      <Bar dataKey="value" fill="#2563eb" radius={[0, 6, 6, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle>Validador comercial</CardTitle><CardDescription>Regras de idioma, tamanho, opt-out e estrutura.</CardDescription></CardHeader>
                <CardContent>
                  {sequenceIssues.length ? (
                    <div className="space-y-2">
                      {sequenceIssues.map((issue, index) => (
                        <div key={index} className="flex items-start justify-between gap-3 rounded-md border border-slate-200 p-3 text-sm dark:border-slate-800">
                          <div>
                            <div className="font-medium">{issue.sequence_id}{issue.step !== undefined ? ` · step ${issue.step + 1}` : ""}</div>
                            <div className="text-slate-500">{issue.message}</div>
                          </div>
                          <Badge tone={severityTone(issue.severity)}>{issue.severity}</Badge>
                        </div>
                      ))}
                    </div>
                  ) : <EmptyState title="Sequências sem alertas" description="Nenhuma inconsistência encontrada nas regras atuais." />}
                </CardContent>
              </Card>
            </section>
            <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {sequences.map((seq) => (
                <Card key={seq.id}>
                  <CardHeader>
                    <CardTitle>{seq.name || seq.id}</CardTitle>
                    <CardDescription>{seq.language || "-"} · {seq.target_product || "-"}</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {(seq.steps || []).map((step, index) => (
                      <div key={index} className="rounded-md bg-slate-50 p-3 text-sm dark:bg-slate-950">
                        <div className="mb-1 flex justify-between text-xs text-slate-500"><span>Step {index + 1}</span><span>{(step.text || "").length} chars</span></div>
                        <div className="whitespace-pre-wrap text-xs leading-relaxed">{step.text}</div>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              ))}
            </section>
          </div>
        );
      }

      function SystemPage() {
        return (
          <div className="space-y-5">
            <PageTitle title="Sistema" description="Configuração operacional e leituras técnicas." />
            <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <MetricCard label="Scheduler" value={`${health.scheduler_interval_seconds || "-"}s`} detail="Intervalo de execução" />
              <MetricCard label="Sequências" value={health.sequences_count} detail="Jornadas carregadas" />
              <MetricCard label="Última compra" value={formatDate(health.last_purchase_at)} detail="Webhook registrado" />
              <MetricCard label="Último envio" value={formatDate(health.last_message_at)} detail="Mensagem enviada" />
            </section>
            <section className="grid gap-4 xl:grid-cols-2">
              <Card>
                <CardHeader><CardTitle>Configuração</CardTitle><CardDescription>Flags lidas pelo processo atual.</CardDescription></CardHeader>
                <CardContent className="space-y-3 text-sm">
                  <div className="flex justify-between"><span className="text-slate-500">Marketing automation</span><Badge tone={health.marketing_enabled ? "success" : "warning"}>{String(!!health.marketing_enabled)}</Badge></div>
                  <div className="flex justify-between"><span className="text-slate-500">AI agent</span><Badge tone={health.ai_agent_enabled ? "success" : "warning"}>{String(!!health.ai_agent_enabled)}</Badge></div>
                  <div className="flex justify-between"><span className="text-slate-500">Receita estimada</span><Badge tone={performance.revenue_configured ? "success" : "muted"}>{performance.revenue_configured ? "configurada" : "sem PRODUCT_PRICE_MAP"}</Badge></div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle>Endpoints</CardTitle><CardDescription>Rotas úteis para operação.</CardDescription></CardHeader>
                <CardContent className="space-y-2 text-sm">
                  {["/marketing/dashboard", "/marketing/dashboard/data", "/marketing/automation/stats", "/marketing/automation/run-once", "/marketing/hotmart/webhook"].map((endpoint) => (
                    <div key={endpoint} className="rounded-md bg-slate-50 px-3 py-2 font-mono text-xs dark:bg-slate-950">{endpoint}</div>
                  ))}
                </CardContent>
              </Card>
            </section>
          </div>
        );
      }

      function CurrentPage() {
        if (loading) return <SkeletonBlock rows={12} />;
        if (page === "contacts") return <ContactsPage />;
        if (page === "purchases") return <PurchasesPage />;
        if (page === "messages") return <MessagesPage />;
        if (page === "sequences") return <SequencesPage />;
        if (page === "system") return <SystemPage />;
        return <OverviewPage />;
      }

      return (
        <div>
          <Sidebar page={page} setPage={setPage} darkMode={darkMode} setDarkMode={setDarkMode} />
          <main className="min-h-screen p-4 lg:ml-72 lg:p-6">
            <div className="mx-auto max-w-[1500px] space-y-5">
              <div className="flex flex-col gap-2 rounded-lg border border-slate-200 bg-white p-4 shadow-soft dark:border-slate-800 dark:bg-slate-900 md:flex-row md:items-center md:justify-between">
                <div>
                  <div className="text-xs uppercase tracking-normal text-slate-500">Atualização automática</div>
                  <div className="mt-1 text-sm text-slate-500 dark:text-slate-400">Última leitura: {formatDate(visibleData.generated_at)}</div>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Badge tone={error ? "danger" : refreshing ? "warning" : health.status === "attention" ? "warning" : "success"}>{error ? "Falha" : refreshing ? "Atualizando" : health.status === "attention" ? "Atenção" : "Operacional"}</Badge>
                  <Button onClick={() => refreshData()}>{refreshing ? "Atualizando..." : "Atualizar agora"}</Button>
                </div>
              </div>
              <CurrentPage />
            </div>
          </main>
        </div>
      );
    }

    ReactDOM.createRoot(document.getElementById("root")).render(<Dashboard />);
  </script>
</body>
</html>
"""
