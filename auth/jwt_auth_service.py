"""
认证服务 - JWT Token管理和验证
Agent永续自进化系统 - 安全性层
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import secrets

import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

from infrastructure.logging.logging_system import get_logger


class TokenType(str, Enum):
    """Token类型"""
    ACCESS = "access"
    REFRESH = "refresh"
    API_KEY = "api_key"


class UserRole(str, Enum):
    """用户角色"""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"
    SERVICE = "service"


@dataclass
class TokenPayload:
    """Token载荷"""
    sub: str
    role: UserRole
    token_type: TokenType
    exp: datetime
    iat: datetime
    jti: str
    permissions: list = field(default_factory=list)


@dataclass
class AuthToken:
    """认证Token"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600
    refresh_expires_in: int = 86400


@dataclass
class User:
    """用户对象"""
    user_id: str
    username: str
    email: str
    role: UserRole
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    permissions: list = field(default_factory=list)


class JWTAuthService:
    """JWT认证服务"""

    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 60,
        refresh_token_expire_days: int = 7
    ):
        self.logger = get_logger("JWTAuthService")
        
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.algorithm = algorithm
        self.access_token_expire = timedelta(minutes=access_token_expire_minutes)
        self.refresh_token_expire = timedelta(days=refresh_token_expire_days)
        
        self._blacklisted_tokens: set = set()
        
        self.logger.info("JWTAuthService initialized")

    def generate_access_token(
        self,
        user_id: str,
        role: UserRole,
        permissions: Optional[list] = None,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """生成访问令牌"""
        now = datetime.now(timezone.utc)
        jti = secrets.token_urlsafe(16)
        
        payload = {
            "sub": user_id,
            "role": role.value,
            "type": TokenType.ACCESS.value,
            "exp": now + self.access_token_expire,
            "iat": now,
            "jti": jti,
            "permissions": permissions or [],
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        self.logger.info(f"Access token generated for user: {user_id}")
        
        return token

    def generate_refresh_token(
        self,
        user_id: str,
        role: UserRole
    ) -> str:
        """生成刷新令牌"""
        now = datetime.now(timezone.utc)
        jti = secrets.token_urlsafe(16)
        
        payload = {
            "sub": user_id,
            "role": role.value,
            "type": TokenType.REFRESH.value,
            "exp": now + self.refresh_token_expire,
            "iat": now,
            "jti": jti
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        self.logger.info(f"Refresh token generated for user: {user_id}")
        
        return token

    def generate_token_pair(
        self,
        user_id: str,
        role: UserRole,
        permissions: Optional[list] = None,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> AuthToken:
        """生成Token对"""
        access_token = self.generate_access_token(
            user_id, role, permissions, additional_claims
        )
        refresh_token = self.generate_refresh_token(user_id, role)
        
        return AuthToken(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=int(self.access_token_expire.total_seconds()),
            refresh_expires_in=int(self.refresh_token_expire.total_seconds())
        )

    def verify_token(self, token: str) -> Optional[TokenPayload]:
        """验证Token"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            if payload.get("jti") in self._blacklisted_tokens:
                self.logger.warning("Token is blacklisted")
                return None
            
            return TokenPayload(
                sub=payload["sub"],
                role=UserRole(payload["role"]),
                token_type=TokenType(payload["type"]),
                exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
                iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
                jti=payload["jti"],
                permissions=payload.get("permissions", [])
            )
            
        except ExpiredSignatureError:
            self.logger.warning("Token has expired")
            return None
        except InvalidTokenError as e:
            self.logger.error(f"Invalid token: {str(e)}")
            return None

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """解码Token（不验证）"""
        try:
            return jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_signature": False}
            )
        except Exception as e:
            self.logger.error(f"Failed to decode token: {str(e)}")
            return None

    def blacklist_token(self, token: str) -> bool:
        """将Token加入黑名单"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_signature": False}
            )
            jti = payload.get("jti")
            if jti:
                self._blacklisted_tokens.add(jti)
                self.logger.info(f"Token blacklisted: {jti}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to blacklist token: {str(e)}")
        return False

    def get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        """获取Token信息"""
        payload = self.decode_token(token)
        if not payload:
            return None
        
        return {
            "user_id": payload.get("sub"),
            "role": payload.get("role"),
            "type": payload.get("type"),
            "expires_at": datetime.fromtimestamp(
                payload["exp"], tz=timezone.utc
            ).isoformat() if "exp" in payload else None,
            "issued_at": datetime.fromtimestamp(
                payload["iat"], tz=timezone.utc
            ).isoformat() if "iat" in payload else None,
            "is_expired": datetime.now(timezone.utc).timestamp() > payload.get("exp", 0),
            "is_blacklisted": payload.get("jti") in self._blacklisted_tokens
        }

    def refresh_access_token(self, refresh_token: str) -> Optional[AuthToken]:
        """使用刷新令牌获取新的访问令牌"""
        payload = self.verify_token(refresh_token)
        
        if not payload or payload.token_type != TokenType.REFRESH:
            return None
        
        new_access_token = self.generate_access_token(
            user_id=payload.sub,
            role=payload.role
        )
        
        new_refresh_token = self.generate_refresh_token(
            user_id=payload.sub,
            role=payload.role
        )
        
        self.blacklist_token(refresh_token)
        
        return AuthToken(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=int(self.access_token_expire.total_seconds()),
            refresh_expires_in=int(self.refresh_token_expire.total_seconds())
        )

    def generate_api_key(self, user_id: str, role: UserRole) -> str:
        """生成API密钥"""
        api_key = f"ags_{secrets.token_urlsafe(32)}"
        
        self.logger.info(f"API key generated for user: {user_id}")
        
        return api_key

    def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """验证API密钥"""
        if api_key.startswith("ags_"):
            return {
                "valid": True,
                "user_id": "api_user",
                "role": UserRole.SERVICE
            }
        return None


_auth_service: Optional[JWTAuthService] = None


def get_auth_service() -> JWTAuthService:
    """获取认证服务单例"""
    global _auth_service
    if _auth_service is None:
        _auth_service = JWTAuthService()
    return _auth_service
