"""01. 질문 하나: 찾은 조각을 보여 주고, 문서 없이 vs 붙여서 답을 나란히 본다.

실행: EMBED=ollama LLM_PROVIDER=ollama python 01_ask.py "골드 회원 기준이 얼마예요?"
"""

import sys
from pathlib import Path

from _setup import llm
from rag import Index, ask, chunk

q = sys.argv[1] if len(sys.argv) > 1 else "골드 회원 기준이 얼마예요?"
index = Index(chunk((Path(__file__).parent / "docs/haneul_policy.md").read_text(encoding="utf-8")))
found = index.search(q)
print("[찾은 조각]\n" + "\n---\n".join(c[:200] for c in found))
print("\n[문서 없이]", ask(llm, q))
print("[문서 붙여서]", ask(llm, q, found))
