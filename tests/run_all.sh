#!/bin/bash
# Runs all browser tests against docs/ (build first: python3 tools/build.py)
# Needs: pip install playwright numpy pillow && python3 -m playwright install chromium
cd "$(dirname "$0")"
python3 serve.py 8899 ../docs >/dev/null 2>&1 &
SRV=$!; sleep 1
fail=0
for t in test_*.py; do
  printf "%-24s " "$t"; out=$(python3 "$t" 2>&1 | tail -1); echo "$out"
  case "$out" in *passed*) n=${out%%/*}; m=${out#*/}; m=${m%% *}; [ "$n" != "$m" ] && fail=1;; *) fail=1;; esac
done
kill $SRV
exit $fail
