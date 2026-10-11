#!/bin/bash
# Re-run Gemini (the /watch plugin) over the show video in overlapping chunks, retrying each
# chunk until it answers. A whole-video request dies at Google's ~10 min deadline (HTTP 504);
# ~5.5 min chunks finish in 1-3 min. Free-tier keys only get the Flash models, so it alternates
# them through "high demand" 503s. Run from the repo root:
#   bash docs/shows/happily-ever-after/watch-chunks.sh [out_dir]
# The python.org Python has no CA bundle, hence SSL_CERT_FILE.
WATCH=${WATCH:-$(ls -d ~/.claude/plugins/cache/claude-video/watch/*/skills/watch/scripts/watch.py | tail -1)}
URL="https://www.youtube.com/watch?v=-LncKUxWMsQ"
HERE=$(dirname "$0")
OUT=${1:-$HERE}
QUESTION=$(cat "$HERE/gemini-question.txt")
STARTS=(00:00 05:00 10:00 15:00)
ENDS=(05:30 10:30 15:30 19:02)
MODELS=(gemini-3.7-flash gemini-3.8-flash)
MAX_TRIES=${MAX_TRIES:-20}
for idx in "${!STARTS[@]}"; do
  a=${STARTS[$idx]}; b=${ENDS[$idx]}
  out="$OUT/gemini-$((idx + 1))-${a//:/}-${b//:/}.md"
  for try in $(seq 1 "$MAX_TRIES"); do
    m=${MODELS[$((try % 2))]}
    echo "chunk $((idx + 1)) ($a-$b) try $try with $m $(date +%T)"
    if SSL_CERT_FILE=/etc/ssl/cert.pem WATCH_GEMINI_MODEL=$m WATCH_GEMINI_TIMEOUT=900 \
        python3 "$WATCH" "$URL" --start "$a" --end "$b" --question "$QUESTION" > "$out.tmp" 2>&1; then
      sed '1{/^\[watch\]/d;}' "$out.tmp" > "$out" && rm "$out.tmp"
      echo "  ok -> $out"
      continue 2
    fi
    echo "  failed: $(grep -m1 -e '^- Gemini' -e 'error:' "$out.tmp" | cut -c1-140)"
    sleep 180
  done
  echo "chunk $((idx + 1)) gave up after $MAX_TRIES tries"; exit 1
done
