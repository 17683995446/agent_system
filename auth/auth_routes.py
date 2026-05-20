"""
认证路由 - 用户认证和授权API
"""
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Depends, Request
from pydantic import BaseModel, EmailStr, Field
import hashlib

from auth.jwt_auth_service import get_auth_service, UserRole
from auth.dependencies import get_current_user, get_current_admin_user

router = APIRouter()


class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field(default="user")


class UserLoginRequest(BaseModel):
    username: str
    password: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    user_id: str
    username: str
    email: str
    role: str
    is_active: bool
    created_at: str
    last_login: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    refresh_expires_in: int


_mock_users_db = {}


def hash_password(password: str) -> str:
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return hash_password(plain_password) == hashed_password


@router.post("/register", response_model=TokenResponse)
async def register(request: UserRegisterRequest):
    """用户注册"""
    auth_service = get_auth_service()
    
    if request.username in _mock_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    user_id = f"user_{len(_mock_users_db) + 1}"
    hashed_password = hash_password(request.password)
    
    role = UserRole.USER
    if request.role == "admin":
        role = UserRole.ADMIN
    
    _mock_users_db[request.username] = {
        "user_id": user_id,
        "username": request.username,
        "email": request.email,
        "password_hash": hashed_password,
        "role": role,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "last_login": None
    }
    
    token_pair = auth_service.generate_token_pair(
        user_id=user_id,
        role=role,
        permissions=[]
    )
    
    return TokenResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        token_type=token_pair.token_type,
        expires_in=token_pair.expires_in,
        refresh_expires_in=token_pair.refresh_expires_in
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: UserLoginRequest):
    """用户登录"""
    auth_service = get_auth_service()
    
    user = _mock_users_db.get(request.username)
    
    if not user or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    user["last_login"] = datetime.now(timezone.utc)
    
    token_pair = auth_service.generate_token_pair(
        user_id=user["user_id"],
        role=user["role"],
        permissions=[]
    )
    
    return TokenResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        token_type=token_pair.token_type,
        expires_in=token_pair.expires_in,
        refresh_expires_in=token_pair.refresh_expires_in
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: TokenRefreshRequest):
    """刷新Token"""
    auth_service = get_auth_service()
    
    new_tokens = auth_service.refresh_access_token(request.refresh_token)
    
    if not new_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return TokenResponse(
        access_token=new_tokens.access_token,
        refresh_token=new_tokens.refresh_token,
        token_type=new_tokens.token_type,
        expires_in=new_tokens.expires_in,
        refresh_expires_in=new_tokens.refresh_expires_in
    )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """用户登出"""
    auth_service = get_auth_service()
    
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        auth_service.blacklist_token(token)
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user)
):
    """获取当前用户信息"""
    for username, user_data in _mock_users_db.items():
        if user_data["user_id"] == current_user["user_id"]:
            return UserResponse(
                user_id=user_data["user_id"],
                username=user_data["username"],
                email=user_data["email"],
                role=user_data["role"].value,
                is_active=user_data["is_active"],
                created_at=user_data["created_at"].isoformat(),
                last_login=user_data["last_login"].isoformat() if user_data["last_login"] else None
            )
    
    return UserResponse(
        user_id=current_user["user_id"],
        username="unknown",
        email="unknown@example.com",
        role=current_user["role"].value,
        is_active=True,
        created_at=datetime.now(timezone.utc).isoformat()
    )


@router.post("/change-password")
async def change_password(
    request: PasswordChangeRequest,
    current_user: dict = Depends(get_current_user)
):
    """修改密码"""
    for username, user_data in _mock_users_db.items():
        if user_data["user_id"] == current_user["user_id"]:
            if not verify_password(request.old_password, user_data["password_hash"]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Incorrect old password"
                )
            
            user_data["password_hash"] = hash_password(request.new_password)
            return {"message": "Password changed successfully"}
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )


@router.get("/users", response_model=list)
async def list_users(
    current_user: dict = Depends(get_current_admin_user)
):
    """列出所有用户（仅管理员）"""
    users = []
    for username, user_data in _mock_users_db.items():
        users.append(UserResponse(
            user_id=user_data["user_id"],
            username=user_data["username"],
            email=user_data["email"],
            role=user_data["role"].value,
            is_active=user_data["is_active"],
            created_at=user_data["created_at"].isoformat(),
            last_login=user_data["last_login"].isoformat() if user_data["last_login"] else None
        ))
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """获取指定用户信息（仅管理员）"""
    for username, user_data in _mock_users_db.items():
        if user_data["user_id"] == user_id:
            return UserResponse(
                user_id=user_data["user_id"],
                username=user_data["username"],
                email=user_data["email"],
                role=user_data["role"].value,
                is_active=user_data["is_active"],
                created_at=user_data["created_at"].isoformat(),
                last_login=user_data["last_login"].isoformat() if user_data["last_login"] else None
            )
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """删除用户（仅管理员）"""
    for username, user_data in list(_mock_users_db.items()):
        if user_data["user_id"] == user_id:
            del _mock_users_db[username]
            return {"message": "User deleted successfully"}
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )


@router.get("/token/info")
async def get_token_info(request: Request):
    """获取Token信息"""
    auth_service = get_auth_service()
    
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    token = auth_header[7:]
    token_info = auth_service.get_token_info(token)
    
    if not token_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    return token_info
