"""
新篇章测试 - API端点层和完整系统验证
"""
import sys
import asyncio
from pathlib import Path

agent_system_path = Path("/workspace/agent_system")
sys.path.insert(0, str(agent_system_path))

print("=" * 80)
print("Agent永续自进化系统 - 新篇章测试")
print("=" * 80)


async def test_agent_endpoints():
    """测试Agent管理API核心功能"""
    print("\n" + "=" * 60)
    print("测试1: Agent管理API")
    print("=" * 60)
    
    try:
        from api_endpoints import AgentEndpoints, AgentStatus
        
        endpoints = AgentEndpoints()
        print("✓ AgentEndpoints初始化成功")
        
        # 测试种群统计
        stats = await endpoints.get_population_stats()
        print(f"✓ 种群统计成功:")
        print(f"  - 总数: {stats['total_agents']}")
        print(f"  - 平均适应度: {stats['avg_fitness']:.4f}")
        
        print("\n✓ Agent管理API核心测试成功!")
        return True
        
    except Exception as e:
        print(f"\n✗ Agent管理API测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_memory_endpoints():
    """测试记忆管理API核心功能"""
    print("\n" + "=" * 60)
    print("测试2: 记忆管理API")
    print("=" * 60)
    
    try:
        from api_endpoints import MemoryEndpoints
        from application_service.memory_application_service import MemoryType
        
        endpoints = MemoryEndpoints()
        print("✓ MemoryEndpoints初始化成功")
        
        # 测试创建记忆
        memory = await endpoints.create_memory(
            content="这是一个测试记忆，包含重要的信息",
            memory_type=MemoryType.EXPERIENCE,
            importance_score=8,
            tags=["测试", "重要"]
        )
        print(f"✓ 记忆创建成功: {memory.memory_id}")
        print(f"  - 内容: {memory.content[:30]}...")
        print(f"  - 重要度: {memory.importance_score}")
        
        # 测试获取记忆
        fetched = await endpoints.get_memory(memory.memory_id)
        assert fetched is not None
        print(f"✓ 记忆获取成功: {fetched.memory_id}")
        
        # 测试搜索记忆
        results = await endpoints.search_memories(query_text="测试", limit=5)
        print(f"✓ 记忆搜索成功: 找到 {results.total} 个结果")
        
        # 测试记忆统计
        stats = await endpoints.get_memory_stats()
        print(f"✓ 记忆统计成功:")
        print(f"  - 总数: {stats['total_memories']}")
        
        print("\n✓ 记忆管理API核心测试成功!")
        return True
        
    except Exception as e:
        print(f"\n✗ 记忆管理API测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_monitoring_analytics_endpoints():
    """测试监控和分析API核心功能"""
    print("\n" + "=" * 60)
    print("测试3: 监控和分析API")
    print("=" * 60)
    
    try:
        from api_endpoints import MonitoringAnalyticsEndpoints
        
        endpoints = MonitoringAnalyticsEndpoints()
        print("✓ MonitoringAnalyticsEndpoints初始化成功")
        
        # 测试记录指标
        for i in range(10):
            await endpoints.record_metric("test_performance", i * 2.5 + 50)
        print(f"✓ 指标记录成功: 10个数据点")
        
        # 测试系统健康检查
        health = await endpoints.get_health_status()
        print(f"✓ 系统健康检查成功: {health.get('status', 'unknown')}")
        
        # 测试系统指标
        metrics = await endpoints.get_system_metrics()
        print(f"✓ 系统指标获取成功")
        
        # 测试仪表板快照
        dashboard = await endpoints.get_dashboard_snapshot()
        print(f"✓ 仪表板快照获取成功")
        
        # 测试告警列表
        alerts = await endpoints.list_alerts(limit=10)
        print(f"✓ 告警列表获取成功: {len(alerts)} 个告警")
        
        # 测试统计信息
        stats = await endpoints.get_statistics()
        print(f"✓ 统计信息获取成功")
        
        print("\n✓ 监控和分析API核心测试成功!")
        return True
        
    except Exception as e:
        print(f"\n✗ 监控和分析API测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_end_to_end_workflow():
    """测试端到端工作流"""
    print("\n" + "=" * 60)
    print("测试4: 端到端工作流")
    print("=" * 60)
    
    try:
        from api_endpoints import AgentEndpoints, MemoryEndpoints, MonitoringAnalyticsEndpoints
        from application_service.memory_application_service import MemoryType
        
        # 初始化所有端点
        agent_endpoints = AgentEndpoints()
        memory_endpoints = MemoryEndpoints()
        monitoring_endpoints = MonitoringAnalyticsEndpoints()
        print("✓ 所有端点初始化成功")
        
        # 1. 记录系统事件到记忆
        print("\n步骤1: 记录系统信息到记忆...")
        memory = await memory_endpoints.create_memory(
            content="系统启动完成，准备运行测试",
            memory_type=MemoryType.EXPERIENCE,
            importance_score=7,
            tags=["系统", "启动"]
        )
        print(f"✓ 记忆记录成功: {memory.memory_id}")
        
        # 2. 记录系统性能指标
        print("\n步骤2: 记录系统性能...")
        for i in range(5):
            performance = 75 + i * 2.5
            await monitoring_endpoints.record_metric("workflow_performance", performance)
        print(f"✓ 性能指标记录成功")
        
        # 3. 搜索相关记忆
        print("\n步骤3: 搜索记忆...")
        results = await memory_endpoints.search_memories(query_text="系统")
        print(f"✓ 记忆搜索成功: {results.total} 个结果")
        
        # 4. 获取系统状态
        print("\n步骤4: 获取系统状态...")
        health = await monitoring_endpoints.get_health_status()
        stats = await agent_endpoints.get_population_stats()
        memory_stats = await memory_endpoints.get_memory_stats()
        
        print(f"✓ 系统状态获取成功")
        print(f"  - 健康: {health.get('status', 'unknown')}")
        print(f"  - Agent数: {stats['total_agents']}")
        print(f"  - 记忆数: {memory_stats['total_memories']}")
        
        print("\n✓ 端到端工作流测试成功!")
        return True
        
    except Exception as e:
        print(f"\n✗ 端到端工作流测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("\n开始运行新篇章测试...\n")
    
    tests = [
        ("Agent管理API", test_agent_endpoints),
        ("记忆管理API", test_memory_endpoints),
        ("监控分析API", test_monitoring_analytics_endpoints),
        ("端到端工作流", test_end_to_end_workflow)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = await test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n✗ {name} 异常: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 最终总结
    print("\n" + "=" * 80)
    print("新篇章测试总结")
    print("=" * 80)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"  {name}: {status}")
    
    print(f"\n总计: {passed_count}/{total_count} 个测试通过")
    
    if passed_count == total_count:
        print("\n🎉 新篇章核心测试全部通过!")
        print("\n系统功能:")
        print("  - 完整的API端点层: ✓")
        print("  - Agent管理: ✓")
        print("  - 记忆管理: ✓")
        print("  - 监控分析: ✓")
        print("  - 端到端工作流: ✓")
    else:
        print(f"\n⚠️ 有 {total_count - passed_count} 个测试需要修复")
    
    return passed_count == total_count


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
