# Notion GUI

Painel web para orquestrar agentes (squad), tarefas e logs do Notion.

## ✅ Pré‑requisitos
- **Node.js 20+** (recomendado 22.x)
- API do Notion rodando (porta **8001** por padrão)

## 🔧 Configuração
Crie um arquivo `.env` (ou copie o exemplo):

```bash
cp .env.example .env
```

Edite os valores conforme o ambiente:

```env
VITE_API_BASE=http://SEU_IP_OU_HOST:8001
# opcional: define URL completa do endpoint
# VITE_API_URL=http://SEU_IP_OU_HOST:8001/api/agents
```

## ▶️ Rodar em desenvolvimento

```bash
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

Acesse: `http://SEU_IP:5173`

## 🏗️ Build para produção (preview)

```bash
npm install
npm run build
npm run preview -- --host 0.0.0.0 --port 5173
```

## 🧰 Systemd (opcional)
Exemplo de serviço (ajuste caminhos se necessário):

```
[Unit]
Description=Notion GUI
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/clawd/notion-gui
ExecStart=/root/.nvm/versions/node/v22.22.0/bin/npm run preview -- --host 0.0.0.0 --port 5173
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Habilitar:
```bash
sudo systemctl daemon-reload
sudo systemctl enable notion-gui
sudo systemctl restart notion-gui
```

## 📌 Notas
- O front espera a API responder em `VITE_API_BASE`.
- Para ambientes com domínio, use o host completo (ex: `https://mc.suaempresa.com`).
