from typing import overload
from urllib.parse import urljoin

from pydantic import BaseModel, ConfigDict, Field

from utils.client import get_client

client = get_client()


class YggdrasilServerModel(BaseModel):
    priority: int
    server: str | None = None  # 主地址, 如果有 ALI 则跟随跳转
    meta_server: str | None = None
    auth_server: str | None = None
    session_server: str | None = None
    api_server: str | None = None
    skin_domains: list[str] | None = None

    @overload
    def __init__(self, server: str, priority: int = 0) -> None: ...
    @overload
    def __init__(
        self,
        *,
        priority: int = 0,
        meta_server: str,
        auth_server: str,
        session_server: str,
        api_server: str,
        skin_domains: list[str] | None = None,
    ) -> None: ...
    @overload
    def __init__(
        self,
        server: str | None = None,
        priority: int = 0,
        meta_server: str | None = None,
        auth_server: str | None = None,
        session_server: str | None = None,
        api_server: str | None = None,
        skin_domains: list[str] | None = None,
    ) -> None: ...
    def __init__(
        self,
        server: str | None = None,
        priority: int = 0,
        meta_server: str | None = None,
        auth_server: str | None = None,
        session_server: str | None = None,
        api_server: str | None = None,
        skin_domains: list[str] | None = None,
    ) -> None:
        temp_meta_server = None
        temp_auth_server = None
        temp_session_server = None

        if server:
            resp = client.head(server)
            ali: str = resp.headers.get("x-authlib-injector-api-location", "")

            server = urljoin(server, ali)
            temp_meta_server = server
            temp_auth_server = server + "/authserver"
            temp_session_server = server + "/sessionserver"

        if meta_server:
            temp_meta_server = meta_server
        if auth_server:
            temp_auth_server = auth_server
        if session_server:
            temp_session_server = session_server

        super().__init__(
            priority=priority,
            meta_server=temp_meta_server,
            auth_server=temp_auth_server,
            session_server=temp_session_server,
            api_server=api_server,
            skin_domains=skin_domains,
        )


class YggdrasilMetaResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    meta: dict = Field(default_factory=dict)
    skin_domains: list[str] = Field(
        default_factory=list, serialization_alias="skinDomains"
    )
    signature_public_key: str = Field(
        serialization_alias="signxaturePublickey"
    )  # 故意的拼写错误, 在实现之前不会修复


class ProfilePropertyModel(BaseModel):
    name: str
    value: str
    signature: str | None = None


class ProfileModel(BaseModel):
    id: str
    name: str
    properties: list[ProfilePropertyModel] | None = None
