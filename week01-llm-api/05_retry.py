"""05. 에러 처리: 다시 보낼 에러와 고쳐야 할 에러를 나누고, 지수 백오프 + 지터로 다시 보낸다.

내 PC에 가짜 API 서버를 띄워서 돌린다(키·인터넷·비용 없음).
실행: python 05_retry.py

규칙 (Claude API 공식 에러 문서 기준: platform.claude.com/docs/en/api/errors)
- 다시 보낼 것: 429 rate_limit_error, 500 api_error, 529 overloaded_error (그리고 504 timeout_error)
- 고쳐서 보낼 것: 400 · 401 · 403 · 404 · 413 → 똑같이 보내면 똑같이 실패한다
- retry-after 헤더가 있으면 그 값을 먼저 따른다. 횟수엔 상한을 둔다.
※ 공식 SDK는 이미 기본 2번 자동 재시도한다(max_retries). SDK 위에 이 코드를 또 감싸면 횟수가 곱해진다.
"""

import contextlib
import json
import random
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

RETRY = {429, 500, 504, 529}
BASE, CAP, MAX_RETRIES = 1.0, 8.0, 5


def wait_time(attempt, retry_after=None):
    """attempt번째 재시도 전에 기다릴 초. 1·2·4·8초에 무작위(0.5~1.5배)를 곱하고 CAP초를 넘지 않게."""
    if retry_after is not None:
        return float(retry_after)
    return min(CAP, BASE * 2**attempt * random.uniform(0.5, 1.5))


def call(url, body):
    """요청 하나. 성공하면 응답 JSON, 다시 보낼 수 없거나 횟수를 다 쓰면 예외."""
    for attempt in range(MAX_RETRIES + 1):
        req = urllib.request.Request(url, json.dumps(body).encode(), {"content-type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                print(f"  요청 {attempt + 1}  {r.status} ✓")
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            kind = json.loads(e.read() or b"{}").get("error", {}).get("type", "")
            if e.code not in RETRY:
                print(f"  요청 {attempt + 1}  {e.code} {kind} → 다시 보내지 않음(요청을 고쳐야 함)")
                raise
            if attempt == MAX_RETRIES:
                print(f"  요청 {attempt + 1}  {e.code} → 최대 {MAX_RETRIES}번 다시 보냈는데 실패, 멈춤")
                raise
            ra = e.headers.get("retry-after")
            w = wait_time(attempt, ra)
            how = f"retry-after {ra}초" if ra else "백오프"
            print(f"  요청 {attempt + 1}  {e.code} {kind} → {w:.1f}초 대기 ({how})")
            time.sleep(w)
    raise RuntimeError("도달하지 않음")


# ---- 가짜 API 서버: 시나리오마다 정해 둔 상태 코드를 차례로 돌려준다 ----
TYPES = {
    400: "invalid_request_error",
    401: "authentication_error",
    429: "rate_limit_error",
    500: "api_error",
    529: "overloaded_error",
}
PLAN = []  # (상태 코드, retry-after) 목록, 앞에서부터 하나씩 쓴다


class FakeAPI(BaseHTTPRequestHandler):
    def do_POST(self):
        self.rfile.read(int(self.headers.get("content-length", 0)))
        code, ra = PLAN.pop(0) if PLAN else (200, None)
        body = (
            {"content": [{"type": "text", "text": "안녕하세요"}]}
            if code == 200
            else {"type": "error", "error": {"type": TYPES.get(code, "error"), "message": "fake"}}
        )
        self.send_response(code)
        self.send_header("content-type", "application/json")
        if ra:
            self.send_header("retry-after", str(ra))
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def log_message(self, *a):  # 서버 로그는 숨긴다
        pass


def scenario(title, plan, url):
    PLAN[:] = plan
    print(f"\n[{title}]")
    t0 = time.time()
    with contextlib.suppress(urllib.error.HTTPError):
        call(url, {"messages": [{"role": "user", "content": "안녕"}]})
    print(f"  걸린 시간 {time.time() - t0:.1f}초")


if __name__ == "__main__":
    srv = HTTPServer(("127.0.0.1", 0), FakeAPI)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_port}/v1/messages"
    scenario("429가 세 번 → 백오프로 다시", [(429, None)] * 3, url)
    scenario("retry-after 헤더가 있으면 그 값대로", [(429, 2)], url)
    scenario("401 키 오류 → 다시 보내지 않음", [(401, None)], url)
    scenario("529가 계속 → 횟수 상한에서 멈춤", [(529, None)] * 9, url)
    srv.shutdown()
