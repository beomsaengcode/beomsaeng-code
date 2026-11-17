"""06. 실험(키·비용 없이): 같은 내용이면 한국어가 토큰을 얼마나 더 쓸까?

실행: pip install tiktoken → python 06_tokens_offline.py
- OpenAI가 공개한 토크나이저(tiktoken)로 세기만 해요. 모델을 부르지 않아서 비용이 0이에요.
- o200k_base = GPT-4o·GPT-5 계열, cl100k_base = 예전 GPT-4·3.5. Claude 토크나이저는 공개돼 있지 않아요(03은 count_tokens API로 셈).
- 영상: 범생코드 쇼츠 "한국어로 물으면 돈을 더 낸다?"
"""

import tiktoken

SYS_KO = """너는 쇼핑몰 고객센터 상담원이다.
항상 존댓말로 짧고 친절하게 답한다.
주문 번호가 없으면 먼저 주문 번호를 물어본다.
환불은 구매 후 7일 이내, 포장을 뜯지 않은 상품만 가능하다고 안내한다.
배송 조회는 주문 번호로 택배사 사이트에서 확인하라고 알려 준다.
모르는 내용은 지어내지 말고 상담원 연결을 권한다.
개인정보(카드 번호, 비밀번호)는 절대 묻지 않는다.
답변은 세 문장을 넘기지 않는다."""
SYS_EN = """You are a customer service agent for an online shop.
Always answer politely, briefly, and kindly.
If there is no order number, ask for the order number first.
Explain that refunds are only possible within 7 days of purchase for unopened items.
For delivery tracking, tell them to check the courier's website with the order number.
Do not make up anything you don't know; suggest connecting to a human agent.
Never ask for personal information (card numbers, passwords).
Keep answers to three sentences or fewer."""
Q = [
    ("이 문서를 세 줄로 요약해 줘.", "Summarize this document in three lines."),
    ("이 코드에서 버그를 찾아 줘.", "Find the bug in this code."),
    ("회의록을 표로 정리해 줘.", "Organize the meeting notes into a table."),
    ("이 이메일을 정중하게 다시 써 줘.", "Rewrite this email politely."),
    ("다음 문장을 영어로 번역해 줘.", "Translate the next sentence into English."),
    ("이 에러 메시지가 무슨 뜻이야?", "What does this error message mean?"),
    ("고객 리뷰를 긍정과 부정으로 나눠 줘.", "Split the customer reviews into positive and negative."),
    ("파이썬으로 CSV 파일 읽는 법 알려 줘.", "Show me how to read a CSV file in Python."),
    ("이 함수에 주석을 달아 줘.", "Add comments to this function."),
    ("발표 자료 목차를 다섯 개 만들어 줘.", "Make a five-item outline for a presentation."),
]

GPT5_MINI_INPUT = 0.25  # 달러 / 100만 토큰, OpenAI 공식 가격표 2026-11-10 확인 (llm/prices.py)


def main():
    for name, label in [("o200k_base", "지금 GPT-5 계열"), ("cl100k_base", "예전 GPT-4")]:
        enc = tiktoken.get_encoding(name)
        n = lambda s, e=enc: len(e.encode(s))  # noqa: E731
        sk, se = n(SYS_KO), n(SYS_EN)
        qk, qe = sum(n(k) for k, _ in Q), sum(n(e) for _, e in Q)
        print(f"[{label} · {name}]")
        print(
            f"  시스템 프롬프트  한국어 {sk:>3}토큰({len(SYS_KO)}자) | 영어 {se:>3}토큰({len(SYS_EN)}자) | {sk / se:.2f}배"
        )
        print(f"  짧은 질문 10개   한국어 {qk:>3} | 영어 {qe:>3} | {qk / qe:.2f}배")
        for s in ["환불은 7일 이내", "Refunds within 7 days"]:
            parts = [enc.decode_single_token_bytes(t).decode("utf-8", "replace") for t in enc.encode(s)]
            print(f"  {s!r} → {len(parts)}조각 {parts}")
        print()
    enc = tiktoken.get_encoding("o200k_base")
    diff = len(enc.encode(SYS_KO)) - len(enc.encode(SYS_EN))
    monthly = diff * 10_000 * 30 / 1e6 * GPT5_MINI_INPUT
    print(
        f"하루 1만 건 요청에 시스템 프롬프트가 붙으면: 차이 {diff}토큰 × 30일 → gpt-5-mini 입력 단가로 한 달 약 ${monthly:.2f}"
    )


if __name__ == "__main__":
    main()
