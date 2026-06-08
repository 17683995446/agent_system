"""
测试 - JWT认证模块单元测试
"""
import pytest
from datetime import timedelta
from api_access.auth_jwt_token_manager import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token,
    get_password_hash,
    verify_password,
    TokenManager,
    UserRole,
    AuthenticatedUser,
)


class TestPasswordHashing:
    """测试密码哈希功能"""
    
    def test_password_hash_creates_hash(self):
        """测试密码哈希创建"""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 20
    
    def test_password_verification_correct(self):
        """测试正确密码验证"""
        password = "correct_password"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_password_verification_incorrect(self):
        """测试错误密码验证"""
        password = "correct_password"
        hashed = get_password_hash(password)
        
        assert verify_password("wrong_password", hashed) is False


class TestTokenCreation:
    """测试令牌创建"""
    
    def test_create_access_token(self):
        """测试创建访问令牌"""
        data = {"sub": "user123", "username": "testuser"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50
    
    def test_create_access_token_with_expiry(self):
        """测试创建带过期时间的令牌"""
        data = {"sub": "user123"}
        expires = timedelta(minutes=60)
        token = create_access_token(data, expires_delta=expires)
        
        assert token is not None
    
    def test_create_refresh_token(self):
        """测试创建刷新令牌"""
        data = {"sub": "user123"}
        token = create_refresh_token(data)
        
        assert token is not None
        assert len(token) > 50


class TestTokenDecoding:
    """测试令牌解码"""
    
    def test_decode_valid_token(self):
        """测试解码有效令牌"""
        data = {"sub": "user123", "username": "testuser"}
        token = create_access_token(data)
        
        decoded = decode_token(token)
        
        assert decoded is not None
        assert decoded["sub"] == "user123"
        assert decoded["username"] == "testuser"
    
    def test_decode_invalid_token(self):
        """测试解码无效令牌"""
        invalid_token = "invalid.token.here"
        
        decoded = decode_token(invalid_token)
        
        assert decoded is None
    
    def test_verify_valid_token(self):
        """测试验证有效令牌"""
        data = {"sub": "user123"}
        token = create_access_token(data)
        
        assert verify_token(token) is True
    
    def test_verify_invalid_token(self):
        """测试验证无效令牌"""
        assert verify_token("invalid_token") is False


class TestTokenManager:
    """测试令牌管理器"""
    
    def test_create_token_pair(self):
        """测试创建令牌对"""
        manager = TokenManager()
        
        tokens = manager.create_token_pair(
            user_id="user123",
            username="testuser",
            roles=[UserRole.USER.value]
        )
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
    
    def test_refresh_access_token(self):
        """测试刷新访问令牌"""
        manager = TokenManager()
        
        tokens = manager.create_token_pair(
            user_id="user123",
            username="testuser"
        )
        
        new_tokens = manager.refresh_access_token(tokens["refresh_token"])
        
        assert new_tokens is not None
        assert "access_token" in new_tokens
        assert "token_type" in new_tokens
    
    def test_blacklist_token(self):
        """测试令牌黑名单"""
        manager = TokenManager()
        
        tokens = manager.create_token_pair(user_id="user123", username="testuser")
        
        manager.blacklist_token(tokens["access_token"])
        
        assert manager.is_blacklisted(tokens["access_token"]) is True
        assert manager.is_blacklisted(tokens["refresh_token"]) is False
    
    def test_refresh_blacklisted_token(self):
        """测试刷新已黑名单的令牌"""
        manager = TokenManager()
        
        tokens = manager.create_token_pair(user_id="user123", username="testuser")
        
        manager.blacklist_token(tokens["refresh_token"])
        
        result = manager.refresh_access_token(tokens["refresh_token"])
        
        assert result is None
