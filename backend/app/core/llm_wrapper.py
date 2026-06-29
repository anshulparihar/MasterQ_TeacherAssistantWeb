import asyncio
import logging
import json
import httpx
from typing import Any, AsyncGenerator

from app.config import settings

logger = logging.getLogger(__name__)

class GenerativeContentResponse:
    """A mock response object that behaves like genai.types.GenerateContentResponse"""
    def __init__(self, data: dict):
        self._data = data

    @property
    def text(self) -> str:
        try:
            return self._data['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError):
            return ""

    @property
    def usage_metadata(self) -> dict:
        return self._data.get('usageMetadata', {})


class GeminiClient:
    """REST API Client for Gemini to avoid global config issues of google.generativeai"""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    async def generate_content(self, model_name: str, prompt: Any, **kwargs) -> GenerativeContentResponse:
        url = f"{self.base_url}/{model_name}:generateContent?key={self.api_key}"
        
        parts = []
        if isinstance(prompt, str):
            parts.append({"text": prompt})
        elif isinstance(prompt, list):
            import base64
            for item in prompt:
                if isinstance(item, str):
                    parts.append({"text": item})
                elif isinstance(item, dict) and "mime_type" in item and "data" in item:
                    # Convert bytes to base64 string
                    b64_data = base64.b64encode(item["data"]).decode("utf-8")
                    parts.append({
                        "inlineData": {
                            "mimeType": item["mime_type"],
                            "data": b64_data
                        }
                    })
        
        payload = {
            "contents": [{"parts": parts}]
        }
        
        generation_config = kwargs.get("generation_config")
        if generation_config:
            # Handle genai.GenerationConfig if passed
            config_dict = {}
            if hasattr(generation_config, "response_mime_type") and generation_config.response_mime_type:
                config_dict["responseMimeType"] = generation_config.response_mime_type
            if hasattr(generation_config, "temperature") and generation_config.temperature is not None:
                config_dict["temperature"] = generation_config.temperature
            payload["generationConfig"] = config_dict
            
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                raise Exception(f"Gemini API Error {resp.status_code}: {resp.text}")
            return GenerativeContentResponse(resp.json())

    async def generate_content_async(self, model_name: str, prompt: Any, stream: bool = False, **kwargs) -> AsyncGenerator[GenerativeContentResponse, None] | GenerativeContentResponse:
        if not stream:
            return await self.generate_content(model_name, prompt, **kwargs)
            
        url = f"{self.base_url}/{model_name}:streamGenerateContent?key={self.api_key}&alt=sse"
        
        parts = []
        if isinstance(prompt, str):
            parts.append({"text": prompt})
        elif isinstance(prompt, list):
            import base64
            for item in prompt:
                if isinstance(item, str):
                    parts.append({"text": item})
                elif isinstance(item, dict) and "mime_type" in item and "data" in item:
                    b64_data = base64.b64encode(item["data"]).decode("utf-8")
                    parts.append({
                        "inlineData": {
                            "mimeType": item["mime_type"],
                            "data": b64_data
                        }
                    })
                    
        payload = {
            "contents": [{"parts": parts}]
        }
        
        async def stream_generator():
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        raise Exception(f"Gemini API Stream Error {response.status_code}: {error_text}")
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                yield GenerativeContentResponse(data)
                            except json.JSONDecodeError:
                                continue
                                
        return stream_generator()


class LLMFallbackMeta(type):
    def __getattr__(cls, name):
        async def fallback_caller(*args, **kwargs):
            # 1. Round-Robin Index
            start_index = 0
            try:
                from app.services.cache_service import cache_service
                if cache_service and cache_service.redis:
                    index_val = await cache_service.redis.incr("gemini_instance_index")
                    start_index = (index_val - 1) % len(cls.instances)
            except Exception as e:
                logger.warning(f"Redis unavailable for round-robin, defaulting to 0: {e}")

            last_exception = None
            total_instances = len(cls.instances)
            
            # 2. Try Fallback Loop
            for i in range(total_instances):
                current_idx = (start_index + i) % total_instances
                instance = cls.instances[current_idx]
                
                try:
                    method = getattr(instance, name)
                    return await method(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(
                        f"API Provider {current_idx} ({instance.__class__.__name__}) failed: {e}. "
                        f"Falling back to next..."
                    )
                    continue
            
            logger.error("All fallback APIs exhausted.")
            raise last_exception
            
        return fallback_caller

class LLMWrapper(metaclass=LLMFallbackMeta):
    # Dynamically build the instances based on what's configured in settings
    instances = []
    if settings.GEMINI_API_KEY:
        instances.append(GeminiClient(api_key=settings.GEMINI_API_KEY))
    if settings.GEMINI_API_KEY_2:
        instances.append(GeminiClient(api_key=settings.GEMINI_API_KEY_2))
    if settings.GEMINI_API_KEY_3:
        instances.append(GeminiClient(api_key=settings.GEMINI_API_KEY_3))
    if settings.GEMINI_API_KEY_4:
        instances.append(GeminiClient(api_key=settings.GEMINI_API_KEY_4))
    if settings.GEMINI_EXTRACTOR_API_KEY:
        instances.append(GeminiClient(api_key=settings.GEMINI_EXTRACTOR_API_KEY))
    if settings.GEMINI_QUESTION_GENERATOR_MODEL:
        instances.append(GeminiClient(api_key=settings.GEMINI_QUESTION_GENERATOR_MODEL))
    if settings.GEMINI_QUESTION_CHAT_BOT:
        instances.append(GeminiClient(api_key=settings.GEMINI_QUESTION_CHAT_BOT))
    if settings.GEMINI_QUESTION_SUPREME:
        instances.append(GeminiClient(api_key=settings.GEMINI_QUESTION_SUPREME))
    if settings.GEMINI_QUESTION_KEY:
        instances.append(GeminiClient(api_key=settings.GEMINI_QUESTION_KEY))
    if settings.GEMINI_QUESTION_KEY_AD_1:
        instances.append(GeminiClient(api_key=settings.GEMINI_QUESTION_KEY_AD_1))
    # If no keys are configured, provide at least one empty client to avoid division by zero
    if not instances:
        instances.append(GeminiClient(api_key=""))
