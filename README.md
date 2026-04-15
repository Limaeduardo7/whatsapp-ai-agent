# 🤖 WhatsApp AI Agent

Agente de IA para atendimento comercial no WhatsApp, integrando Evolution API com LLMs (Kimi 2.5 via NVIDIA).

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 🏗️ Arquitetura

```
┌─────────────┐      ┌──────────────┐      ┌─────────────────┐      ┌─────────────┐
│   Lead      │──────▶│  Evolution   │──────▶│   Bridge        │──────▶│   Kimi 2.5  │
│  WhatsApp   │◀──────│   API        │◀─────│  (FastAPI)      │◀─────│   (NVIDIA)  │
└─────────────┘      └──────────────┘      └─────────────────┘      └─────────────┘
                                                    │
                         ┌──────────────────────────┼──────────────────────────┐
                         │                          │                          ▼
                    ┌────▼────┐              ┌──────▼──────┐           ┌─────────────┐
                    │ SQLite  │              │    JSON     │           │   Notion    │
                    │  (n8n)  │              │  (memória)  │           │  (Pipeline) │
                    └─────────┘              └─────────────┘           └─────────────┘
```

## ✨ Funcionalidades

- 🤖 **Respostas Inteligentes** via Kimi 2.5 (Kimi K2.5 da NVIDIA)
- 💬 **Mensagens Humanizadas** — fragmentadas em balões curtos
- 🔊 **STT/Vision** — transcrição de áudio e análise de imagens via Gemini
- 📄 **PDF de Orçamento** — geração automática com FPDF
- 🗂️ **Pipeline Notion** — integração com CRM
- ⏸️ **Pausa Inteligente** — para quando humano intervém
- 🎯 **Detecção de Intenção** — classifica leads automaticamente
- 🔄 **Follow-up Automático** — para leads sem resposta

## 🚀 Quick Start

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/whatsapp-ai-agent.git
cd whatsapp-ai-agent
```

### 2. Configure o ambiente

```bash
# Crie e env ative ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instale dependências
pip install -r requirements.txt

# Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais
```

### 3. Configure a Evolution API

Siga a documentação da [Evolution API](https://github.com/EvolutionAPI/evolution-api) para deploy.

### 4. Configure o webhook

```bash
curl -X POST "$EVOLUTION_BASE_URL/webhook/set" \
  -H "Content-Type: application/json" \
  -H "apikey: $EVOLUTION_API_KEY" \
  -d '{
    "webhook": {
      "url": "http://seu-servidor:8001/evolution/webhook",
      "events": ["MESSAGES_UPSERT"]
    }
  }'
```

### 5. Execute

```bash
# Desenvolvimento
python -m uvicorn src.main:app --reload --port 8001

# Produção
python -m uvicorn src.main:app --host 0.0.0.0 --port 8001
```

## ⚙️ Configuração via Systemd

```bash
sudo cp config/evolution-bridge.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable evolution-bridge.service
sudo systemctl start evolution-bridge.service
```

## 📁 Estrutura do Projeto

```
whatsapp-ai-agent/
├── src/
│   ├── main.py              # FastAPI app principal
│   ├── handlers/            # Handlers de mensagens
│   ├── services/            # Serviços (LLM, Evolution, etc)
│   └── utils/               # Utilitários
├── config/
│   └── evolution-bridge.service  # Systemd unit
├── docs/
│   └── AGENT_CONFIG.md      # Configuração completa
├── data/                    # Persistência (criado automaticamente)
├── logs/                    # Logs (criado automaticamente)
├── .env.example             # Template de variáveis
├── requirements.txt         # Dependências Python
└── README.md                # Este arquivo
```

## 🛠️ Troubleshooting

### Bot não responde

```bash
# Verificar status
systemctl status evolution-bridge.service

# Verificar logs
journalctl -u evolution-bridge.service -f

# Verificar se webhooks chegam
tail -f logs/app.log | grep webhook
```

### Redis disconnected

```bash
# Reiniciar serviços Docker
docker service update --force automacoes_evolution-api-redis
docker service update --force automacoes_evolution-api
```

## 📚 Documentação

- [Configuração Completa](docs/AGENT_CONFIG.md)
- [API Evolution](https://docs.evolution-api.com/)
- [Kimi 2.5 (NVIDIA)](https://build.nvidia.com/moonshotai/kimi-k2-5)

## 📝 Licença

MIT License — veja [LICENSE](LICENSE) para detalhes.

---

<p align="center">Desenvolvido com 🦞 pela Meraki Group</p>
