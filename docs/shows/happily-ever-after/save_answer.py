"""Put a /watch report's answer at the top of a WATCH.md scene's Answers (used by watch-scenes.sh).

    python3 save_answer.py 4.1 report.md 5:10-5:38
"""
import re, sys, datetime
num, path, window = sys.argv[1], sys.argv[2], sys.argv[3]
report = open(path).read()
model = re.search(r"\*\*Engine:\*\* (\S+)", report).group(1)
answer = report.split("## Answer (from Gemini)", 1)[1]
answer = re.sub(r"^_These are Gemini's observations.*?_\n", "", answer.strip(), flags=re.M | re.S).strip()
# Gemini's headings would join the page's outline: make them bold lines instead.
answer = re.sub(r"^#{1,6}\s*(.+?)\s*$", lambda m: "**" + m.group(1).strip("* ") + "**", answer, flags=re.M)
answer = re.sub(r"^---\s*$\n?", "", answer, flags=re.M).strip()
answer = re.sub(r"\n{3,}", "\n\n", answer)
p = "docs/shows/happily-ever-after/WATCH.md"; s = open(p).read()
sec = re.search(rf"^### {re.escape(num)} .+?$(.*?)(?=^### |^## |\Z)", s, re.M | re.S)
body = sec.group(1)
notes = re.search(r"\*\*Your notes for this scene:\*\*\n\n(.*?)\n\n\*\*Answers", body, re.S).group(1).strip()
noted = "none" if notes.startswith("> _(add what") else "as in the notes above, at the time"
entry = (f"<details><summary><b>{datetime.date.today().isoformat()}</b> · {model} · video {window} · "
         f"notes: {noted}</summary>\n\n{answer}\n\n</details>\n")
head = "**Answers** (newest first):\n\n"
i = body.index(head) + len(head)
rest = body[i:]
rest = rest.replace("_None yet._\n", "", 1) if rest.lstrip().startswith("_None yet._") else rest
body = body[:i] + entry + ("\n" + rest.lstrip("\n") if rest.strip() else "\n")
s = s[:sec.start(1)] + body + s[sec.end(1):]
open(p, "w").write(s)
print("saved", num, model)
