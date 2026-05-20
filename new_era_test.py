"""
新纪元测试 - 验证新的应用服务层
"""
import sys
from pathlib import Path

# 添加当前目录到路径
agent_system_path = Path("/workspace/agent_system")
sys.path.insert(0, str(agent_system_path))

print("=" * 80)
print("新纪元测试 - 新应用服务层验证")
print("=" * 80)

def test_memory_service():
    """测试记忆应用服务"""
    print("\n测试1: 记忆应用服务")
    print("-" * 60)
    
    try:
        from application_service.memory_application_service import (
            MemoryApplicationService, MemoryType, MemorySearchQuery
        )
        
        # 创建服务实例
        service = MemoryApplicationService()
        
        # 创建记忆
        print("创建测试记忆...")
        memory = service.create_memory(
            content="测试记忆内容 - 这是一个重要的测试",
            memory_type=MemoryType.EXPERIENCE,
            importance_score=8,
            tags=["测试", "重要"]
        )
        print(f"✓ 记忆创建成功: {memory.memory_content[:30]}...")
        
        # 获取记忆
        retrieved = service.get_memory(memory.memory_identifier)
        print(f"✓ 记忆检索成功: {retrieved is not None}")
        
        # 搜索记忆
        query = MemorySearchQuery(query_text="测试", limit=5)
        results = service.search_memories(query)
        print(f"✓ 搜索结果: 找到 {len(results)} 条相关记忆")
        
        # 获取统计
        stats = service.get_memory_stats()
        print(f"✓ 统计信息: 总计 {stats.total_memories} 条记忆")
        
        print("✓ 记忆应用服务测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_evolution_service():
    """测试进化应用服务"""
    print("\n测试2: 进化应用服务")
    print("-" * 60)
    
    try:
        from application_service.evolution_application_service import (
            EvolutionApplicationService, EvolutionConfig
        )
        
        # 创建服务实例
        service = EvolutionApplicationService()
        
        # 配置简单的进化
        config = EvolutionConfig(
            population_size=10,
            generations=20,
            mutation_rate=0.2
        )
        
        print(f"开始进化: {config.population_size} 个个体, {config.generations} 代...")
        
        # 运行进化（简化版）
        result = service.run_evolution(config)
        
        print(f"✓ 进化完成! 最佳适应度: {result.final_fitness:.4f}")
        print(f"  代数: {result.generations_used}, 成功: {result.success}")
        
        # 获取种群统计
        stats = service.get_population_stats()
        print(f"  种群统计: 总计 {stats['total']} 个个体")
        
        print("✓ 进化应用服务测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """集成测试"""
    print("\n测试3: 服务集成测试")
    print("-" * 60)
    
    try:
        # 同时使用多个服务
        from application_service.memory_application_service import (
            MemoryApplicationService, MemoryType
        )
        from application_service.evolution_application_service import (
            EvolutionApplicationService, EvolutionConfig
        )
        
        # 创建两个服务
        memory_service = MemoryApplicationService()
        evolution_service = EvolutionApplicationService()
        
        # 创建记忆
        for i in range(5):
            memory_service.create_memory(
                content=f"集成测试记忆 {i}",
                memory_type=MemoryType.EXPERIENCE,
                importance_score=5
            )
        
        # 运行快速进化
        config = EvolutionConfig(
            population_size=5,
            generations=10,
            target_fitness=0.8
        )
        
        result = evolution_service.run_evolution(config)
        
        # 保存最佳Agent到记忆
        if result.best_genome:
            memory_service.create_memory(
                content=f"最佳Agent: {result.best_genome.genes}",
                memory_type=MemoryType.STRATEGY,
                importance_score=9,
                tags=["Agent", "最佳", "进化"]
            )
        
        print("✓ 集成测试通过!")
        return True
        
    except Exception as e:
        print(f"✗ 集成测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    tests = [
        ("记忆服务", test_memory_service),
        ("进化服务", test_evolution_service),
        ("集成测试", test_integration)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"✗ {name} 异常: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"  {name}: {status}")
    
    print(f"\n总计: {passed_count}/{total_count} 个测试通过")
    
    if passed_count == total_count:
        print("\n🎉 新纪元系统测试完全通过！")
    else:
        print(f"\n⚠️ 有 {total_count - passed_count} 个测试需要修复")
    
    return passed_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
