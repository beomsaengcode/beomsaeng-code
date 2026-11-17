# 1주차 · LLM API 기초 (+ API의 이해)

> 범생코드 AI 엔지니어 10주 과정 · 1주차
> 영상과 글: [beomsaengcode.github.io](https://beomsaengcode.github.io)

## 이번 주에 알게 되는 것

```
 내 코드 ──HTTP POST /v1/messages──▶ API ──▶ 모델
   │  헤더: x-api-key · anthropic-version          │
   │  본문: model · max_tokens · messages           │
   ◀──────── 응답: content[] · stop_reason · usage ─┘
```

1. **API 호출의 모양:** 주소, 헤더, 본문, 응답 (`llm/` 안의 공급자 코드)
2. **응답 읽기:** 내용 블록, 멈춘 이유(`stop_reason`), 토큰 사용량(`usage`) (`01`)
3. **API는 기억이 없다:** 대화가 길어지면 매번 전부 다시 보내서 입력 토큰이 쌓인다 (`02`)
4. **비용은 토큰으로 매긴다:** 출력이 입력보다 비싸고(예: claude-opus-5-5는 5배), 한국어와 영어는 토큰 수가 다르다 (`03`)
5. **토큰·비용 계산기:** 턴마다 입력 토큰이 계단처럼 쌓이는 걸 표로 보고, 자르기·요약으로 얼마나 줄어드는지 비교한다 (`04`)
6. **에러 처리:** 429·500·529는 지수 백오프 + 지터로 다시, 400·401·403·404·413은 고쳐서. 가짜 서버로 돌린다 (`05`)

## 실행

```bash
pip install -r ../requirements.txt
# 공급자는 키가 있는 쪽을 자동으로 고르고, 없으면 오프라인(예시 응답)으로 돌아요.
export OPENAI_API_KEY=...           # 또는 직접 지정: LLM_PROVIDER=openai|ollama|offline, LLM_MODEL=...
# 무료 로컬: Ollama 설치 → ollama pull qwen2.5:1.5b → LLM_PROVIDER=ollama

python 01_first_request.py "HTTP 403이랑 404 차이를 한 줄로"
python 02_stream_chat.py
python 03_tokens_ko_en.py
python 04_cost_calc.py --compare --price claude-opus-5-5   # 로컬 모델 토큰을 유료 단가로 어림
python 05_retry.py                                          # 키·인터넷 필요 없음
python 06_tokens_offline.py                                 # 키 없이 한국어/영어 토큰 세기 (pip install tiktoken)
```

- 주차 코드는 저장소 루트의 `llm/` 공통 인터페이스(`chat`, `stream`, `count_tokens`)만 불러요. 어느 회사 모델인지 몰라도 돼요.
- 공급자를 바꿔도 결과는 같은 모양(`Reply`: 답, 멈춘 이유, 토큰)으로 와요. 멈춘 이유 이름도 `end`·`length`·`refusal`로 통일했어요.
- 키 없이도 `fixtures/`의 **예시 응답**으로 흐름을 따라갈 수 있어요. 예시 값은 실측이 아니에요.
- 작은 로컬 모델(qwen2.5:1.5b)은 그럴듯하게 **틀린 답**을 내기도 해요. 왜 평가(7주차)가 필요한지 직접 확인해 보세요.
- 가격은 `llm/prices.py`에 확인한 날짜와 함께 넣어요. 표에 없는 모델은 비용 대신 토큰만 보여 줘요.

## 실습

1. `01`에 `system` 프롬프트를 넣어 "항상 한 줄로만"을 지키게 해 보세요. 출력 토큰이 얼마나 줄어드나요?
2. `02`에서 다섯 번 주고받은 뒤, 마지막 요청의 입력 토큰을 첫 요청과 비교해 보세요. 왜 늘었나요?
3. `03`에 직접 문장 3쌍을 넣어 보세요. 코드 블록이나 숫자가 많은 문장은 어떤가요?
4. `04 --compare`에서 요약이 오히려 비싸게 나오나요? 대화를 30턴으로 늘리면 어떻게 되나요?
5. `05`의 `MAX_RETRIES`를 0으로 바꾸면 어떤 일이 생기나요? SDK의 자동 재시도(기본 2번)와 겹치면 최대 몇 번 보내게 되나요?
6. (API의 이해) 키를 일부러 틀리게 넣고 `01`을 돌려 보세요. 어떤 HTTP 상태 코드가 오고, 무슨 뜻인가요?

## 면접에 나오는 질문

- LLM API가 stateless라는 게 무슨 뜻이고, 대화형 서비스에서는 어떤 비용 문제가 생기나요?
- 출력 토큰이 입력 토큰보다 비싼 이유를 설명해 보세요.
- `stop_reason`이 `max_tokens`일 때 서비스에서는 어떻게 처리해야 하나요?
