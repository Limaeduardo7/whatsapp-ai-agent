#!/bin/bash
# Script para configurar push no GitHub
# Uso: ./scripts/setup-github.sh <seu-token-github>

set -e

TOKEN=$1
REPO_NAME="whatsapp-ai-agent"
REPO_DESC="Agente de IA para atendimento comercial no WhatsApp com Evolution API e Kimi 2.5"

if [ -z "$TOKEN" ]; then
    echo "❌ Erro: Forneça seu token do GitHub"
    echo "Uso: $0 ghp_seu_token_aqui"
    exit 1
fi

echo "🔄 Criando repositório no GitHub..."

# Criar repo via API API
RESPONSE=$(curl -s -X POST https://api.github.com/user/repos \
  -H "Authorization: token ${TOKEN}" \
  -H "Accept: application/vnd.github.v3+json" \
  -d "{\"name\":\"${REPO_NAME}\",\"description\":\"${REPO_DESC}\",\"private\":false,\"auto_init\":false}")

# Verificar se deu certo
if echo "$RESPONSE" | grep -q '"clone_url"'; then
    CLONE_URL=$(echo "$RESPONSE" | grep -o '"clone_url": "[^"]*"' | cut -d'"' -f4)
    HTML_URL=$(echo "$RESPONSE" | grep -o '"html_url": "[^"]*"' | cut -d'"' -f4)
    
    echo "✅ Repositório criado: $HTML_URL"
    
    # Adicionar remote e push
    git remote add origin "$CLONE_URL"
    git branch -M main
    
    # Configurar token para push
    git config credential.helper store
    echo "https://Limaeduardo7:${TOKEN}@github.com" > ~/.git-credentials
    
    echo "🚀 Fazendo push..."
    git push -u origin main
    
    echo "✅ Deploy completo!"
    echo "📁 Repositório: $HTML_URL"
else
    echo "❌ Erro ao criar repositório:"
    echo "$RESPONSE"
    exit 1
fi
