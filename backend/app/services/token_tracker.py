import datetime
import structlog
from app.services.cache_service import cache_service

logger = structlog.get_logger()

class TokenTracker:
    def __init__(self):
        self.DEFAULT_DAILY_LIMIT = 100000

    def _get_key(self, user_id: str) -> str:
        date_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")
        return f"tokens:{user_id}:{date_str}"

    async def check_and_consume_tokens(self, user_id: str, estimated_tokens: int) -> bool:
        key = self._get_key(user_id)
        current = await cache_service.get(key)
        
        if current is None:
            current = 0
            
        if int(current) + estimated_tokens > self.DEFAULT_DAILY_LIMIT:
            logger.warning("User exceeded token limit", user_id=user_id, current_tokens=current, limit=self.DEFAULT_DAILY_LIMIT)
            return False
            
        return True

    async def log_actual_usage(self, user_id: str, tokens_used: int):
        if tokens_used <= 0:
            return
            
        key = self._get_key(user_id)
        current = await cache_service.get(key)
        if current is None:
            # Set with 2 days TTL to ensure it expires safely after midnight
            await cache_service.set(key, tokens_used, ttl=172800) 
        else:
            await cache_service.set(key, int(current) + tokens_used, ttl=172800)
            
        logger.info("Tokens consumed", user_id=user_id, amount=tokens_used)

    async def get_usage(self, user_id: str) -> int:
        key = self._get_key(user_id)
        val = await cache_service.get(key)
        return int(val) if val else 0

token_tracker = TokenTracker()
