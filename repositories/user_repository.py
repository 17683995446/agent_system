"""
UserRepository - 用户Repository实现
Agent永续自进化系统 - 数据持久化层
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import hashlib

from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_model import UserModel
from repositories.base_repository import BaseRepository
from infrastructure.logging.logging_system import get_logger


class UserRepository(BaseRepository[UserModel]):
    """
    用户Repository
    提供用户相关的CRUD操作
    """
    
    def __init__(self, db_session: AsyncSession):
        super().__init__(UserModel, db_session)
        self.logger = get_logger("UserRepository")
    
    async def create(self, data: Dict[str, Any]) -> UserModel:
        """
        创建用户
        
        Args:
            data: 用户数据
            
        Returns:
            创建的用户
        """
        try:
            if 'password' in data:
                data['password_hash'] = self._hash_password(data.pop('password'))
            
            user = UserModel(**data)
            self.db.add(user)
            await self.db.flush()
            await self.db.refresh(user)
            
            self.logger.info(f"User created: {user.id}, username: {user.username}")
            return user
            
        except Exception as e:
            self.logger.error(f"Error creating user: {str(e)}")
            raise
    
    async def get_by_id(self, id: str) -> Optional[UserModel]:
        """
        通过ID获取用户
        
        Args:
            id: 用户ID
            
        Returns:
            用户或None
        """
        try:
            query = select(UserModel).where(UserModel.id == id)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()
            
            if user:
                self.logger.info(f"User found: {id}")
            else:
                self.logger.warning(f"User not found: {id}")
            
            return user
            
        except Exception as e:
            self.logger.error(f"Error getting user by id: {str(e)}")
            raise
    
    async def get_by_username(self, username: str) -> Optional[UserModel]:
        """
        通过用户名获取用户
        
        Args:
            username: 用户名
            
        Returns:
            用户或None
        """
        try:
            query = select(UserModel).where(UserModel.username == username)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()
            
            if user:
                self.logger.info(f"User found by username: {username}")
            
            return user
            
        except Exception as e:
            self.logger.error(f"Error getting user by username: {str(e)}")
            raise
    
    async def get_by_email(self, email: str) -> Optional[UserModel]:
        """
        通过邮箱获取用户
        
        Args:
            email: 邮箱地址
            
        Returns:
            用户或None
        """
        try:
            query = select(UserModel).where(UserModel.email == email)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()
            
            if user:
                self.logger.info(f"User found by email: {email}")
            
            return user
            
        except Exception as e:
            self.logger.error(f"Error getting user by email: {str(e)}")
            raise
    
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[UserModel]:
        """
        更新用户
        
        Args:
            id: 用户ID
            data: 更新数据
            
        Returns:
            更新后的用户或None
        """
        try:
            if 'password' in data:
                data['password_hash'] = self._hash_password(data.pop('password'))
            
            data['updated_at'] = datetime.now(timezone.utc)
            
            query = update(UserModel).where(UserModel.id == id).values(**data)
            await self.db.execute(query)
            await self.db.flush()
            
            self.logger.info(f"User updated: {id}")
            return await self.get_by_id(id)
            
        except Exception as e:
            self.logger.error(f"Error updating user: {str(e)}")
            raise
    
    async def delete(self, id: str) -> bool:
        """
        删除用户
        
        Args:
            id: 用户ID
            
        Returns:
            是否成功
        """
        try:
            query = delete(UserModel).where(UserModel.id == id)
            result = await self.db.execute(query)
            await self.db.flush()
            
            success = result.rowcount > 0
            if success:
                self.logger.info(f"User deleted: {id}")
            else:
                self.logger.warning(f"User not found for deletion: {id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error deleting user: {str(e)}")
            raise
    
    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[UserModel]:
        """
        列出用户
        
        Args:
            skip: 跳过的记录数
            limit: 返回的记录数限制
            role: 角色过滤
            is_active: 活跃状态过滤
            search: 搜索关键词
            
        Returns:
            用户列表
        """
        try:
            query = select(UserModel)
            conditions = []
            
            if role:
                conditions.append(UserModel.role == role)
            
            if is_active is not None:
                conditions.append(UserModel.is_active == is_active)
            
            if search:
                search_pattern = f"%{search}%"
                conditions.append(
                    or_(
                        UserModel.username.ilike(search_pattern),
                        UserModel.email.ilike(search_pattern),
                        UserModel.first_name.ilike(search_pattern),
                        UserModel.last_name.ilike(search_pattern)
                    )
                )
            
            if conditions:
                query = query.where(and_(*conditions))
            
            query = query.order_by(UserModel.created_at.desc()).offset(skip).limit(limit)
            
            result = await self.db.execute(query)
            users = result.scalars().all()
            
            self.logger.info(f"Listed {len(users)} users")
            return list(users)
            
        except Exception as e:
            self.logger.error(f"Error listing users: {str(e)}")
            raise
    
    async def count_users(
        self,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> int:
        """
        统计用户数量
        
        Args:
            role: 角色过滤
            is_active: 活跃状态过滤
            
        Returns:
            用户数量
        """
        try:
            query = select(func.count()).select_from(UserModel)
            conditions = []
            
            if role:
                conditions.append(UserModel.role == role)
            
            if is_active is not None:
                conditions.append(UserModel.is_active == is_active)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            result = await self.db.execute(query)
            count = result.scalar()
            
            return count or 0
            
        except Exception as e:
            self.logger.error(f"Error counting users: {str(e)}")
            raise
    
    async def update_last_login(self, id: str) -> bool:
        """
        更新最后登录时间
        
        Args:
            id: 用户ID
            
        Returns:
            是否成功
        """
        try:
            query = update(UserModel).where(UserModel.id == id).values(
                last_login=datetime.now(timezone.utc)
            )
            result = await self.db.execute(query)
            await self.db.flush()
            
            return result.rowcount > 0
            
        except Exception as e:
            self.logger.error(f"Error updating last login: {str(e)}")
            raise
    
    async def verify_password(self, username: str, password: str) -> Optional[UserModel]:
        """
        验证用户密码
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            用户或None
        """
        try:
            user = await self.get_by_username(username)
            
            if not user:
                return None
            
            password_hash = self._hash_password(password)
            
            if user.password_hash == password_hash:
                self.logger.info(f"Password verified for user: {username}")
                return user
            else:
                self.logger.warning(f"Invalid password for user: {username}")
                return None
            
        except Exception as e:
            self.logger.error(f"Error verifying password: {str(e)}")
            raise
    
    async def change_password(self, id: str, new_password: str) -> bool:
        """
        修改密码
        
        Args:
            id: 用户ID
            new_password: 新密码
            
        Returns:
            是否成功
        """
        try:
            password_hash = self._hash_password(new_password)
            
            query = update(UserModel).where(UserModel.id == id).values(
                password_hash=password_hash,
                updated_at=datetime.now(timezone.utc)
            )
            result = await self.db.execute(query)
            await self.db.flush()
            
            success = result.rowcount > 0
            if success:
                self.logger.info(f"Password changed for user: {id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error changing password: {str(e)}")
            raise
    
    async def deactivate(self, id: str) -> bool:
        """
        禁用用户
        
        Args:
            id: 用户ID
            
        Returns:
            是否成功
        """
        return await self.update(id, {"is_active": False}) is not None
    
    async def activate(self, id: str) -> bool:
        """
        启用用户
        
        Args:
            id: 用户ID
            
        Returns:
            是否成功
        """
        return await self.update(id, {"is_active": True}) is not None
    
    async def username_exists(self, username: str) -> bool:
        """
        检查用户名是否存在
        
        Args:
            username: 用户名
            
        Returns:
            是否存在
        """
        try:
            user = await self.get_by_username(username)
            return user is not None
            
        except Exception as e:
            self.logger.error(f"Error checking username existence: {str(e)}")
            raise
    
    async def email_exists(self, email: str) -> bool:
        """
        检查邮箱是否存在
        
        Args:
            email: 邮箱地址
            
        Returns:
            是否存在
        """
        try:
            user = await self.get_by_email(email)
            return user is not None
            
        except Exception as e:
            self.logger.error(f"Error checking email existence: {str(e)}")
            raise
    
    def _hash_password(self, password: str) -> str:
        """
        哈希密码
        
        Args:
            password: 原始密码
            
        Returns:
            哈希后的密码
        """
        return hashlib.sha256(password.encode()).hexdigest()
