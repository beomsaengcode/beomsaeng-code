"""04. 토큰·비용 계산기: 10번 주고받으며 턴마다 입력·출력 토큰과 누적 비용을 표로 본다.

핵심: API는 기억이 없어서 매번 지난 대화 전체를 다시 보낸다 → 입력 토큰이 계단처럼 쌓인다.
실행: python 04_cost_calc.py                 (그대로: 대화 전체를 보냄)
      python 04_cost_calc.py --trim 4        (자르기: 최근 4턴만 보냄)
      python 04_cost_calc.py --summary 3     (요약: 오래된 대화는 요약 한 덩어리 + 최근 3턴)
      python 04_cost_calc.py --compare       (세 방식을 차례로 돌려 누적만 나란히)
      --price claude-opus-5-5                (비용을 이 모델 단가로 어림. 로컬 모델로 연습할 때. 토크나이저가 달라 어림값)
"""

import sys

from _setup import cost, llm

QUESTIONS = [
    "REST API가 뭐야? 두 문장으로",
    "GET이랑 POST 차이는?",
    "그럼 PUT이랑 PATCH는?",
    "상태 코드 401이랑 403 차이는?",
    "429는 언제 나와?",
    "429가 나면 어떻게 다시 보내?",
    "지수 백오프가 뭐야?",
    "지터는 왜 섞어?",
    "재시도 횟수는 몇 번이 적당해?",
    "지금까지 얘기한 걸 세 줄로 정리해 줘",
]
SHORT = "모든 답은 두 문장 이하로."
PRICE = sys.argv[sys.argv.index("--price") + 1] if "--price" in sys.argv else None


def usd(model, i, o):
    return cost(PRICE or model, i, o) or 0.0


def send(messages, mode, keep, memo):
    """mode에 따라 실제로 보낼 메시지를 고른다. 요약은 추가 호출의 Reply도 돌려준다.
    keep턴 = 지난 (keep-1)번의 질문·답 + 이번 질문 → 메시지 2*keep-1개 (항상 user로 시작)
    요약은 매번 하지 않는다: 요약 안 된 오래된 메시지가 keep턴만큼 쌓였을 때만, 지난 요약 + 새로 밀려난 부분을 다시 요약."""
    n = 2 * keep - 1
    if mode == "trim" and len(messages) > n:
        return messages[-n:], None
    if mode == "summary" and len(messages) > n:
        s = None
        old = messages[memo["done"] : -n]
        if len(old) >= 2 * keep:
            talk = "\n".join(f"{m['role']}: {m['content']}" for m in old)
            prev = f"지난 요약: {memo['text']}\n\n" if memo["text"] else ""
            s = llm.chat(
                [{"role": "user", "content": f"{prev}다음 대화를 더해 세 줄로 요약해 줘.\n\n{talk}"}],
                max_tokens=200,
            )
            memo["text"], memo["done"] = s.text, len(messages) - n
        recent = messages[memo["done"] :]
        if not memo["text"]:
            return recent, s
        head = {"role": "user", "content": f"(앞 대화 요약) {memo['text']}"}
        # user가 두 번 이어지면 안 되는 공급자가 있어 요약 뒤에 짧은 답을 끼운다
        return [head, {"role": "assistant", "content": "네, 이어서 할게요."}, *recent], s
    return messages, None


def run(mode="full", keep=4, show=True):
    history, total_in, total_cost, extra, memo = [], 0, 0.0, 0, {"text": "", "done": 0}
    if show:
        print(f"[방식] {mode}" + (f" (최근 {keep}턴)" if mode != "full" else ""))
        print(f"{'턴':>2} {'보낸 메시지':>6} {'입력':>6} {'출력':>5} {'이번 비용':>10} {'누적':>10}")
    for i, q in enumerate(QUESTIONS, 1):
        history.append({"role": "user", "content": q})
        msgs, s = send(history, mode, keep, memo)
        sent = len(msgs)
        r = llm.chat(msgs, system=SHORT, max_tokens=200)
        history.append(r.as_message())
        n_in = r.input_tokens + (s.input_tokens if s else 0)
        c = usd(r.model, r.input_tokens, r.output_tokens)
        if s:
            c += usd(s.model, s.input_tokens, s.output_tokens)
            extra += 1
        total_in += n_in
        total_cost += c
        if show:
            print(f"{i:>2} {sent:>6} {n_in:>6,} {r.output_tokens:>5} ${c:>9.5f} ${total_cost:>9.5f}")
    if show:
        tail = f" · 요약 호출 {extra}번 포함" if extra else ""
        print(f"\n[누적 입력] {total_in:,} 토큰{tail}")
        if PRICE:
            print(f"※ 비용은 {PRICE} 단가로 어림한 값이에요(모델마다 토큰 수가 달라요).")
        elif cost(llm.model, 1, 0) == 0:
            print("※ 로컬 모델은 API 비용이 0이에요. --price claude-opus-5-5 로 유료 단가를 어림해 보세요.")
    return total_in, total_cost, extra


if __name__ == "__main__":
    args = sys.argv[1:]

    def num(flag, d):
        return int(args[args.index(flag) + 1]) if flag in args and len(args) > args.index(flag) + 1 else d

    if "--compare" in args:
        rows = [("그대로", *run("full", show=False))]
        rows.append(("최근 4턴만", *run("trim", 4, show=False)))
        rows.append(("요약+최근 3턴", *run("summary", 3, show=False)))
        base = rows[0][1]
        for name, tin, tc, extra in rows:
            note = f"  (요약 호출 {extra}번 포함)" if extra else ""
            print(f"{name:<10} 누적 입력 {tin:>7,} 토큰  {tin / base:>5.0%}  ${tc:.5f}{note}")
    elif "--trim" in args:
        run("trim", num("--trim", 4))
    elif "--summary" in args:
        run("summary", num("--summary", 3))
    else:
        run()
