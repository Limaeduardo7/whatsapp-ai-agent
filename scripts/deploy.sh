#!/bin/bash
# Deploy local do WhatsApp AI Agent com systemd.
# Uso: sudo ./scripts/deploy.sh

set -euo pipefail

echo "WhatsApp AI Agent - Deploy"

if [ ! -f "src/main.py" ]; then
    echo "Erro: execute este script da raiz do projeto"
    exit 1
fi

if [ ! -f ".env" ]; then
    echo "Erro: .env nao encontrado. Copie .env.example para .env e configure as credenciais."
    exit 1
fi

mkdir -p data logs

if ! id -u whatsapp-agent >/dev/null 2>&1; then
    useradd --system --no-create-home --shell /usr/sbin/nologin whatsapp-agent
fi

chown -R whatsapp-agent:whatsapp-agent data logs

python3 -m pip install -q -r requirements.txt

cp config/evolution-bridge.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable evolution-bridge.service
systemctl restart evolution-bridge.service

sleep 2

if systemctl is-active --quiet evolution-bridge.service; then
    echo "Servico ativo."
    systemctl status evolution-bridge.service --no-pager
else
    echo "Falha ao iniciar servico. Logs:"
    journalctl -u evolution-bridge.service -n 50 --no-pager
    exit 1
fi
