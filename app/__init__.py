import asyncio
from typing import Annotated

from fastapi import Depends, FastAPI
from httpx import AsyncClient

from app import shared as shared
from models import YggdrasilMetaResponse
from utils.client import get_async_client

from .api import api
from .auth import auth
from .session import session

app = FastAPI()

app.include_router(auth, prefix="/authserver")
app.include_router(session, prefix="/sessionserver")
app.include_router(api, prefix="/api")


@app.get("/")
async def meta(
    client: Annotated[AsyncClient, Depends(get_async_client)],
) -> YggdrasilMetaResponse:
    resps = await asyncio.gather(
        *(
            client.get(server.meta_server)
            for server in shared.servers
            if server.meta_server is not None
        )
    )

    skin_domains: set[str] = set()
    for x in resps:
        skin_domains.update(x.json().get("skinDomains", []))

    for server in shared.servers:
        if server.skin_domains:
            skin_domains.update(server.skin_domains)

    return YggdrasilMetaResponse(
        meta={},
        skin_domains=list(skin_domains),
        signature_public_key="",
    )
