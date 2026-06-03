import hashlib
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.cache_service import cache_service

class CacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only cache GET requests
        if request.method != "GET":
            return await call_next(request)
            
        path = request.url.path
        
        # Determine TTL and if route is cacheable
        ttl = None
        if path.startswith("/subjects") or path.startswith("/exam-types"):
            ttl = 86400  # 1 day
        elif path.startswith("/topics/document/"):
            ttl = 3600   # 1 hour
            
        if not ttl:
            return await call_next(request)
            
        # Cache Key logic
        query = request.url.query
        key_raw = f"{path}?{query}" if query else path
        cache_key = "cache:endpoint:" + hashlib.md5(key_raw.encode()).hexdigest()
        
        cached_response = await cache_service.get(cache_key)
        if cached_response:
            # Inject CORS headers manually to bypass BaseHTTPMiddleware limitations on cache hits
            origin = request.headers.get("origin", "*")
            headers = {
                "access-control-allow-origin": origin,
                "access-control-allow-credentials": "true",
                "access-control-allow-methods": "*",
                "access-control-allow-headers": "*"
            }
            return Response(content=cached_response, media_type="application/json", headers=headers)
            
        # Execute request
        response = await call_next(request)
        
        # Read body and cache if 200 OK
        if response.status_code == 200:
            body_iterator = response.body_iterator
            body = b""
            async for chunk in body_iterator:
                body += chunk
                
            await cache_service.set(cache_key, body.decode('utf-8'), ttl=ttl)
            
            # Reconstruct response to return it since we consumed the iterator
            return Response(
                content=body, 
                status_code=response.status_code, 
                headers=dict(response.headers),
                media_type=response.media_type
            )
            
        return response
