"""
缓存服务 - 基于Redis的权限与数据缓存
如果Redis不可用，自动降级为Flask应用内存缓存（仅单实例有效）
"""
import json
import time

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class CacheService:
    """缓存服务"""
    
    _memory_cache = {}  # 内存缓存降级方案 {key: (value, expire_at)}
    _redis_client = None
    
    @classmethod
    def _get_redis(cls):
        """懒加载Redis连接"""
        if not REDIS_AVAILABLE:
            return None
        if cls._redis_client is not None:
            return cls._redis_client
        try:
            from flask import current_app
            redis_url = current_app.config.get('REDIS_URL')
            if redis_url:
                cls._redis_client = redis.from_url(redis_url, decode_responses=True)
                cls._redis_client.ping()
            return cls._redis_client
        except Exception:
            cls._redis_client = None
            return None
    
    @classmethod
    def _make_key(cls, key):
        """统一Key前缀"""
        return f"techhub:{key}"
    
    @classmethod
    def get(cls, key):
        """获取缓存"""
        key = cls._make_key(key)
        r = cls._get_redis()
        if r:
            val = r.get(key)
            if val:
                try:
                    return json.loads(val)
                except Exception:
                    return val
            return None
        
        # 内存缓存降级
        item = cls._memory_cache.get(key)
        if item is None:
            return None
        value, expire_at = item
        if expire_at and expire_at < time.time():
            cls._memory_cache.pop(key, None)
            return None
        return value
    
    @classmethod
    def set(cls, key, value, ttl=300):
        """设置缓存，ttl单位为秒"""
        key = cls._make_key(key)
        r = cls._get_redis()
        if r:
            try:
                r.setex(key, ttl, json.dumps(value, default=str))
                return True
            except Exception:
                pass
        
        # 内存缓存降级
        expire_at = time.time() + ttl if ttl else None
        cls._memory_cache[key] = (value, expire_at)
        # 清理过期项，防止内存无限增长
        cls._cleanup_memory_cache()
        return True
    
    @classmethod
    def delete(cls, key):
        """删除缓存"""
        key = cls._make_key(key)
        r = cls._get_redis()
        if r:
            try:
                r.delete(key)
            except Exception:
                pass
        cls._memory_cache.pop(key, None)
        return True
    
    @classmethod
    def _cleanup_memory_cache(cls):
        """清理过期的内存缓存项"""
        now = time.time()
        expired = [k for k, v in cls._memory_cache.items() if v[1] and v[1] < now]
        for k in expired:
            cls._memory_cache.pop(k, None)
        # 如果仍然太多，清理最早的20%
        if len(cls._memory_cache) > 1000:
            keys = sorted(cls._memory_cache.keys(), 
                         key=lambda k: cls._memory_cache[k][1] or 0)
            for k in keys[:200]:
                cls._memory_cache.pop(k, None)
    
    # ==================== 权限相关快捷方法 ====================
    
    @classmethod
    def get_user_permissions(cls, user_id):
        """获取用户权限缓存"""
        return cls.get(f"permissions:user:{user_id}")
    
    @classmethod
    def cache_user_permissions(cls, user_id, permissions, ttl=300):
        """缓存用户权限"""
        return cls.set(f"permissions:user:{user_id}", permissions, ttl)
    
    @classmethod
    def invalidate_user_permissions(cls, user_id):
        """清除用户权限缓存"""
        return cls.delete(f"permissions:user:{user_id}")
    
    @classmethod
    def get_role_permissions(cls, role_id):
        """获取角色权限缓存"""
        return cls.get(f"permissions:role:{role_id}")
    
    @classmethod
    def cache_role_permissions(cls, role_id, permissions, ttl=600):
        """缓存角色权限"""
        return cls.set(f"permissions:role:{role_id}", permissions, ttl)
    
    @classmethod
    def invalidate_role_permissions(cls, role_id):
        """清除角色权限缓存"""
        return cls.delete(f"permissions:role:{role_id}")
    
    # ==================== Token黑名单（替代内存set）====================
    
    @classmethod
    def is_token_revoked(cls, jti):
        """检查token是否已被注销"""
        return cls.get(f"token:revoked:{jti}") is not None
    
    @classmethod
    def revoke_token(cls, jti, expires_in=86400):
        """注销token，默认缓存到原token过期时间"""
        return cls.set(f"token:revoked:{jti}", True, ttl=expires_in)
