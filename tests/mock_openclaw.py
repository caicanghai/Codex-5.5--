"""In-process mock of the OpenClaw (openclaw-weixin) HTTP endpoint.

Provides an httpx.MockTransport handler so the OpenClawProvider can be exercised
end-to-end without a live server.
"""

from __future__ import annotations

import httpx

STREAM_BODY = (
    "data: {\"choices\":[{\"delta\":{\"content\":\"Hello\"}}]}\n\n"
    "data: {\"choices\":[{\"delta\":{\"content\":\" world\"}}]}\n\n"
    "data: [DONE]\n\n"
)


def make_handler(*, fail_times: int = 0):
    """Return a handler; first `fail_times` calls raise a transport error."""
    state = {"fails": fail_times}

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if state["fails"] > 0:
            state["fails"] -= 1
            raise httpx.ConnectError("mock transient failure", request=request)
        if path.endswith("/healthz"):
            return httpx.Response(200, json={"status": "ok"})
        if path.endswith("/v1/chat/completions"):
            import json as _json

            body = _json.loads(request.content or b"{}")
            if body.get("stream"):
                return httpx.Response(
                    200, text=STREAM_BODY, headers={"content-type": "text/event-stream"}
                )
            return httpx.Response(
                200, json={"choices": [{"message": {"content": "Hello world"}}]}
            )
        if path.endswith("/media"):
            return httpx.Response(200, json={"media_id": "md-1"})
        if path.endswith("/send"):
            return httpx.Response(200, json={"ok": True, "message_id": "m-1"})
        return httpx.Response(404, json={"error": "not found"})

    return handler


def mock_transport(*, fail_times: int = 0) -> httpx.MockTransport:
    return httpx.MockTransport(make_handler(fail_times=fail_times))
