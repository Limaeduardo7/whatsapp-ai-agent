# 🚀 Deploy no GitHub

## Status
✅ Projeto estruturado e commitado localmente
❌ Aguardando push para GitHub (token expirado)

## Opção 1: Completar via Script (Rápido)

1. Crie um token no GitHub: https://github.com/settings/tokens
   - Scopes necessários: `repo`, `workflow`

2. Execute:
   ```bash
   cd /root/clawd/projects/whatsapp-ai-agent
   ./scripts/setup-github.sh ghp_SEU_TOKEN_AQUI
   ```

## Opção 2: Manual (Via Interface Web)

1. Acesse: https://github.com/new
   - Nome: `whatsapp-ai-agent`
   - Description: Opcional
   - Público
   - NÃO inicialize com README

2. Execute no terminal:
   ```bash
   cd /root/clawd/projects/whatsapp-ai-agent
   
   # Configure remote
   git remote add origin https://github.com/Limaeduardo7/whatsapp-ai-agent.git
   git branch -M main
   
   # Push
   git push -u origin main
   ```

## Estrutura do Projeto

```
whatsapp-ai-agent/
├──📄 README.md              # Documentação principal
├──📄 LICENSE                # MIT License
├──📄 .env.example           # Template de configuração
├──📄 requirements.txt       # Dependências Python
├──📄 GITHUB_DEPLOY.md       # Este arquivo
│
├──📁 src/
│   └── main.py              # FastAPI app principal
│
├──📁 config/
│   └── evolution-bridge.service  # Systemd unit
│
├──📁 docs/
│   └── AGENT_CONFIG.md      # Configuração completa
│
├──📁 scripts/
│   ├── setup-github.sh      # Script setup GitHub
│   └── deploy.sh            # Script deploy local
│
└──📁 {data,logs}/           # Diretórios de persistência
```

## Pós-Deploy

Após push no GitHub:
1. Adicione as secrets no repo (Settings > Secrets):
   - EVOLUTION_API_KEY
   - LLM_API_KEY
   - Etc (veja .env.example)

2. Configure GitHub Actions (opcional)
3. Defina branch main como default

---

**Data de criação:** 2026-04-15
**Local:** `/root/clawd/projects/whatsapp-ai-agent`
