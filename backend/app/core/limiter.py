import time
from fastapi import Request, HTTPException
from app.services.cache_service import cache_service
from app.core.deps import get_current_user

class RateLimiter:
    def __init__(self):
        # Base limits
        self.limits = {
            "qgen": {"limit": 10, "window": 3600},
            "upload": {"limit": 20, "window": 86400},
            "chat": {"limit": 100, "window": 3600}
        }

    async def check_limit(self, user_id: str, action: str):
        if action not in self.limits:
            return True

        config = self.limits[action]
        limit = config["limit"]
        window = config["window"]

        key = f"rate:{action}:{user_id}"
        
        # Token bucket logic using Redis pipeline or simple increment
        # Since we use simple aioredis get/set wrapper in cache_service:
        # A true atomic token bucket usually requires Lua script.
        # Here we use a simpler Fixed Window approach via INCR and EXPIRE for simplicity in Python if Lua isn't available.
        # Actually, let's implement standard fixed window counter for robustness without lua.
        
        # We assume cache_service.redis is available. If not, fallback to simple wrapper.
        current_count = await cache_service.get(key)
        if current_count is None:
            current_count = 0
            
        if int(current_count) >= limit:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded for {action}. Try again later."
            )
            
        # Increment (in a real system use cache_service.redis.incr to be atomic)
        # We will use set with TTL if it's the first time
        if current_count == 0:
            await cache_service.set(key, 1, ttl=window)
        else:
            await cache_service.set(key, int(current_count) + 1, ttl=window)
            
        return True

rate_limiter = RateLimiter()

# Middleware usage:
# async def limit_middleware(request: Request, call_next):
#    # identify action based on route and call check_limit
#    ...
