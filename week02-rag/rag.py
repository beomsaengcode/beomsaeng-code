"""회사 문서 읽는 AI (RAG)를 50줄로: 자르기 → 숫자로 바꾸기 → 가까운 조각 찾기 → 붙여서 묻기.

숫자로 바꾸기(임베딩): EMBED=ollama 이면 bge-m3 (내 PC, 무료), 비우면 글자 묶음 해시 (설치 없이 돌아감, 정확도 낮음)
"""

import json
import os
import re
import urllib.request

import numpy as np

HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")


def chunk(text, size=None, overlap=0):
    """size가 없으면 '# 제목' 단위로, 있으면 글자 수로 자른다 (overlap만큼 앞뒤를 겹친다)."""
    if size is None:
        return [s.strip() for s in re.split(r"\n(?=# )", text) if s.strip()]
    t = text.replace("\n", " ")
    return [t[i : i + size] for i in range(0, len(t), size - overlap)]


def embed(texts):
    """글 여러 개를 길이 1짜리 벡터로 바꾼다. 뜻이 비슷하면 벡터 방향도 비슷하다."""
    if os.environ.get("EMBED") == "ollama":
        body = json.dumps({"model": "bge-m3", "input": texts}).encode()
        req = urllib.request.Request(f"{HOST}/api/embed", body, {"Content-Type": "application/json"})
        v = np.array(json.loads(urllib.request.urlopen(req, timeout=300).read())["embeddings"])
    else:
        v = np.zeros((len(texts), 4096))
        for i, s in enumerate(texts):
            s = re.sub(r"\s", "", s)
            for j in range(len(s) - 1):
                v[i, int.from_bytes(s[j : j + 2].encode(), "little") % 4096] += 1
    return v / (np.linalg.norm(v, axis=1, keepdims=True) + 1e-9)


class Index:
    """조각과 벡터를 들고 있다가, 질문과 가장 가까운 조각 k개를 돌려준다."""

    def __init__(self, chunks):
        self.chunks, self.vecs = chunks, embed(chunks)

    def search(self, question, k=2):
        scores = self.vecs @ embed([question])[0]  # 코사인 유사도 (벡터 길이가 1이라 곱하기만)
        return [self.chunks[i] for i in np.argsort(-scores)[:k]]


def ask(llm, question, context=None):
    """context(찾은 조각)가 있으면 붙여서, 없으면 질문만 보낸다."""
    if context:
        prompt = "아래 규정만 보고 한 문장으로 답해. 규정에 없으면 '모름'.\n\n" + "\n---\n".join(context)
        prompt += f"\n\n질문: {question}"
    else:
        prompt = f"하늘몰 쇼핑몰 상담원으로서 한 문장으로 답해.\n질문: {question}"
    return llm.chat([{"role": "user", "content": prompt}]).text.strip()
