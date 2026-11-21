"""02. 같은 질문 10개로 비교: 문서 없이 / 100자로 잘라 붙이기 / 제목 단위로 잘라 붙이기.

실행: EMBED=ollama LLM_PROVIDER=ollama python 02_compare.py   → results.json
채점: 답에 정답 낱말이 모두 들어 있어야 맞음 (엄하게 셈).
"""

import json
from pathlib import Path

from _setup import llm
from rag import Index, ask, chunk

HERE = Path(__file__).parent
if llm.name == "offline":
    raise SystemExit("비교는 실제 모델이 필요해요: LLM_PROVIDER=ollama (무료) 또는 API 키를 쓰세요.")
DOC = (HERE / "docs/haneul_policy.md").read_text(encoding="utf-8")
QUESTIONS = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))
MODES = {"문서 없이": None, "100자로 자르기": Index(chunk(DOC, 100)), "제목 단위로 자르기": Index(chunk(DOC))}

results = {}
for name, index in MODES.items():
    rows = []
    for q in QUESTIONS:
        ctx = index.search(q["q"]) if index else None
        a = ask(llm, q["q"], ctx)
        rows.append({"q": q["q"], "answer": a, "ok": all(k in a for k in q["keys"]), "context": ctx})
    results[name] = {"ok": sum(r["ok"] for r in rows), "rows": rows}
    print(f"{name:12} {results[name]['ok']:2} / {len(QUESTIONS)}")
out = {"provider": llm.name, "model": llm.model, "results": results}
(HERE / "results.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
