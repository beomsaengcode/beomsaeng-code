"""장애 일지 #3 측정: 문서를 100자씩 자를 때 vs 항목(#) 단위로 나눌 때, 같은 질문 10개를 몇 개 맞히나.
검색 = 글자 두 개 묶음 겹침 점수로 1등 조각 하나만 붙인다 (임베딩 없이도 '자르는 위치' 문제만 보이게).
답 = Ollama qwen2.5:1.5b (무료, 내 PC). 채점 = 답에 정답 낱말이 다 들어 있으면 맞음.
python -X utf8 measure.py  → measure.json"""
import json
import re
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
DOC = (HERE / "policy.txt").read_text(encoding="utf-8")
Q = [("신선식품은 언제 환불돼요?", ["상하", "24시간"]),
     ("단순 변심 반품 배송비 얼마예요?", ["6,000"]),
     ("제주도 배송은 며칠 걸려요?", ["2~5일"]),
     ("오후 3시에 주문하면 언제 보내요?", ["다음 영업일"]),
     ("상담원은 몇 시까지 상담해요?", ["6시"]),
     ("쿠폰 두 장 같이 써도 돼요?", ["하나"]),
     ("적립금은 언제 사라져요?", ["12개월"]),
     ("골드 회원 기준이 얼마예요?", ["30만"]),
     ("할부는 얼마 이상부터 돼요?", ["5만"]),
     ("계좌이체는 언제까지 입금해야 해요?", ["48시간"])]


def fixed(text, n=100):
    t = text.replace("\n", " ")
    return [t[i:i + n] for i in range(0, len(t), n)]


def by_section(text):
    return [s.strip() for s in re.split(r"\n(?=# )", text) if s.strip()]


def grams(s):
    s = re.sub(r"\s", "", s)
    return {s[i:i + 2] for i in range(len(s) - 1)}


def top(chunks, q):
    g = grams(q)
    return max(chunks, key=lambda c: len(g & grams(c)))


def ask(ctx, q):
    body = {"model": "qwen2.5:1.5b", "stream": False, "options": {"temperature": 0},
            "prompt": f"아래 규정만 보고 한 문장으로 답해. 규정에 없으면 '모름'.\n규정: {ctx}\n질문: {q}\n답:"}
    req = urllib.request.Request("http://127.0.0.1:11434/api/generate", json.dumps(body).encode(), {"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=120).read())["response"].strip()


out = {}
for name, chunks in (("100자", fixed(DOC)), ("항목", by_section(DOC))):
    rows = []
    for q, keys in Q:
        ctx = top(chunks, q)
        a = ask(ctx, q)
        rows.append({"q": q, "chunk": ctx, "answer": a, "ok": all(k in a for k in keys), "chunk_has": all(k in ctx for k in keys)})
    out[name] = {"chunks": len(chunks), "ok": sum(r["ok"] for r in rows), "chunk_has": sum(r["chunk_has"] for r in rows), "rows": rows}
    print(name, "조각", len(chunks), "맞힘", out[name]["ok"], "/ 10 · 정답이 조각에 온전히 있음", out[name]["chunk_has"])
(HERE / "measure.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
