from pydantic import BaseModel

from models import ProfileModel

from .client import get_async_client

async_client = get_async_client()


class TextureInnerDataModel(BaseModel):
    url: str
    model: str | None = None
    cape: str | None = None


async def process_texture(profile: ProfileModel) -> ProfileModel:
    if profile.properties is None:
        return profile

    for prop in profile.properties:
        if prop.name == "textures":
            ...

    return profile
