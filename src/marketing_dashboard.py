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
      theme: {
        extend: {
          colors: {
            border: "hsl(214.3 31.8% 91.4%)",
            input: "hsl(214.3 31.8% 91.4%)",
            ring: "hsl(222.2 84% 4.9%)",
            background: "hsl(0 0% 100%)",
            foreground: "hsl(222.2 84% 4.9%)",
            muted: { DEFAULT: "hsl(210 40% 96.1%)", foreground: "hsl(215.4 16.3% 46.9%)" },
            primary: { DEFAULT: "hsl(222.2 47.4% 11.2%)", foreground: "hsl(210 40% 98%)" },
            destructive: { DEFAULT: "hsl(0 84.2% 60.2%)", foreground: "hsl(210 40% 98%)" },
            card: { DEFAULT: "hsl(0 0% 100%)", foreground: "hsl(222.2 84% 4.9%)" }
          },
          boxShadow: { soft: "0 12px 40px rgba(15, 23, 42, 0.08)" }
        }
      }
    }
  </script>
</head>
<body class="bg-slate-50 text-slate-950">
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
    const STATUS_COLORS = {
      active: "#2563eb",
      waiting_purchase: "#f59e0b",
      idle: "#64748b",
      completed: "#16a34a"
    };

    function cn(...parts) {
      return parts.filter(Boolean).join(" ");
    }

    function Card({ className = "", children }) {
      return <div className={cn("rounded-lg border border-slate-200 bg-white text-slate-950 shadow-soft", className)}>{children}</div>;
    }

    function CardHeader({ children }) {
      return <div className="flex flex-col gap-1.5 p-5 pb-2">{children}</div>;
    }

    function CardTitle({ children }) {
      return <h3 className="text-sm font-semibold leading-none tracking-normal">{children}</h3>;
    }

    function CardDescription({ children }) {
      return <p className="text-sm text-slate-500">{children}</p>;
    }

    function CardContent({ className = "", children }) {
      return <div className={cn("p-5 pt-2", className)}>{children}</div>;
    }

    function Button({ active, className = "", children, ...props }) {
      return (
        <button
          className={cn(
            "inline-flex h-9 items-center justify-center rounded-md border px-3 text-sm font-medium transition-colors",
            active ? "border-slate-900 bg-slate-900 text-white" : "border-slate-200 bg-white text-slate-700 hover:bg-slate-100",
            className
          )}
          {...props}
        >
          {children}
        </button>
      );
    }

    function Badge({ tone = "default", children }) {
      const tones = {
        default: "border-transparent bg-slate-900 text-white",
        muted: "border-transparent bg-slate-100 text-slate-700",
        success: "border-transparent bg-emerald-100 text-emerald-700",
        warning: "border-transparent bg-amber-100 text-amber-800",
        danger: "border-transparent bg-red-100 text-red-700"
      };
      return <span className={cn("inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold", tones[tone])}>{children}</span>;
    }

    function Input(props) {
      return <input className="h-9 w-full rounded-md border border-slate-200 bg-white px-3 text-sm outline-none ring-offset-white placeholder:text-slate-400 focus:ring-2 focus:ring-slate-300" {...props} />;
    }

    function Select(props) {
      return <select className="h-9 rounded-md border border-slate-200 bg-white px-3 text-sm outline-none focus:ring-2 focus:ring-slate-300" {...props} />;
    }

    function EmptyState({ title, description }) {
      return (
        <div className="flex min-h-[180px] flex-col items-center justify-center rounded-lg border border-dashed border-slate-200 bg-slate-50 p-8 text-center">
          <div className="text-sm font-medium">{title}</div>
          <div className="mt-1 max-w-md text-sm text-slate-500">{description}</div>
        </div>
      );
    }

    function SkeletonTable() {
      return (
        <div className="space-y-2">
          {Array.from({ length: 8 }).map((_, index) => <div key={index} className="h-10 animate-pulse rounded-md bg-slate-100" />)}
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

    function statusTone(value) {
      if (value === "active") return "success";
      if (value === "waiting_purchase") return "warning";
      if (value === "error" || value === "failed") return "danger";
      return "muted";
    }

    function normalizeStatus(value) {
      return value || "unknown";
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
        const day = formatDay(item.created_at || item.approved_at);
        const current = map.get(day) || { day, compras: 0, mensagens: 0 };
        current.compras += 1;
        map.set(day, current);
      }
      for (const item of messages) {
        const day = formatDay(item.created_at);
        const current = map.get(day) || { day, compras: 0, mensagens: 0 };
        current.mensagens += 1;
        map.set(day, current);
      }
      return Array.from(map.values()).slice(-14);
    }

    function DataTable({ columns, rows, emptyTitle, emptyDescription }) {
      if (!rows.length) return <EmptyState title={emptyTitle} description={emptyDescription} />;
      return (
        <div className="overflow-hidden rounded-md border border-slate-200">
          <div className="max-h-[460px] overflow-auto">
            <table className="w-full border-collapse text-sm">
              <thead className="sticky top-0 z-10 bg-slate-50">
                <tr>
                  {columns.map((column) => (
                    <th key={column.key} className="border-b border-slate-200 px-3 py-3 text-left font-medium text-slate-500">
                      {column.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, index) => (
                  <tr key={row.id || row.purchase_id || `${row.phone}-${index}`} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                    {columns.map((column) => (
                      <td key={column.key} className="max-w-[340px] px-3 py-3 align-top">
                        {column.render ? column.render(row) : row[column.key] || "-"}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      );
    }

    function MetricCard({ label, value, detail }) {
      return (
        <Card>
          <CardHeader>
            <CardDescription>{label}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-semibold tracking-normal">{value ?? 0}</div>
            <div className="mt-1 text-xs text-slate-500">{detail}</div>
          </CardContent>
        </Card>
      );
    }

    function Dashboard() {
      const [data, setData] = useState(null);
      const [lastGoodData, setLastGoodData] = useState(null);
      const [loading, setLoading] = useState(true);
      const [refreshing, setRefreshing] = useState(false);
      const [error, setError] = useState("");
      const [tab, setTab] = useState("customers");
      const [query, setQuery] = useState("");
      const [statusFilter, setStatusFilter] = useState("all");

      const visibleData = data || lastGoodData || { stats: {}, customers: [], purchases: [], messages: [] };

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

      useEffect(() => {
        refreshData({ initial: true });
        const id = setInterval(() => refreshData(), 30000);
        return () => clearInterval(id);
      }, []);

      const customers = visibleData.customers || [];
      const purchases = visibleData.purchases || [];
      const messages = visibleData.messages || [];
      const stats = visibleData.stats || {};

      const filteredCustomers = useMemo(() => {
        return customers.filter((row) => {
          const matchesStatus = statusFilter === "all" || row.status === statusFilter;
          const haystack = `${row.phone || ""} ${row.current_sequence_id || ""} ${row.last_product_bought || ""}`.toLowerCase();
          return matchesStatus && haystack.includes(query.toLowerCase());
        });
      }, [customers, query, statusFilter]);

      const filteredPurchases = useMemo(() => {
        return purchases.filter((row) => `${row.phone || ""} ${row.purchase_id || ""} ${row.product || ""}`.toLowerCase().includes(query.toLowerCase()));
      }, [purchases, query]);

      const filteredMessages = useMemo(() => {
        return messages.filter((row) => `${row.phone || ""} ${row.sequence_id || ""} ${row.provider_status || ""} ${row.text || ""}`.toLowerCase().includes(query.toLowerCase()));
      }, [messages, query]);

      const statusChart = useMemo(() => groupCount(customers, (row) => normalizeStatus(row.status)), [customers]);
      const sequenceChart = useMemo(() => groupCount(customers, (row) => row.current_sequence_id).sort((a, b) => b.value - a.value).slice(0, 8), [customers]);
      const dailySeries = useMemo(() => buildDailySeries(purchases, messages), [purchases, messages]);
      const failedMessages = messages.filter((row) => String(row.provider_status || "").toLowerCase().includes("fail") || String(row.provider_status || "").toLowerCase().includes("error")).length;

      const customerColumns = [
        { key: "phone", label: "Telefone" },
        { key: "status", label: "Status", render: (row) => <Badge tone={statusTone(row.status)}>{row.status || "-"}</Badge> },
        { key: "current_sequence_id", label: "Sequência" },
        { key: "current_step", label: "Step" },
        { key: "next_send_at", label: "Próximo envio", render: (row) => formatDate(row.next_send_at) },
        { key: "last_product_bought", label: "Último produto" },
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
        { key: "provider_status", label: "Status", render: (row) => <Badge tone={String(row.provider_status || "").toLowerCase().includes("error") ? "danger" : "muted"}>{row.provider_status || "-"}</Badge> },
        { key: "created_at", label: "Criado em", render: (row) => formatDate(row.created_at) },
        { key: "text", label: "Texto", render: (row) => <span title={row.text || ""}>{(row.text || "").slice(0, 160)}</span> }
      ];

      return (
        <div className="min-h-screen">
          <header className="border-b border-slate-200 bg-white">
            <div className="mx-auto flex max-w-[1440px] flex-col gap-4 px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <div className="text-xs font-medium uppercase tracking-[0.18em] text-slate-500">Syncronix</div>
                <h1 className="mt-1 text-3xl font-semibold tracking-normal">Marketing Automation</h1>
                <p className="mt-1 text-sm text-slate-500">Monitoramento público da automação Hotmart para WhatsApp.</p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone={error ? "danger" : refreshing ? "warning" : "success"}>
                  {error ? "Falha ao atualizar" : refreshing ? "Atualizando" : "Operacional"}
                </Badge>
                <Button onClick={() => refreshData()}>{refreshing ? "Atualizando..." : "Atualizar"}</Button>
              </div>
            </div>
          </header>

          <main className="mx-auto max-w-[1440px] space-y-5 px-6 py-6">
            {error && (
              <Card className="border-red-200 bg-red-50 text-red-900">
                <CardContent className="flex flex-col gap-1 pt-5">
                  <div className="font-medium">Não foi possível atualizar os dados.</div>
                  <div className="text-sm text-red-700">{error}</div>
                  {lastGoodData && <div className="text-xs text-red-600">Mantendo a última leitura válida na tela.</div>}
                </CardContent>
              </Card>
            )}

            <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
              <MetricCard label="Clientes" value={stats.customers_total} detail="Base monitorada" />
              <MetricCard label="Clientes ativos" value={stats.customers_active} detail="Com sequência em andamento" />
              <MetricCard label="Aguardando compra" value={stats.customers_waiting_purchase} detail="Fim da jornada atual" />
              <MetricCard label="Compras" value={stats.purchases_total} detail="Eventos registrados" />
              <MetricCard label="Mensagens" value={stats.messages_sent_total} detail={`${failedMessages} com possível falha`} />
            </section>

            <section className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
              <Card>
                <CardHeader>
                  <CardTitle>Volume diário</CardTitle>
                  <CardDescription>Compras e mensagens nos últimos registros disponíveis.</CardDescription>
                </CardHeader>
                <CardContent className="h-[280px]">
                  {loading ? <SkeletonTable /> : (
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
                <CardContent className="h-[280px]">
                  {loading ? <SkeletonTable /> : (
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie data={statusChart} dataKey="value" nameKey="name" innerRadius={58} outerRadius={94} paddingAngle={3}>
                          {statusChart.map((entry) => <Cell key={entry.name} fill={STATUS_COLORS[entry.name] || "#94a3b8"} />)}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  )}
                </CardContent>
              </Card>
            </section>

            <section className="grid gap-4 xl:grid-cols-[0.8fr_1.2fr]">
              <Card>
                <CardHeader>
                  <CardTitle>Sequências ativas</CardTitle>
                  <CardDescription>Top sequências por quantidade de clientes.</CardDescription>
                </CardHeader>
                <CardContent className="h-[300px]">
                  {loading ? <SkeletonTable /> : (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={sequenceChart} layout="vertical" margin={{ left: 8, right: 18 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                        <XAxis type="number" allowDecimals={false} stroke="#64748b" fontSize={12} />
                        <YAxis type="category" dataKey="name" width={160} stroke="#64748b" fontSize={11} />
                        <Tooltip />
                        <Bar dataKey="value" fill="#2563eb" radius={[0, 6, 6, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Registros</CardTitle>
                  <CardDescription>Clientes, compras e mensagens recentes.</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="mb-4 grid gap-3 md:grid-cols-[1fr_180px_auto]">
                    <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Buscar por telefone, produto, sequência ou status" />
                    <Select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
                      <option value="all">Todos os status</option>
                      {Array.from(new Set(customers.map((row) => row.status).filter(Boolean))).map((status) => (
                        <option key={status} value={status}>{status}</option>
                      ))}
                    </Select>
                    <div className="flex gap-2">
                      <Button active={tab === "customers"} onClick={() => setTab("customers")}>Clientes</Button>
                      <Button active={tab === "purchases"} onClick={() => setTab("purchases")}>Compras</Button>
                      <Button active={tab === "messages"} onClick={() => setTab("messages")}>Mensagens</Button>
                    </div>
                  </div>

                  {loading ? <SkeletonTable /> : tab === "customers" ? (
                    <DataTable columns={customerColumns} rows={filteredCustomers} emptyTitle="Nenhum cliente encontrado" emptyDescription="Ajuste os filtros ou aguarde novos eventos da Hotmart." />
                  ) : tab === "purchases" ? (
                    <DataTable columns={purchaseColumns} rows={filteredPurchases} emptyTitle="Nenhuma compra encontrada" emptyDescription="Compras aprovadas aparecerão aqui após o webhook." />
                  ) : (
                    <DataTable columns={messageColumns} rows={filteredMessages} emptyTitle="Nenhuma mensagem encontrada" emptyDescription="Mensagens enviadas pela automação aparecerão aqui." />
                  )}
                </CardContent>
              </Card>
            </section>

            <footer className="pb-8 text-xs text-slate-500">
              Última atualização: {formatDate(visibleData.generated_at)} · Atualização automática a cada 30 segundos
            </footer>
          </main>
        </div>
      );
    }

    ReactDOM.createRoot(document.getElementById("root")).render(<Dashboard />);
  </script>
</body>
</html>
"""
