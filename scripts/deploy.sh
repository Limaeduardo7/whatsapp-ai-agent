#!/bin/bash
# Script de deploy do WhatsApp AI Agent
# Uso: sudo ./scripts/deploy.sh

set -e

echo "🤖 WhatsApp AI Agent - Deploy"
echo "================================"

# Verificar se está no diretório correto
if [ ! -f "src/main.py" ]; then
    echo "❌ Erro: Execute este script da raiz do projeto"
    exit 1
fi

# Criar diretórios de dados
mkdir -p data logs

echo "📦 Instalando dependências..."
pip install -q -r requirements.txt

echo "🔧 Configurando serviço systemd..."
if [ -f ".env" ]; then
    sudo cp config/evolution-bridge.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable evolution-bridge.service
    echo "✅ Serviço configurado"
else
    echo "⚠️ .env não encontrado. Copie .env.example para .env e configure"
    exit 1
fi

echo "🚀 Iniciando serviço..."
sudo systemctl restart evolution-bridge.service

# Aguardar inicialização
sleep 2

# Verificar status
if systemctl is-active --quiet evolution-bridge.service; then
    echo "✅ Serviço ativo!"
    systemctl status evolution-bridge.service --no-pager
    echo ""
    echo "📋 Comandos úteis:"
    echo "  Logs: sudo journalctl -u evolution-bridge.service -f"
    echo "  Status: sudo systemctl status evolution-bridge.service"
    echo "  Restart: sudo systemctl restart evolution-bridge.service"
else
    echo "❌ Falha ao iniciar serviço"
    echo "Verifique os logs: sudo journalctl -u evolution-bridge.service -n 50"
    exit 1
fi
