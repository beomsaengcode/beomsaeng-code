# 2주차 · RAG 기본: 회사 문서 읽는 AI

> 범생코드 AI 엔지니어 10주 과정 · 2주차
> 영상과 글: [beomsaengcode.github.io](https://beomsaengcode.github.io)

## 이번 주에 알게 되는 것

```
 회사 문서 ─자르기─▶ 조각들 ─임베딩─▶ 벡터들 ──┐
                                               ├─ 가까운 조각 2개 ─▶ 질문에 붙여서 ─▶ LLM ─▶ 답
 질문 ─────────────────────임베딩─▶ 벡터 ──────┘   (코사인 유사도)
```

1. **자르기 (청킹):** 글자 수로 자를지, 제목 단위로 자를지 (`chunk`)
2. **임베딩:** 글을 뜻이 담긴 숫자 벡터로 (`embed`, bge-m3)
3. **검색:** 질문 벡터와 가장 가까운 조각 찾기 (`Index.search`)
4. **붙여서 묻기:** 찾은 조각만 보고 답하게 하기 (`ask`)

핵심 코드는 `rag.py` 하나, 설명 빼고 50줄 안팎이에요. 벡터 DB(FAISS 등)는 조각이 수만 개가 되면 씁니다. 지금은 numpy 곱하기 한 번으로 충분해요.

## 직접 잰 결과 (2026-11-21, 내 PC, 전부 무료)

가상 쇼핑몰 '하늘몰' 규정(`docs/haneul_policy.md`), 같은 질문 10개(`questions.json`), 답 모델 qwen2.5:1.5b, 임베딩 bge-m3, 조각 2개를 붙임.

| 방식 | 맞힌 질문 |
|---|---|
| 문서 없이 | 0 / 10 |
| 100자로 잘라 붙이기 | 4 / 10 |
| 제목 단위로 잘라 붙이기 | 8 / 10 |

- 문서 없이 물으면 그럴듯하게 지어내요. "골드 회원 기준?" → "100만원입니다" (규정은 30만 원)
- 채점: 답에 정답 낱말이 모두 들어 있어야 맞음 (엄하게 셈). 질문별 답과 붙인 조각은 `results.json`에 있어요.
- `chunking/`은 임베딩 없이 자르는 위치만 비교한 수요일 쇼츠 측정이에요 (조각 1개, 100자 2/10 vs 제목 7/10).

## 실행

```bash
pip install numpy requests
ollama pull qwen2.5:1.5b && ollama pull bge-m3

# 질문 하나: 찾은 조각, 문서 없이 답 vs 붙여서 답
EMBED=ollama LLM_PROVIDER=ollama python 01_ask.py "골드 회원 기준이 얼마예요?"

# 10개 비교 → results.json
EMBED=ollama LLM_PROVIDER=ollama python 02_compare.py

# 모델 없이 도는 테스트
python -m pytest tests
```

`EMBED`를 비우면 설치 없이 도는 글자 묶음 방식으로 검색해요 (테스트용, 정확도 낮음).

## 연습 문제

1. `chunk(DOC, 100, overlap=30)`으로 겹치기를 넣으면 100자 결과가 몇 개로 바뀌나요?
2. `search(q, k=1)`과 `k=4`를 비교해 보세요. 조각이 많을수록 늘 좋아지나요?
3. 틀린 질문 하나를 골라 `results.json`의 `context`부터 보세요. 검색이 틀렸나요, 답이 틀렸나요?
