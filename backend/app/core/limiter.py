from slowapi import Limiter
from slowapi.util import get_remote_address

# 共享限流器：默认全局 200 次/分钟/客户端 IP，防止接口被恶意刷
# （具体接口可在路由上叠加更严格的 @limiter.limit）
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
