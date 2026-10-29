import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from coproducer.services import set_service

SEEN = []


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        SEEN.append((self.path, body))
        reply = {"choices": [{"message": {"role": "assistant", "content": "", "tool_calls": [{"id": "1", "type": "function",
                 "function": {"name": "ping_fl", "arguments": "{}"}}]}, "finish_reason": "tool_calls"}], "usage": {"total_tokens": 12}}
        data = json.dumps(reply).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass


def test_round_trip(rig):
    srv = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        set_service("llm", {"endpoint": "http://127.0.0.1:%d/v1/" % srv.server_port, "model": "local-model", "timeout_s": 5})
        tools = [{"type": "function", "function": {"name": "ping_fl", "parameters": {"type": "object", "properties": {}}}}]
        r = rig.call("call_agent_llm", prompt="check FL", system="You are a co-producer.", tools=tools)
        assert r.ok and r.value["message"]["tool_calls"][0]["function"]["name"] == "ping_fl" and r.value["usage"]["total_tokens"] == 12
        path, body = SEEN[-1]
        assert path == "/v1/chat/completions" and body["model"] == "local-model" and body["tools"] == tools
        assert [m["role"] for m in body["messages"]] == ["system", "user"]
    finally:
        srv.shutdown()


def test_unreachable_and_unset(rig):
    assert rig.call("call_agent_llm", prompt="hi").error.code == "E_UNSUPPORTED_API"
    set_service("llm", {"endpoint": "http://127.0.0.1:9/v1", "timeout_s": 1})
    r = rig.call("call_agent_llm", prompt="hi")
    assert r.error.code == "E_MODEL" and r.error.retryable
