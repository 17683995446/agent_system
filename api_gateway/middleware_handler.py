"""
中间件处理器
处理跨域、日志、认证等中间件逻辑
"""
from typing import Callable, Dict, Any
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求并记录日志"""
        logger = logging.getLogger("api_gateway")
        
        request_id = request.headers.get("X-Request-ID", "unknown")
        start_time = time.time()
        
        logger.info(
            f"请求开始: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
            }
        )
        
        try:
            response = await call_next(request)
            
            duration = time.time() - start_time
            
            logger.info(
                f"请求完成: {request.method} {request.url.path} - 状态码: {response.status_code}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration": duration,
                }
            )
            
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(duration)
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            logger.error(
                f"请求失败: {request.method} {request.url.path} - 错误: {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "duration": duration,
                }
            )
            
            raise


class RateLimitMiddleware(BaseHTTPMiddleware):
    """速率限制中间件"""
    
    def __init__(self, app, max_requests_per_minute: int = 100):
        super().__init__(app)
        self.max_requests_per_minute = max_requests_per_minute
        self.request_counts: Dict[str, list] = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理速率限制"""
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        
        self.request_counts[client_ip] = [
            req_time for req_time in self.request_counts[client_ip]
            if current_time - req_time < 60
        ]
        
        if len(self.request_counts[client_ip]) >= self.max_requests_per_minute:
            return Response(
                content="Rate limit exceeded",
                status_code=429,
                headers={"Retry-After": "60"}
            )
        
        self.request_counts[client_ip].append(current_time)
        
        return await call_next(request)


class MiddlewareHandler:
    """中间件处理器"""
    
    def __init__(self, app, gateway_config):
        self.app = app
        self.config = gateway_config
        self.logger = logging.getLogger("api_gateway")
    
    def setup_cors_middleware(self) -> None:
        """设置CORS中间件"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.cors_allowed_origins,
            allow_credentials=True,
            allow_methods=self.config.cors_allowed_methods,
            allow_headers=self.config.cors_allowed_headers,
        )
    
    def setup_logging_middleware(self) -> None:
        """设置日志中间件"""
        self.app.add_middleware(RequestLoggingMiddleware)
    
    def setup_rate_limit_middleware(self) -> None:
        """设置速率限制中间件"""
        self.app.add_middleware(
            RateLimitMiddleware,
            max_requests_per_minute=self.config.rate_limit_per_minute
        )
    
    def setup_all_middlewares(self) -> None:
        """设置所有中间件"""
        self.setup_cors_middleware()
        self.setup_logging_middleware()
        self.setup_rate_limit_middleware()


def setup_middlewares(app, gateway_config=None):
    """设置所有中间件的便捷函数"""
    from api_gateway.gateway_config import GatewayConfig
    
    if gateway_config is None:
        gateway_config = GatewayConfig()
    
    handler = MiddlewareHandler(app, gateway_config)
    handler.setup_all_middlewares()
    
    return handler
