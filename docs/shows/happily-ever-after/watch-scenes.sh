#!/bin/bash
# Watch WATCH.md scenes with the /watch skill (Gemini) and save each answer under its scene.
#   bash docs/shows/happily-ever-after/watch-scenes.sh 4.1 4.2 4.3      (run from the repo root)
# Each scene's question is the base prompt plus its notes (watch_scene.py); the video window runs 3 s
# past each end of the scene. Gemini's free tier is often busy (503) and has a daily quota (429): each
# scene is retried on both Flash models, and a scene that still fails is reported and left for later.
DIR="$(cd "$(dirname "$0")" && pwd)"
WORK="${WATCH_WORK:-$(mktemp -d)}"
WATCH="${WATCH_SCRIPT:-$(ls -d "$HOME"/.claude/plugins/cache/claude-video/watch/*/skills/watch/scripts/watch.py 2>/dev/null | tail -1)}"
URL="https://www.youtube.com/watch?v=-LncKUxWMsQ"
[ -f "$WATCH" ] || { echo "the /watch skill's watch.py isn't installed (set WATCH_SCRIPT)"; exit 1; }
for n in "$@"; do
  read P0 P1 TITLE < <(python3 "$DIR/watch_scene.py" "$n" "$WORK/q-$n.txt") || { echo "no scene $n"; continue; }
  echo "== $n $TITLE (video $P0-$P1)"
  ok=
  for attempt in 1 2 3 4 5 6; do
    for model in gemini-3.8-flash gemini-3.7-flash; do
      # The Mac's python.org Python has no CA bundle of its own.
      SSL_CERT_FILE=/etc/ssl/cert.pem WATCH_GEMINI_MODEL=$model python3 "$WATCH" "$URL" \
        --start "$P0" --end "$P1" --question "$(cat "$WORK/q-$n.txt")" > "$WORK/a-$n.md" 2>"$WORK/a-$n.err"
      if grep -q "## Answer (from Gemini)" "$WORK/a-$n.md"; then ok=1; break 2; fi
      echo "  attempt $attempt $model: $(grep -m1 -o 'HTTP [0-9]*' "$WORK/a-$n.md")"
      sleep 20
    done
  done
  if [ -n "$ok" ]; then python3 "$DIR/save_answer.py" "$n" "$WORK/a-$n.md" "$P0-$P1"; else echo "FAILED $n (see $WORK/a-$n.md)"; fi
done
