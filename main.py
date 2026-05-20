"""
FastAPI Web服务入口
Agent永续自进化系统 - API接入层
"""
import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from datetime import datetime, timezone

from configuration.app_config import AppConfig
from infrastructure.logging.logging_system import StructuredLogger
from api_gateway.middleware_handler import MiddlewareHandler

from backend.database import init_db
from backend.tenant_routes import router as tenant_router
from backend.service_routes import router as service_router
from backend.monitoring_routes import router as monitoring_router
from backend.seed import seed_data

config = AppConfig()
logger = StructuredLogger("fastapi_main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FastAPI应用启动", 
                version=config.version,
                environment=config.environment)
    
    await init_db()
    
    try:
        await seed_data()
    except Exception as e:
        logger.warning(f"数据种子可能已存在: {e}")
    
    yield
    logger.info("FastAPI应用关闭")

app = FastAPI(
    title="Agent永续自进化系统 API",
    description="""
## Agent永续自进化系统

这是一个高度模块化的AI Agent自进化运行系统，具备以下核心能力：

### 核心功能
- 🧬 **Agent进化引擎** - 基于遗传算法的智能体自进化
- 💾 **记忆管理系统** - 持久化和检索Agent经验
- 📊 **监控系统** - 实时系统健康监控和告警
- 📈 **数据分析** - 趋势分析和异常检测

### 技术特性
- ✅ 7层Clean Architecture架构
- ✅ FastAPI + SQLAlchemy 2.0异步架构
- ✅ Repository模式与依赖注入
- ✅ 完整JWT认证授权
- ✅ 结构化日志和监控
    """,
    version=config.version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("收到请求",
                method=request.method,
                url=str(request.url),
                client=request.client.host if request.client else "unknown")
    response = await call_next(request)
    logger.info("请求完成",
                method=request.method,
                url=str(request.url),
                status_code=response.status_code)
    return response

@app.get("/", tags=["健康检查"])
async def root():
    return {
        "message": "Agent永续自进化系统 API",
        "version": config.version,
        "status": "running",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/health", tags=["健康检查"])
async def health_check():
    return {
        "status": "healthy",
        "version": config.version,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/ready", tags=["健康检查"])
async def readiness_check():
    return {
        "ready": True,
        "version": config.version,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

app.include_router(tenant_router)
app.include_router(service_router)
app.include_router(monitoring_router)

try:
    from auth.auth_routes import router as auth_router
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["认证管理"])
    logger.info("认证路由已注册")
except Exception as e:
    logger.warning(f"认证路由注册跳过: {e}")

try:
    from api_endpoints.agent_routes import router as agent_router
    app.include_router(agent_router, prefix="/api/v1/agents", tags=["Agent管理"])
    logger.info("Agent路由已注册")
except Exception as e:
    logger.warning(f"Agent路由注册跳过: {e}")

try:
    from api_endpoints.memory_routes import router as memory_router
    app.include_router(memory_router, prefix="/api/v1/memories", tags=["记忆管理"])
    logger.info("记忆路由已注册")
except Exception as e:
    logger.warning(f"记忆路由注册跳过: {e}")

try:
    from api_endpoints.monitoring_routes import router as monitoring_router_old
    app.include_router(monitoring_router_old, prefix="/api/v1/monitoring", tags=["监控分析"])
    logger.info("旧监控路由已注册")
except Exception as e:
    logger.warning(f"旧监控路由注册跳过: {e}")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("全局异常",
                error=str(exc),
                path=str(request.url),
                method=request.method)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "内部服务器错误",
            "message": str(exc),
            "path": str(request.url),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
