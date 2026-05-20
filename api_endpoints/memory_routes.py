"""
FastAPI路由 - 记忆管理
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel

from api_endpoints.memory_endpoints import MemoryEndpoints
from application_service.memory_application_service import MemoryType

router = APIRouter()

class CreateMemoryRequest(BaseModel):
    content: str
    memory_type: str = "experience"
    importance_score: int = 5
    tags: List[str] = []
    metadata: Optional[dict] = None

class UpdateMemoryRequest(BaseModel):
    content: Optional[str] = None
    importance_score: Optional[int] = None
    tags: Optional[List[str]] = None

class SearchMemoriesRequest(BaseModel):
    query_text: str
    memory_type: Optional[str] = None
    min_importance: Optional[int] = None
    tags: Optional[List[str]] = None
    limit: int = 10

@router.get("/")
async def list_memories(limit: int = Query(50, ge=1, le=1000)) -> dict:
    """List recent memories"""
    endpoints = MemoryEndpoints()
    memories = await endpoints.list_recent_memories(limit=limit)
    return {"total": len(memories), "memories": [m.__dict__ for m in memories]}

@router.post("/")
async def create_memory(request: CreateMemoryRequest) -> dict:
    """Create a new memory"""
    endpoints = MemoryEndpoints()
    
    memory_type = MemoryType(request.memory_type)
    
    memory = await endpoints.create_memory(
        content=request.content,
        memory_type=memory_type,
        importance_score=request.importance_score,
        tags=request.tags,
        metadata=request.metadata
    )
    return memory.__dict__

@router.get("/stats")
async def get_memory_stats(hours: int = Query(24, ge=1, le=168)) -> dict:
    """Get memory statistics"""
    endpoints = MemoryEndpoints()
    return await endpoints.get_memory_stats(hours=hours)

@router.get("/search")
async def search_memories(
    query_text: str = Query(..., description="Search query"),
    memory_type: Optional[str] = Query(None, description="Filter by memory type"),
    min_importance: Optional[int] = Query(None, ge=1, le=10, description="Minimum importance"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    limit: int = Query(10, ge=1, le=100)
) -> dict:
    """Search memories"""
    endpoints = MemoryEndpoints()
    
    tag_list = tags.split(",") if tags else None
    
    results = await endpoints.search_memories(
        query_text=query_text,
        memory_type=memory_type,
        min_importance=min_importance,
        tags=tag_list,
        limit=limit
    )
    
    return {
        "total": results.total,
        "results": [r.__dict__ for r in results.results],
        "search_time_ms": results.search_time_ms
    }

@router.get("/{memory_id}")
async def get_memory(memory_id: str) -> dict:
    """Get memory by ID"""
    endpoints = MemoryEndpoints()
    memory = await endpoints.get_memory(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail=f"Memory {memory_id} not found")
    return memory.__dict__

@router.patch("/{memory_id}")
async def update_memory(memory_id: str, request: UpdateMemoryRequest) -> dict:
    """Update memory"""
    endpoints = MemoryEndpoints()
    memory = await endpoints.update_memory(
        memory_id,
        content=request.content,
        importance_score=request.importance_score,
        tags=request.tags
    )
    if not memory:
        raise HTTPException(status_code=404, detail=f"Memory {memory_id} not found")
    return memory.__dict__

@router.delete("/{memory_id}")
async def delete_memory(memory_id: str) -> dict:
    """Delete memory"""
    endpoints = MemoryEndpoints()
    success = await endpoints.delete_memory(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Memory {memory_id} not found")
    return {"memory_id": memory_id, "deleted": success}

@router.post("/cleanup")
async def cleanup_memories(max_age_days: int = Query(30, ge=1, le=365)) -> dict:
    """Cleanup expired memories"""
    endpoints = MemoryEndpoints()
    count = await endpoints.cleanup_expired_memories(max_age_days=max_age_days)
    return {"deleted_count": count}
