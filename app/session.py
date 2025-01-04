import asyncio
from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from httpx import AsyncClient

from app import shared
from models import ProfileModel
from utils.client import get_async_client

session = APIRouter()


@session.get(
    "/session/minecraft/hasJoined",
    response_model=ProfileModel,
    responses={204: {"model": None}},
)
async def has_joined(
    client: Annotated[AsyncClient, Depends(get_async_client)],
    username: str,
    server_id: Annotated[str, Query(alias="serverId")],
    ip: str | None = None,
) -> ProfileModel | Response:
    resps = await asyncio.gather(
        *(
            client.get(
                f"{server.session_server}/session/minecraft/hasJoined",
                params={"username": username, "serverId": server_id}
                if ip is None
                else {"username": username, "serverId": server_id, "ip": ip},
            )
            for server in shared.servers
        )
    )

    for resp in resps:
        print(resp.status_code)
        if resp.status_code == HTTPStatus.OK:
            return resp.json()

    # print(res)
    return Response(status_code=HTTPStatus.NO_CONTENT)


@session.get(
    "/session/minecraft/profile/{uuid}",
    response_model=ProfileModel,
    responses={200: {"model": ProfileModel}, 204: {"model": None}},
)
async def get_profile(
    client: Annotated[AsyncClient, Depends(get_async_client)],
    uuid: UUID,
    unsigned: bool = True,
) -> ProfileModel | Response:
    resps = await asyncio.gather(
        *(
            client.get(
                f"{server.session_server}/session/minecraft/profile/{str(uuid).replace('-', '')}",
                params={"unsigned": unsigned},
            )
            for server in shared.servers
        )
    )

    for resp in resps:
        if resp.status_code == HTTPStatus.OK:
            return resp.json()

    return Response(status_code=HTTPStatus.NO_CONTENT)
