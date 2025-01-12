import asyncio
import base64
import random
import urllib
import urllib.parse
from hashlib import sha256
from http import HTTPStatus
from typing import Literal

from pydantic import BaseModel
from pydantic.fields import Field

from app import shared
from models import BlockingMode, ProfileModel, ProfilePropertyModel

from .client import get_async_client

async_client = get_async_client()
background_tasks = set()


class TextureInnerMetadataModel(BaseModel):
    model: Literal["slim", "classic"]


class TextureInnerModel(BaseModel):
    url: str
    metadata: TextureInnerMetadataModel | None = None


class TextureModel(BaseModel):
    timestamp: int
    profile_id: str = Field(
        validation_alias="profileId", serialization_alias="profileId"
    )
    profile_name: str = Field(
        validation_alias="profileName", serialization_alias="profileName"
    )
    signature_required: bool = Field(
        False,
        validation_alias="signatureRequired",
        serialization_alias="signatureRequired",
    )
    textures: dict[Literal["SKIN", "CAPE"], TextureInnerModel]


# https://github.com/yushijinhun/authlib-injector/wiki/Yggdrasil-%E6%9C%8D%E5%8A%A1%E7%AB%AF%E6%8A%80%E6%9C%AF%E8%A7%84%E8%8C%83#%E6%9D%90%E8%B4%A8%E5%9F%9F%E5%90%8D%E7%99%BD%E5%90%8D%E5%8D%95
TEXTURE_DOMAIN_ALLOWLIST = [".mojang.com", ".minecraft.net"]


async def restore_profile(
    profile: ProfileModel, blocking_mode: BlockingMode = BlockingMode.NON_BLOCKING
) -> ProfileModel:
    new_profile = profile.model_copy()

    if new_profile.properties is None:
        return new_profile

    for i, prop in enumerate(new_profile.properties):
        if prop.name == "textures":
            new_profile.properties[i] = await restore_texture(prop, blocking_mode)

    return new_profile


async def restore_texture(
    texture_property: ProfilePropertyModel,
    blocking_mode: BlockingMode = BlockingMode.NON_BLOCKING,
) -> ProfilePropertyModel:
    new_texture_property = texture_property.model_copy()

    texture_data = TextureModel.model_validate_json(
        base64.b64decode(new_texture_property.value).decode()
    )

    if "SKIN" not in texture_data.textures:
        return new_texture_property

    if texture_data.signature_required and new_texture_property.signature is not None:
        ...  # TODO: Verify mojang signature

    texture_url = texture_data.textures["SKIN"].url
    texture_domain = urllib.parse.urlparse(texture_url).netloc

    if any(
        texture_domain.endswith(x)
        for x in TEXTURE_DOMAIN_ALLOWLIST
        if x.startswith(".")
    ) or any(
        texture_domain == x for x in TEXTURE_DOMAIN_ALLOWLIST if not x.startswith(".")
    ):
        return new_texture_property

    resp = await async_client.get(texture_url)
    if resp.status_code != HTTPStatus.OK:
        return new_texture_property

    skin_hash = sha256(resp.content).hexdigest()

    cached = await shared.cache.get(
        f"skin-{skin_hash}",
    )
    if cached:
        restore_result = RestoreResult.model_validate_json(cached)
        new_texture_property.value = restore_result.value
        new_texture_property.signature = restore_result.signature
        return new_texture_property

    if blocking_mode == BlockingMode.NON_BLOCKING:
        task: asyncio.Task[RestoreResult | int | None] = asyncio.create_task(
            restore_skin(
                skin_hash,
                texture_url,
                texture_data.textures["SKIN"].metadata.model
                if texture_data.textures["SKIN"].metadata
                else "unknown",
                wait=True,
            )
        )
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)
    elif blocking_mode == BlockingMode.SEMI_BLOCKING:
        res = await restore_skin(
            skin_hash,
            texture_url,
            texture_data.textures["SKIN"].metadata.model
            if texture_data.textures["SKIN"].metadata
            else "unknown",
            wait=False,
        )
        if res:
            new_texture_property.value = res.value
            new_texture_property.signature = res.signature
    else:
        res = await restore_skin(
            skin_hash,
            texture_url,
            texture_data.textures["SKIN"].metadata.model
            if texture_data.textures["SKIN"].metadata
            else "unknown",
            wait=True,
        )
        if res:
            new_texture_property.value = res.value
            new_texture_property.signature = res.signature

    return new_texture_property


class RestoreResult(BaseModel):
    value: str
    signature: str


async def queue_restore_skin(
    skin_hash: str, url: str, variant: Literal["slim", "classic", "unknown"]
) -> RestoreResult | str | None:
    resp = await async_client.post(
        "https://api.mineskin.org/v2/queue",
        json={
            "url": url,
            "variant": variant,
        },
    )
    data = resp.json()
    if resp.status_code == HTTPStatus.OK:
        # skin found
        result = RestoreResult(
            value=data["skin"]["texture"]["data"]["value"],
            signature=data["skin"]["texture"]["data"]["signature"],
        )
        await shared.cache.set(
            f"skin-{skin_hash}",
            result.model_dump_json(),
        )
        return result
    if resp.status_code == HTTPStatus.ACCEPTED:
        # skin not found, queued
        return data["job"]["id"]
    return None


async def wait_skin(skin_hash: str, job_id: str) -> RestoreResult:
    while True:
        resp = await async_client.get(f"https://api.mineskin.org/v2/queue/{job_id}")
        data = resp.json()
        print(resp.status_code, data)
        if data["job"]["status"] == "completed":
            result = RestoreResult(
                value=data["skin"]["texture"]["data"]["value"],
                signature=data["skin"]["texture"]["data"]["signature"],
            )
            await shared.cache.set(
                f"skin-{skin_hash}",
                result.model_dump_json(),
            )
            return result
        await asyncio.sleep(random.random() * 0.5 + 1)


async def restore_skin(
    skin_hash: str,
    url: str,
    variant: Literal["slim", "classic", "unknown"],
    wait: bool = True,
) -> RestoreResult | None:
    res = await queue_restore_skin(skin_hash, url, variant)

    if isinstance(res, RestoreResult):
        return res

    if isinstance(res, str):
        if wait:
            return await wait_skin(skin_hash, res)
        task: asyncio.Task[RestoreResult] = asyncio.create_task(
            wait_skin(skin_hash, res)
        )
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)

    return None
