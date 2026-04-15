from flask import Flask, request, jsonify
import subprocess
import os
import json

app = Flask(__name__)

IGNORE_PATH = "/root/clawd/scripts/ignored_numbers.json"

def load_ignored_numbers():
    try:
        with open(IGNORE_PATH, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return set(str(x) for x in data)
    except Exception:
        pass
    return set()

@app.route('/webhook/evolution', methods=['POST'])
def receive_whatsapp():
    data = request.json
    # Lógica simplificada para extrair mensagem
    try:
        # Estrutura típica da Evolution API (pode variar conforme versão)
        message_data = data.get('data', {})
        sender = message_data.get('key', {}).get('remoteJid', '').split('@')[0]
        text = message_data.get('message', {}).get('conversation') or message_data.get('message', {}).get('extendedTextMessage', {}).get('text')

        ignored = load_ignored_numbers()
        if sender and sender not in ignored and text:
            print(f"📩 WhatsApp de {sender}: {text}")

            # Envia para o OpenClaw processar como se fosse um comando
            # Usando 'openclaw agent' para injetar a mensagem no fluxo principal
            subprocess.run(["openclaw", "agent", "--message", f"[WhatsApp] {text}", "--deliver"])

    except Exception as e:
        print(f"Erro processando webhook: {e}")

    return jsonify({"status": "received"}), 200

if __name__ == '__main__':
    print("🚀 WhatsApp Listener rodando na porta 5005...")
    app.run(host='0.0.0.0', port=5005)
