"""
新阶段测试 - 验证新服务
"""
import sys
import asyncio
from pathlib import Path

agent_system_path = Path("/workspace/agent_system")
sys.path.insert(0, str(agent_system_path))

print("=" * 80)
print("新阶段测试 - 监控和分析服务")
print("=" * 80)


def test_monitoring_service():
    """测试监控服务"""
    print("\n测试 1: 监控应用服务")
    print("-" * 60)
    
    try:
        from application_service.monitoring_application_service import (
            MonitoringApplicationService,
            AlertSeverity,
            AlertStatus,
            AlertRule,
            MetricsQuery,
            DashboardSnapshot
        )
        
        service = MonitoringApplicationService()
        print("✓ 监控服务创建成功")
        
        # 测试记录指标
        for i in range(20):
            service.record_metric("test_metric", i * 1.5 + 10)
        print("✓ 指标记录成功")
        
        # 测试查询指标
        query = MetricsQuery(
            metric_name="test_metric"
        )
        result = service.query_metrics(query)
        print(f"✓ 指标查询成功: {len(result.values)} 个数据点")
        print(f"  统计: 平均={result.statistics.get('avg', 0):.2f}, 最大={result.statistics.get('max', 0):.2f}")
        
        # 测试告警规则注册
        custom_rule = AlertRule(
            name="custom_test_rule",
            description="自定义测试规则",
            condition=lambda ctx: True,
            severity=AlertSeverity.INFO,
            cooldown_seconds=60
        )
        service.register_alert_rule(custom_rule)
        print("✓ 告警规则注册成功")
        
        # 获取统计信息
        stats = service.get_statistics(hours=24)
        print(f"✓ 统计信息获取成功: 规则数={stats['total_rules']}")
        
        print("✓ 监控服务测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 监控服务测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_analytics_service():
    """测试分析服务"""
    print("\n测试 2: 分析应用服务")
    print("-" * 60)
    
    try:
        from application_service.analytics_application_service import (
            AnalyticsApplicationService,
            TrendDirection,
            InsightSeverity,
            ReportConfig,
            Report
        )
        
        service = AnalyticsApplicationService()
        print("✓ 分析服务创建成功")
        
        # 创建测试数据
        test_data = []
        for i in range(30):
            test_data.append({
                "timestamp": str(i),
                "value": 50 + i * 2.5 + (i % 3) * 0.5
            })
        
        # 测试统计计算
        stats = service.calculate_statistics(test_data, "test_performance")
        print(f"✓ 统计计算成功:")
        print(f"  平均: {stats.get('mean', 0):.2f}")
        print(f"  中位数: {stats.get('median', 0):.2f}")
        print(f"  标准差: {stats.get('std_dev', 0):.2f}")
        
        # 测试趋势分析
        trend = service.analyze_trend(test_data, "test_performance")
        print(f"✓ 趋势分析成功: 方向={trend.direction.value}, 斜率={trend.slope:.3f}")
        print(f"  置信度: {trend.confidence:.2%}, 预测点: {len(trend.forecast)}")
        
        # 测试洞察生成
        insights = service.generate_insights([trend], {"metrics": {"test_performance": stats}})
        print(f"✓ 洞察生成成功: {len(insights)} 个洞察")
        for insight in insights[:3]:
            print(f"  - [{insight.severity.value}] {insight.title}")
        
        # 测试异常检测
        # 添加一个明显的异常值
        anomalous_data = test_data.copy()
        anomalous_data.append({"timestamp": "30", "value": 500})
        
        anomalies = service.detect_anomalies(anomalous_data)
        print(f"✓ 异常检测成功: 找到 {len(anomalies)} 个异常")
        
        # 测试数据聚合
        aggregated = service.aggregate_metrics(test_data, group_by="hour")
        print(f"✓ 数据聚合成功: {len(aggregated)} 个分组")
        
        print("✓ 分析服务测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 分析服务测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_combined_features():
    """测试组合功能"""
    print("\n测试 3: 组合功能测试")
    print("-" * 60)
    
    try:
        from application_service.monitoring_application_service import (
            MonitoringApplicationService,
            AlertSeverity,
            AlertStatus
        )
        from application_service.analytics_application_service import (
            AnalyticsApplicationService,
            ReportConfig
        )
        
        # 创建两个服务
        monitoring = MonitoringApplicationService()
        analytics = AnalyticsApplicationService()
        print("✓ 服务初始化成功")
        
        # 生成模拟数据
        test_data = []
        for i in range(50):
            value = 30 + i * 1.2 + (i % 7) * 0.3
            test_data.append({"timestamp": str(i), "value": value})
            
            # 同时记录到监控
            monitoring.record_metric("system_performance", value)
        
        print("✓ 数据生成和记录成功")
        
        # 使用分析服务
        report_config = ReportConfig(
            title="系统性能分析报告",
            include_trends=True,
            include_insights=True,
            include_statistics=True
        )
        
        report = await analytics.generate_report(report_config, test_data, "system_performance")
        print(f"✓ 报告生成成功: {report.title}")
        print(f"  摘要: {report.summary}")
        print(f"  趋势: {len(report.trends)} 个, 洞察: {len(report.insights)} 个")
        
        # 监控系统指标
        metrics_query = monitoring.monitoring_system.get_metrics()
        print("✓ 系统指标获取成功")
        
        print("✓ 组合功能测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 组合功能测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_compatibility_with_existing():
    """测试与现有服务的兼容性"""
    print("\n测试 4: 与现有服务的兼容性")
    print("-" * 60)
    
    try:
        from application_service.memory_application_service import (
            MemoryApplicationService,
            MemoryType
        )
        from application_service.evolution_application_service import (
            EvolutionApplicationService,
            EvolutionConfig
        )
        
        # 测试记忆服务仍然可用
        memory_service = MemoryApplicationService()
        memory = memory_service.create_memory(
            content="新的测试记忆",
            memory_type=MemoryType.EXPERIENCE,
            importance_score=7,
            tags=["test", "new_phase"]
        )
        print(f"✓ 记忆服务正常工作: {memory.id}")
        
        # 测试进化服务仍然可用
        evolution_service = EvolutionApplicationService()
        config = EvolutionConfig(
            population_size=15,
            generations=20
        )
        result = evolution_service.run_evolution(config)
        print(f"✓ 进化服务正常工作: 适应度={result.final_fitness:.3f}")
        
        print("✓ 兼容性测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 兼容性测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    tests = [
        ("监控应用服务", test_monitoring_service),
        ("分析应用服务", test_analytics_service),
        ("与现有服务兼容性", test_compatibility_with_existing)
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
    
    # 运行异步测试
    print("\n运行异步测试...")
    try:
        passed = asyncio.run(test_combined_features())
        results.append(("组合功能", passed))
    except Exception as e:
        print(f"✗ 组合功能测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("组合功能", False))
    
    # 最终总结
    print("\n" + "=" * 80)
    print("新阶段测试总结")
    print("=" * 80)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"  {name}: {status}")
    
    print(f"\n总计: {passed_count}/{total_count} 个测试通过")
    
    if passed_count == total_count:
        print("\n🎉 新阶段所有测试完全通过！")
        print("\n新增功能总结:")
        print("  - MonitoringApplicationService: 完整的监控和告警系统")
        print("  - AnalyticsApplicationService: 数据分析、趋势预测和洞察")
        print("  - 完整的7层架构应用服务")
    else:
        print(f"\n⚠️ 有 {total_count - passed_count} 个测试需要修复")
    
    return passed_count == total_count


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
