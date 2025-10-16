"""
Redis caching service for performance optimization
"""
import redis
import json
from typing import Optional, Any
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CacheService:
    """Redis cache service"""
    
    def __init__(self):
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error("Failed to connect to Redis", extra={"error": str(e)})
            self.redis_client = None
    
    def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        if not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                logger.debug("Cache hit", extra={"key": key})
            return value
        except Exception as e:
            logger.error("Cache get failed", extra={"key": key, "error": str(e)})
            return None
    
    def set(self, key: str, value: str, ttl: int = 3600):
        """Set value in cache with TTL in seconds"""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.setex(key, ttl, value)
            logger.debug("Cache set", extra={"key": key, "ttl": ttl})
            return True
        except Exception as e:
            logger.error("Cache set failed", extra={"key": key, "error": str(e)})
            return False
    
    def delete(self, key: str):
        """Delete key from cache"""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.delete(key)
            logger.debug("Cache delete", extra={"key": key})
            return True
        except Exception as e:
            logger.error("Cache delete failed", extra={"key": key, "error": str(e)})
            return False
    
    def get_json(self, key: str) -> Optional[Any]:
        """Get JSON value from cache"""
        value = self.get(key)
        if value:
            try:
                return json.loads(value)
            except:
                return None
        return None
    
    def set_json(self, key: str, value: Any, ttl: int = 3600):
        """Set JSON value in cache"""
        try:
            json_str = json.dumps(value)
            return self.set(key, json_str, ttl)
        except:
            return False
    
    # Project-specific caching methods
    
    def cache_project_html(self, subdomain: str, html: str, ttl: int = 3600):
        """Cache project HTML by subdomain"""
        key = f"project:subdomain:{subdomain}"
        return self.set(key, html, ttl)
    
    def get_cached_project_html(self, subdomain: str) -> Optional[str]:
        """Get cached project HTML"""
        key = f"project:subdomain:{subdomain}"
        return self.get(key)
    
    def cache_custom_domain_html(self, domain: str, html: str, ttl: int = 3600):
        """Cache project HTML by custom domain"""
        key = f"project:domain:{domain}"
        return self.set(key, html, ttl)
    
    def get_cached_custom_domain_html(self, domain: str) -> Optional[str]:
        """Get cached project HTML by custom domain"""
        key = f"project:domain:{domain}"
        return self.get(key)
    
    def invalidate_project_cache(self, subdomain: str = None, domain: str = None):
        """Invalidate project cache"""
        if subdomain:
            self.delete(f"project:subdomain:{subdomain}")
        if domain:
            self.delete(f"project:domain:{domain}")
        logger.info("Project cache invalidated", extra={
            "subdomain": subdomain,
            "domain": domain
        })


# Global cache service instance
cache_service = CacheService()
