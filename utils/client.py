from hishel import (
    HEURISTICALLY_CACHEABLE_STATUS_CODES,
    AsyncCacheClient,
    AsyncFileStorage,
    CacheClient,
    Controller,
    FileStorage,
)
from httpx import AsyncClient, Client, Timeout

user_agent = "mc-fusion-auth/v0.0.0-dev"

storage, async_storage = (
    FileStorage(
        ttl=3600,
    ),
    AsyncFileStorage(
        ttl=3600,
    ),
)

controller = Controller(
    allow_heuristics=True,
    cacheable_methods=["GET", "HEAD"],
    cacheable_status_codes=HEURISTICALLY_CACHEABLE_STATUS_CODES,  # type: ignore
)

client = CacheClient(
    http2=True,
    storage=storage,
    controller=controller,
    timeout=Timeout(20),
    headers={"User-Agent": user_agent},
)
async_client = AsyncCacheClient(
    http2=True,
    storage=async_storage,
    controller=controller,
    timeout=Timeout(20),
    headers={"User-Agent": user_agent},
)


def get_client() -> Client:
    return client


def get_async_client() -> AsyncClient:
    return async_client
