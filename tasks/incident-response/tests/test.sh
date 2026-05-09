#!/bin/bash
set -e

python3 /tests/verify.py 2>&1 | tee /logs/verifier/test-output.log
exit_code=$?

if [ ! -f /logs/verifier/reward.txt ]; then
  if [ "${exit_code}" -eq 0 ]; then
    echo 1 > /logs/verifier/reward.txt
  else
    echo 0 > /logs/verifier/reward.txt
  fi
fi

exit "${exit_code}"
