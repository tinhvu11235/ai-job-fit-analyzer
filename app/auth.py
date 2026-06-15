import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable

from fastapi import Header, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse

from app.config import get_settings


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if not settings.app_api_key:
        return
    if x_api_key != settings.app_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key.")


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    async def __call__(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        settings = get_settings()
        limit = settings.rate_limit_per_minute
        if limit <= 0 or request.url.path == "/health":
            return await call_next(request)

        client = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - 60
        hits = self._hits[client]
        while hits and hits[0] < window_start:
            hits.popleft()

        if len(hits) >= limit:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded."},
            )

        hits.append(now)
        return await call_next(request)


class InMemoryDailyQuota:
    def __init__(self) -> None:
        self._counts: dict[str, tuple[str, int]] = {}

    def consume(self, request: Request) -> None:
        settings = get_settings()
        limit = settings.public_demo_daily_limit
        if limit <= 0:
            return

        client = request.client.host if request.client else "unknown"
        today = time.strftime("%Y-%m-%d", time.gmtime())
        recorded_day, count = self._counts.get(client, (today, 0))
        if recorded_day != today:
            count = 0

        if count >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Public demo daily limit reached. Try again tomorrow or use a private API key.",
            )

        self._counts[client] = (today, count + 1)


async def require_public_demo_enabled() -> None:
    settings = get_settings()
    if not settings.public_demo_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Public demo is not enabled.")
