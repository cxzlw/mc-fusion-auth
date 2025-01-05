from models import YggdrasilServerModel

servers: list[YggdrasilServerModel] = [
    YggdrasilServerModel(
        priority=0,
        session_server="https://sessionserver.mojang.com",
        api_server="https://api.minecraftservices.com",
        skin_domains=[
            ".minecraft.net",
            ".mojang.com",
        ],
    ),
    YggdrasilServerModel(
        priority=1,
        server="https://skin.cxzlw.top",
    ),
    YggdrasilServerModel(
        priority=2,
        server="https://littleskin.cn",
    ),
    # YggdrasilServerModel(  # Removed support as it's using uuid3
    #     priority=2,
    #     server="https://mcskin.com.cn",
    # ),
]
