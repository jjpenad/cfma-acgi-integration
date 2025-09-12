import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CacheManager:
    """Generic cache manager with time-based expiration"""
    
    def __init__(self, default_expiry_minutes: int = 30):
        """
        Initialize the cache manager
        
        Args:
            default_expiry_minutes: Default cache expiration time in minutes
        """
        self._cache = {}
        self._default_expiry = timedelta(minutes=default_expiry_minutes)
        logger.info(f"CacheManager initialized with {default_expiry_minutes} minute default expiry")
    
    def get(self, key: str, expiry: Optional[timedelta] = None) -> Optional[Any]:
        """
        Get cached data if it exists and is still valid
        
        Args:
            key: Cache key
            expiry: Custom expiry time (uses default if None)
            
        Returns:
            Cached data if valid, None otherwise
        """
        if key not in self._cache:
            return None
        
        cache_entry = self._cache[key]
        cache_time = cache_entry['timestamp']
        expiry_time = expiry or self._default_expiry
        
        if datetime.now() - cache_time >= expiry_time:
            # Cache expired, remove it
            del self._cache[key]
            logger.debug(f"Cache expired for key: {key}")
            return None
        
        logger.debug(f"Cache hit for key: {key}")
        return cache_entry['data']
    
    def set(self, key: str, data: Any, expiry: Optional[timedelta] = None) -> None:
        """
        Store data in cache with timestamp
        
        Args:
            key: Cache key
            data: Data to cache
            expiry: Custom expiry time (uses default if None)
        """
        self._cache[key] = {
            'data': data,
            'timestamp': datetime.now(),
            'expiry': expiry or self._default_expiry
        }
        logger.debug(f"Cached data for key: {key}")
    
    def is_valid(self, key: str, expiry: Optional[timedelta] = None) -> bool:
        """
        Check if cache entry exists and is still valid
        
        Args:
            key: Cache key
            expiry: Custom expiry time (uses default if None)
            
        Returns:
            True if cache is valid, False otherwise
        """
        if key not in self._cache:
            return False
        
        cache_entry = self._cache[key]
        cache_time = cache_entry['timestamp']
        expiry_time = expiry or self._default_expiry
        
        return datetime.now() - cache_time < expiry_time
    
    def clear(self, key: Optional[str] = None) -> None:
        """
        Clear cache entry or all cache
        
        Args:
            key: Specific key to clear (clears all if None)
        """
        if key:
            if key in self._cache:
                del self._cache[key]
                logger.info(f"Cleared cache for key: {key}")
        else:
            self._cache.clear()
            logger.info("Cleared all cache entries")
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get information about current cache state
        
        Returns:
            Dictionary with cache statistics
        """
        now = datetime.now()
        cache_info = {
            'total_entries': len(self._cache),
            'entries': []
        }
        
        for cache_key, cache_entry in self._cache.items():
            age_minutes = (now - cache_entry['timestamp']).total_seconds() / 60
            expiry_minutes = cache_entry['expiry'].total_seconds() / 60
            is_valid = self.is_valid(cache_key)
            
            cache_info['entries'].append({
                'key': cache_key,
                'age_minutes': round(age_minutes, 2),
                'expiry_minutes': round(expiry_minutes, 2),
                'is_valid': is_valid,
                'cached_at': cache_entry['timestamp'].isoformat()
            })
        
        return cache_info
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired cache entries
        
        Returns:
            Number of entries removed
        """
        now = datetime.now()
        expired_keys = []
        
        for key, cache_entry in self._cache.items():
            if now - cache_entry['timestamp'] >= cache_entry['expiry']:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        total_entries = len(self._cache)
        valid_entries = sum(1 for key in self._cache.keys() if self.is_valid(key))
        expired_entries = total_entries - valid_entries
        
        return {
            'total_entries': total_entries,
            'valid_entries': valid_entries,
            'expired_entries': expired_entries,
            'hit_rate': f"{valid_entries}/{total_entries}" if total_entries > 0 else "0/0"
        }


# Global cache manager instance
events_cache = CacheManager(default_expiry_minutes=30)
