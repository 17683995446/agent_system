"""
API接入层 - JWT认证授权模块
提供JWT令牌生成、验证和授权功能
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from jose import JWTError, jwt
import bcrypt
from pydantic import BaseModel, Field
from enum import Enum


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

try:
    SECRET_KEY = "your-secret-key-here-change-in-production"
except Exception:
    SECRET_KEY = "dev-secret-key-please-change"


class TokenType(str, Enum):
    """令牌类型"""
    ACCESS = "access"
    REFRESH = "refresh"


class TokenData(BaseModel):
    """令牌数据"""
    sub: str
    exp: datetime
    iat: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    token_type: TokenType = TokenType.ACCESS
    roles: List[str] = Field(default_factory=list)


class UserRole(str, Enum):
    """用户角色"""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class AuthenticatedUser(BaseModel):
    """认证用户模型"""
    user_id: str
    username: str
    roles: List[str] = Field(default_factory=list)
    is_active: bool = True


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        password_bytes = plain_password.encode('utf-8')[:72]
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "token_type": TokenType.ACCESS.value
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """创建刷新令牌"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "token_type": TokenType.REFRESH.value
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """解码令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def verify_token(token: str) -> bool:
    """验证令牌是否有效"""
    payload = decode_token(token)
    if not payload:
        return False
    
    exp = payload.get("exp")
    if not exp:
        return False
    
    exp_datetime = datetime.fromtimestamp(exp, tz=timezone.utc)
    if exp_datetime < datetime.now(timezone.utc):
        return False
    
    return True


def get_user_from_token(token: str) -> Optional[AuthenticatedUser]:
    """从令牌获取用户信息"""
    payload = decode_token(token)
    if not payload:
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    return AuthenticatedUser(
        user_id=user_id,
        username=payload.get("username", user_id),
        roles=payload.get("roles", []),
        is_active=payload.get("is_active", True)
    )


class RoleChecker:
    """角色检查器"""
    
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, user: AuthenticatedUser) -> bool:
        if not user.is_active:
            return False
        
        if UserRole.ADMIN.value in user.roles:
            return True
        
        for role in self.allowed_roles:
            if role in user.roles:
                return True
        
        return False


def require_roles(*roles: str):
    """角色装饰器"""
    def decorator(func):
        func._required_roles = list(roles)
        return func
    return decorator


class TokenManager:
    """令牌管理器"""
    
    def __init__(self):
        self._blacklist: set = set()
    
    def blacklist_token(self, token: str):
        """将令牌加入黑名单"""
        self._blacklist.add(token)
    
    def is_blacklisted(self, token: str) -> bool:
        """检查令牌是否在黑名单"""
        return token in self._blacklist
    
    def create_token_pair(
        self,
        user_id: str,
        username: str,
        roles: List[str] = None
    ) -> Dict[str, str]:
        """创建令牌对"""
        if roles is None:
            roles = [UserRole.USER.value]
        
        data = {
            "sub": user_id,
            "username": username,
            "roles": roles
        }
        
        return {
            "access_token": create_access_token(data),
            "refresh_token": create_refresh_token(data),
            "token_type": "bearer"
        }
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """使用刷新令牌刷新访问令牌"""
        payload = decode_token(refresh_token)
        if not payload:
            return None
        
        if payload.get("token_type") != TokenType.REFRESH.value:
            return None
        
        if self.is_blacklisted(refresh_token):
            return None
        
        new_data = {
            "sub": payload.get("sub"),
            "username": payload.get("username"),
            "roles": payload.get("roles", [])
        }
        
        return {
            "access_token": create_access_token(new_data),
            "token_type": "bearer"
        }


token_manager = TokenManager()
