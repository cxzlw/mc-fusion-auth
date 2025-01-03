from fastapi import APIRouter

from app import shared
from utils.upstreams import get_upstreams_profile_keys

api = APIRouter()


@api.get("/publickeys")
async def public_keys() -> set[str]:
    return await get_upstreams_profile_keys(shared.servers)
