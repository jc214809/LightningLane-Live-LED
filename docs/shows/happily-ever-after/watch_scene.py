"""Build the /watch question and padded video window for a WATCH.md scene (used by watch-scenes.sh).

    python3 watch_scene.py 4.1 question.txt   ->  prints "<start> <end> <title>", writes the question
"""
import re, sys
num = sys.argv[1]
s = open("docs/shows/happily-ever-after/WATCH.md").read()
base = s[s.index("## Base prompt"):s.index("## The show")]
prompt = "\n".join(l[2:] if l.startswith("> ") else ("" if l == ">" else None) for l in base.splitlines()
                   if l.startswith(">"))
sec = re.search(rf"^### {re.escape(num)} (.+?)$(.*?)(?=^### |^## |\Z)", s, re.M | re.S)
title, body = sec.group(1), sec.group(2)
v0, v1 = re.search(r"`--start (\d+:\d+) --end (\d+:\d+)`", body).groups()
ours = re.search(r"\*\*Our score now:\*\* (.+)", body).group(1).strip()
notes = re.search(r"\*\*Your notes for this scene:\*\*\n\n(.*?)\n\n\*\*Answers", body, re.S).group(1)
notes = "\n".join(l[2:] if l.startswith("> ") else l for l in notes.splitlines()).strip()
if notes.startswith("_(add what"):
    notes = ""
def sec_of(t):
    m, x = t.split(":"); return int(m) * 60 + int(x)
def fmt(x):
    return f"{x // 60}:{x % 60:02d}"
pad0, pad1 = fmt(max(0, sec_of(v0) - 3)), fmt(sec_of(v1) + 3)
q = prompt.replace("{start}", v0).replace("{end}", v1).replace("{title}", title).replace("{ours}", ours)
if notes:
    q += "\n\nAlso, for this part specifically:\n" + notes
open(sys.argv[2], "w").write(q)
print(pad0, pad1, title)
