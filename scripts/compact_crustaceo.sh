#!/bin/bash
# Compacta o contexto do agente crustaceo quando estiver acima do threshold.
# Mantém: header de sessão + último compaction summary + últimas 60 mensagens.
# Reinicia o gateway para recarregar do disco.

set -euo pipefail

SESSION_JSON="/root/.openclaw/agents/crustaceo/sessions/sessions.json"
THRESHOLD=240000   # ~88% de 272k — compacta antes de travar
LOG_TAG="compact-crustaceo"

log() { echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') [$LOG_TAG] $*"; }

# --- Ler estado atual ---
read -r TOKENS SESSION_FILE < <(python3 - "$SESSION_JSON" <<'PYEOF'
import json, sys
path = sys.argv[1]
with open(path) as f:
    d = json.load(f)
s = d.get("agent:crustaceo:main", {})
tokens = s.get("contextTokens", 0) or 0
sf = s.get("sessionFile", "")
print(tokens, sf)
PYEOF
)

log "Contexto atual: ${TOKENS} tokens (threshold: ${THRESHOLD})"

if [ "${TOKENS}" -lt "${THRESHOLD}" ]; then
    log "OK — nenhuma ação necessária."
    exit 0
fi

log "ALTO! Iniciando compactação..."

if [ -z "${SESSION_FILE}" ] || [ ! -f "${SESSION_FILE}" ]; then
    log "ERRO: session file não encontrado: '${SESSION_FILE}'"
    exit 1
fi

log "Session file: ${SESSION_FILE} ($(wc -l < "${SESSION_FILE}") linhas)"

# --- Compactar via Python ---
python3 - "${SESSION_FILE}" "${SESSION_JSON}" <<'PYEOF'
import json, shutil, sys
from datetime import datetime, timezone

session_file = sys.argv[1]
sessions_json = sys.argv[2]
KEEP_MESSAGES = 60   # últimas N mensagens a preservar

# Backup datado
ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
backup = session_file + f".bak.{ts}"
shutil.copy2(session_file, backup)
print(f"  Backup: {backup}")

# Ler todas as linhas
with open(session_file) as f:
    lines = [json.loads(l) for l in f if l.strip()]

total_before = len(lines)

# Separar por tipo
headers    = [l for l in lines if l.get("type") in ("session", "model_change", "thinking_level_change")]
compacts   = [l for l in lines if l.get("type") == "compaction"]
customs    = [l for l in lines if l.get("type") == "custom"]
messages   = [l for l in lines if l.get("type") == "message"]

# Manter último compaction + últimas N mensagens
keep = headers + compacts[-1:] + messages[-KEEP_MESSAGES:]

with open(session_file, "w") as f:
    for item in keep:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

print(f"  Linhas: {total_before} → {len(keep)} (compactions mantidos: {len(compacts[-1:])}, msgs mantidas: {min(len(messages), KEEP_MESSAGES)})")

# Resetar metadata em sessions.json
with open(sessions_json) as f:
    d = json.load(f)

if "agent:crustaceo:main" in d:
    d["agent:crustaceo:main"]["contextTokens"] = 0
    d["agent:crustaceo:main"]["compactionCount"] = 0
    d["agent:crustaceo:main"]["inputTokens"] = 0
    d["agent:crustaceo:main"]["outputTokens"] = 0
    d["agent:crustaceo:main"]["totalTokens"] = 0

with open(sessions_json, "w") as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

print("  sessions.json atualizado.")
PYEOF

log "Compactação concluída. Reiniciando gateway..."

# Reiniciar o gateway de usuário (carrega sessões do disco)
XDG_RUNTIME_DIR="/run/user/0" systemctl --user restart openclaw-gateway.service

log "Gateway reiniciado com sucesso."
