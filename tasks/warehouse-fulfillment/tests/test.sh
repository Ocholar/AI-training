#!/bin/bash
set -euo pipefail
mkdir -p /logs/verifier
pip install --quiet openai==1.76.0
python3 /tests/judge.py \
  --agent-output /logs/agent/output.json \
  --oracle /tests/oracle.json \
  --reward-out /logs/verifier/reward.json
