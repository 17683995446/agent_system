"""
认证中间件 - FastAPI依赖注入和路由保护
"""
from typing import Optional, Callable
from functools import wraps
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .jwt_auth_service import JWTAuthService, get_auth_service, TokenType, UserRole


security = HTTPBearer(auto_error=False)


class AuthenticationError(Exception):
    """认证错误"""
    def __init__(self, message: str, status_code: int = status.HTTP_401_UNAUTHORIZED):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthorizationError(Exception):
    """授权错误"""
    def __init__(self, message: str, status_code: int = status.HTTP_403_FORBIDDEN):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: JWTAuthService = Depends(get_auth_service)
) -> dict:
    """获取当前用户"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = credentials.credentials
    payload = auth_service.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if payload.token_type != TokenType.ACCESS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return {
        "user_id": payload.sub,
        "role": payload.role,
        "permissions": payload.permissions,
        "token_id": payload.jti
    }


async def get_current_active_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """获取当前活跃用户"""
    return current_user


async def get_current_admin_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """获取当前管理员用户"""
    if current_user["role"] != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: JWTAuthService = Depends(get_auth_service)
) -> Optional[dict]:
    """获取可选用户（未认证也返回None）"""
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = auth_service.verify_token(token)
    
    if not payload:
        return None
    
    return {
        "user_id": payload.sub,
        "role": payload.role,
        "permissions": payload.permissions
    }


def require_roles(*roles: UserRole):
    """角色依赖装饰器"""
    async def role_checker(
        current_user: dict = Depends(get_current_user)
    ) -> dict:
        if current_user["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {[r.value for r in roles]}"
            )
        return current_user
    return role_checker


def require_permissions(*permissions: str):
    """权限依赖装饰器"""
    async def permission_checker(
        current_user: dict = Depends(get_current_user)
    ) -> dict:
        user_permissions = set(current_user.get("permissions", []))
        required_permissions = set(permissions)
        
        if not required_permissions.issubset(user_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required permissions: {list(required_permissions)}"
            )
        return current_user
    return permission_checker


def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """简单的速率限制装饰器"""
    request_counts: dict = {}
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            client_ip = kwargs.get("request").client.host
            
            now = datetime.now(timezone.utc)
            key = f"{client_ip}:{now.minute // (window_seconds // 60)}"
            
            count = request_counts.get(key, 0)
            if count >= max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )
            
            request_counts[key] = count + 1
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


from datetime import datetime, timezone


class APIKeyAuth:
    """API密钥认证"""
    
    @staticmethod
    async def verify_api_key(
        api_key: Optional[str] = None,
        auth_service: JWTAuthService = Depends(get_auth_service)
    ) -> Optional[dict]:
        """验证API密钥"""
        if not api_key:
            return None
        
        return auth_service.verify_api_key(api_key)
