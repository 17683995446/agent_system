"""
Phase 49: 安全认证与授权核心模块
包含 JWT、API Key、权限控制、租户隔离等安全功能
"""

import os
import sys
import uuid
import time
import hmac
import hashlib
import base64
import secrets
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Set
from enum import Enum
from dataclasses import dataclass, field
import json
import re
import threading

# 配置日志
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'phase49_security.log')
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] [%(thread)d:%(name)s:%(lineno)d] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== 枚举定义 ====================

class AuthMethod(Enum):
    """认证方法"""
    JWT = "jwt"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    BASIC = "basic"

class Permission(Enum):
    """权限枚举"""
    TENANT_READ = "tenant:read"
    TENANT_WRITE = "tenant:write"
    TENANT_DELETE = "tenant:delete"
    TENANT_ADMIN = "tenant:admin"
    SERVICE_READ = "service:read"
    SERVICE_WRITE = "service:write"
    SERVICE_DELETE = "service:delete"
    ADMIN_ALL = "admin:all"

class TokenType(Enum):
    """Token类型"""
    ACCESS = "access"
    REFRESH = "refresh"
    API_KEY = "api_key"

# ==================== 安全配置 ====================

@dataclass
class SecurityConfig:
    """安全配置"""
    jwt_secret_key: str = field(default_factory=lambda: os.getenv("JWT_SECRET", secrets.token_hex(32)))
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    api_key_length: int = 32
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    min_password_length: int = 8
    require_special_chars: bool = True
    bcrypt_rounds: int = 12
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    
    # CORS
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = field(default_factory=lambda: ["*"])
    cors_allow_headers: List[str] = field(default_factory=lambda: ["*"])

# 全局配置
security_config = SecurityConfig()

# ==================== JWT Token 管理 ====================

class TokenManager:
    """Token 管理器"""
    
    def __init__(self, config: SecurityConfig = None):
        self.config = config or security_config
        self._blacklist: Set[str] = set()
        self._blacklist_lock = threading.RLock()
        logger.info("[TokenManager] TokenManager 初始化完成")
    
    def _get_current_time(self) -> datetime:
        """获取当前时间（带日志）"""
        now = datetime.now(timezone.utc)
        logger.debug(f"[TokenManager._get_current_time] 当前时间: {now}")
        return now
    
    def generate_access_token(self, user_id: str, tenant_id: str, 
                            permissions: List[str] = None,
                            additional_claims: Dict = None) -> str:
        """生成访问令牌（带日志）"""
        logger.info(f"[TokenManager.generate_access_token] 生成访问令牌: user_id={user_id}, tenant_id={tenant_id}")
        
        now = self._get_current_time()
        expire = now + timedelta(minutes=self.config.access_token_expire_minutes)
        
        payload = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "iat": now,
            "exp": expire,
            "type": TokenType.ACCESS.value,
            "jti": str(uuid.uuid4()),
            "permissions": permissions or [],
            **(additional_claims or {})
        }
        
        logger.debug(f"[TokenManager.generate_access_token] Token payload: {payload}")
        
        # 简化版 JWT（实际应使用 PyJWT）
        header = {"alg": self.config.jwt_algorithm, "typ": "JWT"}
        header_b64 = self._base64url_encode(json.dumps(header))
        payload_b64 = self._base64url_encode(json.dumps(payload, default=str))
        
        signature = self._sign(f"{header_b64}.{payload_b64}")
        
        token = f"{header_b64}.{payload_b64}.{signature}"
        logger.info(f"[TokenManager.generate_access_token] Token生成成功: {token[:50]}...")
        
        return token
    
    def generate_refresh_token(self, user_id: str, tenant_id: str) -> str:
        """生成刷新令牌（带日志）"""
        logger.info(f"[TokenManager.generate_refresh_token] 生成刷新令牌: user_id={user_id}")
        
        now = self._get_current_time()
        expire = now + timedelta(days=self.config.refresh_token_expire_days)
        
        payload = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "iat": now,
            "exp": expire,
            "type": TokenType.REFRESH.value,
            "jti": str(uuid.uuid4())
        }
        
        header = {"alg": self.config.jwt_algorithm, "typ": "JWT"}
        header_b64 = self._base64url_encode(json.dumps(header))
        payload_b64 = self._base64url_encode(json.dumps(payload, default=str))
        
        signature = self._sign(f"{header_b64}.{payload_b64}")
        
        token = f"{header_b64}.{payload_b64}.{signature}"
        logger.info(f"[TokenManager.generate_refresh_token] RefreshToken生成成功: {token[:50]}...")
        
        return token
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """验证令牌（带日志）"""
        logger.debug(f"[TokenManager.verify_token] 验证令牌: {token[:50]}...")
        
        try:
            parts = token.split(".")
            if len(parts) != 3:
                logger.warning(f"[TokenManager.verify_token] Token格式错误: parts={len(parts)}")
                return None
            
            header_b64, payload_b64, signature = parts
            
            # 验证签名
            expected_signature = self._sign(f"{header_b64}.{payload_b64}")
            if not hmac.compare_digest(signature, expected_signature):
                logger.warning(f"[TokenManager.verify_token] 签名验证失败")
                return None
            
            # 解析 payload
            payload = json.loads(self._base64url_decode(payload_b64))
            logger.debug(f"[TokenManager.verify_token] Token payload解析成功: {payload}")
            
            # 检查是否在黑名单
            jti = payload.get("jti")
            if jti and self.is_token_blacklisted(jti):
                logger.warning(f"[TokenManager.verify_token] Token已在黑名单: jti={jti}")
                return None
            
            # 检查过期
            exp = datetime.fromisoformat(payload["exp"].replace("Z", "+00:00")) if isinstance(payload["exp"], str) else payload["exp"]
            if exp < self._get_current_time():
                logger.warning(f"[TokenManager.verify_token] Token已过期: exp={exp}")
                return None
            
            logger.info(f"[TokenManager.verify_token] Token验证成功: sub={payload.get('sub')}")
            return payload
            
        except Exception as e:
            logger.error(f"[TokenManager.verify_token] Token验证异常: {e}", exc_info=True)
            return None
    
    def revoke_token(self, token: str) -> bool:
        """撤销令牌（带日志）"""
        logger.info(f"[TokenManager.revoke_token] 撤销令牌: {token[:50]}...")
        
        payload = self.verify_token(token)
        if not payload:
            logger.warning(f"[TokenManager.revoke_token] 无法撤销无效Token")
            return False
        
        jti = payload.get("jti")
        if jti:
            with self._blacklist_lock:
                self._blacklist.add(jti)
                logger.info(f"[TokenManager.revoke_token] Token已加入黑名单: jti={jti}")
        
        return True
    
    def is_token_blacklisted(self, jti: str) -> bool:
        """检查令牌是否在黑名单（带日志）"""
        with self._blacklist_lock:
            result = jti in self._blacklist
            logger.debug(f"[TokenManager.is_token_blacklisted] jti={jti}, blacklisted={result}")
            return result
    
    def _sign(self, data: str) -> str:
        """签名（带日志）"""
        signature = hmac.new(
            self.config.jwt_secret_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        logger.debug(f"[TokenManager._sign] 签名完成: {signature[:20]}...")
        return signature
    
    def _base64url_encode(self, data: str) -> str:
        """Base64 URL 安全编码（带日志）"""
        encoded = base64.urlsafe_b64encode(data.encode()).decode().rstrip("=")
        logger.debug(f"[TokenManager._base64url_encode] 编码完成: {encoded[:20]}...")
        return encoded
    
    def _base64url_decode(self, data: str) -> str:
        """Base64 URL 安全解码（带日志）"""
        padded = data + "=" * (4 - len(data) % 4)
        decoded = base64.urlsafe_b64decode(padded).decode()
        logger.debug(f"[TokenManager._base64url_decode] 解码完成")
        return decoded

# ==================== API Key 管理 ====================

class APIKeyManager:
    """API Key 管理器"""
    
    def __init__(self):
        self._api_keys: Dict[str, Dict] = {}
        self._keys_by_tenant: Dict[str, Set[str]] = {}
        self._lock = threading.RLock()
        logger.info("[APIKeyManager] APIKeyManager 初始化完成")
    
    def generate_api_key(self, tenant_id: str, name: str = None,
                        permissions: List[str] = None,
                        expires_in_days: int = None) -> Dict[str, str]:
        """生成 API Key（带日志）"""
        logger.info(f"[APIKeyManager.generate_api_key] 生成API Key: tenant_id={tenant_id}, name={name}")
        
        key_id = f"ak_{secrets.token_hex(8)}"
        key_secret = secrets.token_hex(security_config.api_key_length)
        
        # 生成哈希值用于存储
        key_hash = self._hash_key(key_secret)
        
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
        
        api_key_data = {
            "key_id": key_id,
            "key_hash": key_hash,
            "tenant_id": tenant_id,
            "name": name or f"API Key {key_id}",
            "permissions": permissions or [],
            "created_at": datetime.now(timezone.utc),
            "expires_at": expires_at,
            "last_used": None,
            "is_active": True
        }
        
        with self._lock:
            self._api_keys[key_id] = api_key_data
            if tenant_id not in self._keys_by_tenant:
                self._keys_by_tenant[tenant_id] = set()
            self._keys_by_tenant[tenant_id].add(key_id)
        
        logger.info(f"[APIKeyManager.generate_api_key] API Key生成成功: key_id={key_id}")
        
        # 返回完整key（只显示一次）
        full_key = f"{key_id}_{key_secret}"
        logger.warning(f"[APIKeyManager.generate_api_key] 完整Key已生成，请妥善保管: {full_key[:50]}...")
        
        return {
            "key_id": key_id,
            "full_key": full_key,
            "name": api_key_data["name"],
            "expires_at": expires_at,
            "permissions": permissions
        }
    
    def verify_api_key(self, full_key: str) -> Optional[Dict]:
        """验证 API Key（带日志）"""
        logger.debug(f"[APIKeyManager.verify_api_key] 验证API Key")
        
        try:
            if "_" not in full_key:
                logger.warning(f"[APIKeyManager.verify_api_key] Key格式错误")
                return None
            
            key_id, key_secret = full_key.split("_", 1)
            
            with self._lock:
                if key_id not in self._api_keys:
                    logger.warning(f"[APIKeyManager.verify_api_key] Key不存在: key_id={key_id}")
                    return None
                
                api_key_data = self._api_keys[key_id]
                
                # 检查是否激活
                if not api_key_data["is_active"]:
                    logger.warning(f"[APIKeyManager.verify_api_key] Key已停用: key_id={key_id}")
                    return None
                
                # 检查过期
                if api_key_data["expires_at"]:
                    if datetime.now(timezone.utc) > api_key_data["expires_at"]:
                        logger.warning(f"[APIKeyManager.verify_api_key] Key已过期: key_id={key_id}")
                        return None
                
                # 验证哈希
                key_hash = self._hash_key(key_secret)
                if not hmac.compare_digest(key_hash, api_key_data["key_hash"]):
                    logger.warning(f"[APIKeyManager.verify_api_key] Key哈希不匹配")
                    return None
                
                # 更新最后使用时间
                api_key_data["last_used"] = datetime.now(timezone.utc)
                
                logger.info(f"[APIKeyManager.verify_api_key] API Key验证成功: key_id={key_id}, tenant_id={api_key_data['tenant_id']}")
                return api_key_data
                
        except Exception as e:
            logger.error(f"[APIKeyManager.verify_api_key] 验证异常: {e}", exc_info=True)
            return None
    
    def revoke_api_key(self, key_id: str) -> bool:
        """撤销 API Key（带日志）"""
        logger.info(f"[APIKeyManager.revoke_api_key] 撤销API Key: key_id={key_id}")
        
        with self._lock:
            if key_id not in self._api_keys:
                logger.warning(f"[APIKeyManager.revoke_api_key] Key不存在: {key_id}")
                return False
            
            self._api_keys[key_id]["is_active"] = False
            logger.info(f"[APIKeyManager.revoke_api_key] API Key已停用: {key_id}")
            return True
    
    def list_keys_for_tenant(self, tenant_id: str) -> List[Dict]:
        """列出租户的所有API Keys（带日志）"""
        logger.debug(f"[APIKeyManager.list_keys_for_tenant] 列出Keys: tenant_id={tenant_id}")
        
        with self._lock:
            key_ids = self._keys_by_tenant.get(tenant_id, set())
            keys = []
            
            for kid in key_ids:
                key_data = self._api_keys.get(kid)
                if key_data:
                    keys.append({
                        "key_id": key_data["key_id"],
                        "name": key_data["name"],
                        "permissions": key_data["permissions"],
                        "created_at": key_data["created_at"].isoformat(),
                        "expires_at": key_data["expires_at"].isoformat() if key_data["expires_at"] else None,
                        "last_used": key_data["last_used"].isoformat() if key_data["last_used"] else None,
                        "is_active": key_data["is_active"]
                    })
            
            logger.debug(f"[APIKeyManager.list_keys_for_tenant] 返回 {len(keys)} 个Keys")
            return keys
    
    def _hash_key(self, key: str) -> str:
        """哈希 Key（带日志）"""
        hashed = hashlib.sha256(key.encode()).hexdigest()
        logger.debug(f"[APIKeyManager._hash_key] Key哈希完成")
        return hashed

# ==================== 权限管理器 ====================

class PermissionManager:
    """权限管理器"""
    
    def __init__(self):
        self._role_permissions: Dict[str, Set[str]] = {
            "admin": {p.value for p in Permission},
            "tenant_admin": {
                Permission.TENANT_READ.value,
                Permission.TENANT_WRITE.value,
                Permission.TENANT_ADMIN.value,
                Permission.SERVICE_READ.value,
                Permission.SERVICE_WRITE.value
            },
            "developer": {
                Permission.TENANT_READ.value,
                Permission.TENANT_WRITE.value,
                Permission.SERVICE_READ.value,
                Permission.SERVICE_WRITE.value
            },
            "viewer": {
                Permission.TENANT_READ.value,
                Permission.SERVICE_READ.value
            }
        }
        self._lock = threading.RLock()
        logger.info("[PermissionManager] PermissionManager 初始化完成")
    
    def get_permissions_for_role(self, role: str) -> Set[str]:
        """获取角色权限（带日志）"""
        logger.debug(f"[PermissionManager.get_permissions_for_role] 获取权限: role={role}")
        
        with self._lock:
            permissions = self._role_permissions.get(role, set())
            logger.debug(f"[PermissionManager.get_permissions_for_role] 返回 {len(permissions)} 个权限")
            return permissions
    
    def has_permission(self, permissions: List[str], required: str) -> bool:
        """检查权限（带日志）"""
        logger.debug(f"[PermissionManager.has_permission] 检查权限: required={required}")
        
        with self._lock:
            # 检查是否拥有管理员权限
            if Permission.ADMIN_ALL.value in permissions:
                logger.debug(f"[PermissionManager.has_permission] 拥有管理员权限")
                return True
            
            result = required in permissions
            logger.debug(f"[PermissionManager.has_permission] 权限检查结果: {result}")
            return result
    
    def has_tenant_access(self, user_tenant_id: str, target_tenant_id: str, 
                         permissions: List[str]) -> bool:
        """检查租户访问权限（带日志）"""
        logger.debug(f"[PermissionManager.has_tenant_access] 检查租户访问: user_tenant={user_tenant_id}, target_tenant={target_tenant_id}")
        
        # 管理员可以访问所有租户
        if Permission.ADMIN_ALL.value in permissions:
            logger.info(f"[PermissionManager.has_tenant_access] 管理员权限，允许访问")
            return True
        
        # 检查是否是同一租户
        if user_tenant_id == target_tenant_id:
            logger.info(f"[PermissionManager.has_tenant_access] 同一租户，允许访问")
            return True
        
        logger.warning(f"[PermissionManager.has_tenant_access] 跨租户访问被拒绝")
        return False

# ==================== 速率限制器 ====================

class RateLimiter:
    """速率限制器"""
    
    def __init__(self, config: SecurityConfig = None):
        self.config = config or security_config
        self._requests: Dict[str, List[datetime]] = {}
        self._lock = threading.RLock()
        logger.info("[RateLimiter] RateLimiter 初始化完成")
    
    def is_allowed(self, identifier: str) -> bool:
        """检查是否允许请求（带日志）"""
        logger.debug(f"[RateLimiter.is_allowed] 检查速率限制: identifier={identifier}")
        
        with self._lock:
            now = datetime.now(timezone.utc)
            window_start = now - timedelta(seconds=self.config.rate_limit_window_seconds)
            
            # 清理旧请求
            if identifier in self._requests:
                self._requests[identifier] = [
                    ts for ts in self._requests[identifier]
                    if ts > window_start
                ]
            else:
                self._requests[identifier] = []
            
            # 检查限制
            request_count = len(self._requests[identifier])
            
            if request_count >= self.config.rate_limit_requests:
                logger.warning(f"[RateLimiter.is_allowed] 请求超限: identifier={identifier}, count={request_count}")
                return False
            
            # 记录请求
            self._requests[identifier].append(now)
            logger.debug(f"[RateLimiter.is_allowed] 请求允许: identifier={identifier}, count={request_count + 1}")
            return True
    
    def get_remaining(self, identifier: str) -> int:
        """获取剩余请求次数（带日志）"""
        with self._lock:
            now = datetime.now(timezone.utc)
            window_start = now - timedelta(seconds=self.config.rate_limit_window_seconds)
            
            if identifier in self._requests:
                recent_requests = [
                    ts for ts in self._requests[identifier]
                    if ts > window_start
                ]
                remaining = max(0, self.config.rate_limit_requests - len(recent_requests))
            else:
                remaining = self.config.rate_limit_requests
            
            logger.debug(f"[RateLimiter.get_remaining] 剩余次数: {remaining}")
            return remaining
    
    def reset(self, identifier: str):
        """重置限制（带日志）"""
        logger.info(f"[RateLimiter.reset] 重置速率限制: identifier={identifier}")
        with self._lock:
            if identifier in self._requests:
                del self._requests[identifier]

# ==================== 输入验证器 ====================

class InputValidator:
    """输入验证器"""
    
    # 恶意模式
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
        r"(--|#|/\*|\*/)",
        r"(\bOR\b|\bAND\b).*=.*",
        r"('|\"|;|\\)"
    ]
    
    XSS_PATTERNS = [
        r"<script",
        r"javascript:",
        r"onerror=",
        r"onload=",
        r"<iframe",
        r"eval\(",
        r"document\."
    ]
    
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"/etc/passwd",
        r"c:\\windows"
    ]
    
    @classmethod
    def validate_sql_injection(cls, value: str) -> bool:
        """验证 SQL 注入（带日志）"""
        logger.debug(f"[InputValidator.validate_sql_injection] 检查输入: {value[:50] if value else 'None'}...")
        
        if not value:
            logger.debug(f"[InputValidator.validate_sql_injection] 输入为空，跳过检查")
            return True
        
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"[InputValidator.validate_sql_injection] 检测到SQL注入: pattern={pattern}")
                return False
        
        logger.debug(f"[InputValidator.validate_sql_injection] 通过检查")
        return True
    
    @classmethod
    def validate_xss(cls, value: str) -> bool:
        """验证 XSS（带日志）"""
        logger.debug(f"[InputValidator.validate_xss] 检查输入: {value[:50] if value else 'None'}...")
        
        if not value:
            logger.debug(f"[InputValidator.validate_xss] 输入为空，跳过检查")
            return True
        
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"[InputValidator.validate_xss] 检测到XSS: pattern={pattern}")
                return False
        
        logger.debug(f"[InputValidator.validate_xss] 通过检查")
        return True
    
    @classmethod
    def validate_path_traversal(cls, value: str) -> bool:
        """验证路径遍历（带日志）"""
        logger.debug(f"[InputValidator.validate_path_traversal] 检查输入: {value[:50] if value else 'None'}...")
        
        if not value:
            logger.debug(f"[InputValidator.validate_path_traversal] 输入为空，跳过检查")
            return True
        
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"[InputValidator.validate_path_traversal] 检测到路径遍历: pattern={pattern}")
                return False
        
        logger.debug(f"[InputValidator.validate_path_traversal] 通过检查")
        return True
    
    @classmethod
    def sanitize_input(cls, value: str) -> str:
        """清理输入（带日志）"""
        logger.debug(f"[InputValidator.sanitize_input] 清理输入: {value[:50] if value else 'None'}...")
        
        if not value:
            return value
        
        # 移除潜在危险字符
        sanitized = value.replace("<", "&lt;").replace(">", "&gt;")
        sanitized = sanitized.replace("'", "&#39;").replace('"', "&quot;")
        
        logger.debug(f"[InputValidator.sanitize_input] 清理完成")
        return sanitized

# ==================== 全局实例 ====================

token_manager = TokenManager()
api_key_manager = APIKeyManager()
permission_manager = PermissionManager()
rate_limiter = RateLimiter()

logger.info("=" * 80)
logger.info("Phase 49: 安全模块初始化完成")
logger.info("=" * 80)

if __name__ == "__main__":
    print("=" * 80)
    print("Phase 49: 安全模块测试")
    print("=" * 80)
    
    # 测试 Token 生成和验证
    print("\n--- 测试 JWT Token ---")
    token = token_manager.generate_access_token(
        user_id="user123",
        tenant_id="tenant456",
        permissions=["tenant:read", "tenant:write"]
    )
    print(f"生成的 Token: {token[:50]}...")
    
    verified = token_manager.verify_token(token)
    print(f"验证结果: {verified}")
    
    # 测试 API Key
    print("\n--- 测试 API Key ---")
    api_key_info = api_key_manager.generate_api_key(
        tenant_id="tenant789",
        name="Test API Key",
        permissions=["tenant:read"]
    )
    print(f"API Key 信息: {api_key_info}")
    
    verified_key = api_key_manager.verify_api_key(api_key_info["full_key"])
    print(f"API Key 验证结果: {verified_key is not None}")
    
    # 测试权限检查
    print("\n--- 测试权限 ---")
    has_perm = permission_manager.has_permission(
        ["tenant:read", "tenant:write"],
        "tenant:read"
    )
    print(f"权限检查: {has_perm}")
    
    # 测试输入验证
    print("\n--- 测试输入验证 ---")
    sql_test = InputValidator.validate_sql_injection("SELECT * FROM users")
    print(f"SQL注入测试: {sql_test}")
    
    xss_test = InputValidator.validate_xss("<script>alert('xss')</script>")
    print(f"XSS测试: {xss_test}")
    
    # 测试速率限制
    print("\n--- 测试速率限制 ---")
    limiter = RateLimiter()
    for i in range(5):
        result = limiter.is_allowed("test_user")
        print(f"请求 {i+1}: {'允许' if result else '拒绝'}")
    
    print("\n" + "=" * 80)
    print("✅ Phase 49 安全模块测试完成！")
    print("=" * 80)
