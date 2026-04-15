#!/usr/bin/env python3
import json, os, sys
QUEUE = "/root/clawd/scripts/notify_queue.jsonl"

if not os.path.exists(QUEUE):
    sys.exit(0)

with open(QUEUE, "r") as f:
    lines = [l.strip() for l in f if l.strip()]

if not lines:
    sys.exit(0)

# Clear queue
open(QUEUE, "w").close()

for line in lines:
    try:
        print(line)
    except Exception:
        pass
