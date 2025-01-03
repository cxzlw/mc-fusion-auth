import asyncio

from models import YggdrasilServerModel

from .client import get_async_client

client = get_async_client()


async def get_upstream_profile_keys(server: YggdrasilServerModel) -> set[str]:
    profile_keys: set[str] = set()
    if server.meta_server:
        resp = await client.get(server.meta_server)
        if resp.is_success:
            key: str | None = resp.json().get("signaturePublickey", None)
            if key:
                key = (
                    key.replace("-----BEGIN PUBLIC KEY-----", "")
                    .replace("-----END PUBLIC KEY-----", "")
                    .replace("\n", "")
                    .strip()
                )
                print(key)
                profile_keys.add(key)

    if server.api_server:
        resp = await client.get(server.api_server + "/publickeys")
        if resp.is_success:
            print(resp.json())
            profile_keys.update(
                x["publicKey"] for x in resp.json()["profilePropertyKeys"]
            )
    return profile_keys


async def get_upstreams_profile_keys(servers: list[YggdrasilServerModel]) -> set[str]:
    keys: set[str] = set()
    for res in await asyncio.gather(
        *[get_upstream_profile_keys(server) for server in servers]
    ):
        keys.update(res)
    return keys
