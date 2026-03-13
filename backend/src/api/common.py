from __future__ import annotations


def get_request_id(request) -> str | None:
    state = getattr(request, "state", None)
    if state is None:
        return None
    return getattr(state, "request_id", None)
