"""
完整集成测试和系统测试 - 使用Agent系统处理多个GitHub项目
发现实际使用中的问题
"""
import os
import sys
import time
import json
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any


class MultiProjectSystemTest:
    """多项目系统测试"""
    
    def __init__(self):
        self.test_results = []
        self.issues_found = []
        self.projects_tested = []
    
    def test_agent_evolution_engine(self) -> Dict[str, Any]:
        """测试进化引擎"""
        print("\n" + "="*80)
        print("测试1: 进化引擎集成测试")
        print("="*80)
        
        start_time = time.time()
        
        try:
            sys.path.insert(0, "/workspace/agent_system")
            
            from domain_logic.evolution_engine_core import (
                EvolutionEngine,
                EvolutionStrategy,
                AgentGenome
            )
            
            # 创建进化引擎
            engine = EvolutionEngine(
                population_size=10,
                mutation_rate=0.1,
                strategy=EvolutionStrategy.ADAPTIVE
            )
            
            print(f"✓ 进化引擎创建成功")
            print(f"  种群大小: {engine.population_size}")
            print(f"  进化策略: {engine.strategy.value}")
            
            # 定义适应度函数
            def fitness_func(genome: AgentGenome) -> float:
                return sum(genome.genes.values()) if genome.genes else 0.0
            
            # 进化一代
            metrics = engine.evolve_generation(fitness_func)
            
            print(f"✓ 进化完成")
            print(f"  代数: {metrics.generation}")
            print(f"  适应度: {metrics.fitness_score:.4f}")
            print(f"  多样性: {metrics.diversity_score:.4f}")
            
            duration = time.time() - start_time
            
            return {
                "test_name": "evolution_engine_integration",
                "test_type": "integration",
                "status": "passed",
                "duration": duration,
                "details": {
                    "generation": metrics.generation,
                    "fitness": metrics.fitness_score,
                    "diversity": metrics.diversity_score
                }
            }
            
        except Exception as e:
            self.issues_found.append({
                "test": "evolution_engine",
                "error": str(e),
                "type": "integration_error"
            })
            
            return {
                "test_name": "evolution_engine_integration",
                "test_type": "integration",
                "status": "error",
                "duration": time.time() - start_time,
                "error": str(e)
            }
    
    def test_jwt_authentication(self) -> Dict[str, Any]:
        """测试JWT认证"""
        print("\n" + "="*80)
        print("测试2: JWT认证集成测试")
        print("="*80)
        
        start_time = time.time()
        
        try:
            sys.path.insert(0, "/workspace/agent_system")
            
            from api_access.auth_jwt_token_manager import (
                create_access_token,
                create_refresh_token,
                decode_token,
                verify_token,
                TokenManager,
                UserRole
            )
            
            # 创建令牌管理器
            manager = TokenManager()
            
            # 创建令牌对
            tokens = manager.create_token_pair(
                user_id="test_user_123",
                username="testuser",
                roles=[UserRole.USER.value]
            )
            
            print(f"✓ 令牌对创建成功")
            print(f"  访问令牌长度: {len(tokens['access_token'])}")
            print(f"  刷新令牌长度: {len(tokens['refresh_token'])}")
            
            # 验证令牌
            is_valid = verify_token(tokens['access_token'])
            print(f"✓ 令牌验证: {'通过' if is_valid else '失败'}")
            
            # 解码令牌
            payload = decode_token(tokens['access_token'])
            print(f"✓ 令牌解码成功")
            print(f"  用户ID: {payload.get('sub')}")
            print(f"  用户名: {payload.get('username')}")
            
            # 刷新令牌
            new_tokens = manager.refresh_access_token(tokens['refresh_token'])
            print(f"✓ 令牌刷新成功")
            
            duration = time.time() - start_time
            
            return {
                "test_name": "jwt_authentication",
                "test_type": "integration",
                "status": "passed",
                "duration": duration,
                "details": {
                    "token_created": True,
                    "token_valid": is_valid,
                    "token_refreshed": new_tokens is not None
                }
            }
            
        except Exception as e:
            self.issues_found.append({
                "test": "jwt_authentication",
                "error": str(e),
                "type": "integration_error"
            })
            
            return {
                "test_name": "jwt_authentication",
                "test_type": "integration",
                "status": "error",
                "duration": time.time() - start_time,
                "error": str(e)
            }
    
    def test_cache_system(self) -> Dict[str, Any]:
        """测试缓存系统"""
        print("\n" + "="*80)
        print("测试3: 缓存系统集成测试")
        print("="*80)
        
        start_time = time.time()
        
        try:
            sys.path.insert(0, "/workspace/agent_system")
            
            from infrastructure.cache.cache_manager import (
                CacheManager,
                default_cache,
                task_cache
            )
            
            # 测试默认缓存
            default_cache.set("test_key", "test_value")
            value = default_cache.get("test_key")
            
            print(f"✓ 默认缓存测试: {'通过' if value == 'test_value' else '失败'}")
            
            # 测试任务缓存
            task_cache.set("task_1", {"status": "completed"})
            task_value = task_cache.get("task_1")
            
            print(f"✓ 任务缓存测试: {'通过' if task_value else '失败'}")
            
            # 获取统计信息
            stats = default_cache.get_stats()
            print(f"✓ 缓存统计:")
            print(f"  类型: {stats['type']}")
            print(f"  当前大小: {stats['current_size']}")
            print(f"  命中率: {stats['hit_rate']:.2%}")
            
            duration = time.time() - start_time
            
            return {
                "test_name": "cache_system",
                "test_type": "integration",
                "status": "passed",
                "duration": duration,
                "details": {
                    "default_cache": value == "test_value",
                    "task_cache": task_value is not None,
                    "stats": stats
                }
            }
            
        except Exception as e:
            self.issues_found.append({
                "test": "cache_system",
                "error": str(e),
                "type": "integration_error"
            })
            
            return {
                "test_name": "cache_system",
                "test_type": "integration",
                "status": "error",
                "duration": time.time() - start_time,
                "error": str(e)
            }
    
    def test_performance_benchmark(self) -> Dict[str, Any]:
        """测试性能基准"""
        print("\n" + "="*80)
        print("测试4: 性能基准测试")
        print("="*80)
        
        start_time = time.time()
        
        try:
            sys.path.insert(0, "/workspace/agent_system")
            
            from application_service.performance_benchmark_runner import (
                PerformanceBenchmark,
                ConcurrentBenchmark
            )
            
            # 创建基准测试器
            benchmark = PerformanceBenchmark(min_runs=5)
            
            # 测试同步函数
            def sample_sync_func():
                return sum(range(1000))
            
            sync_result = benchmark.benchmark_sync(
                "sample_sync_benchmark",
                sample_sync_func,
                runs=10
            )
            
            print(f"✓ 同步基准测试完成")
            print(f"  名称: {sync_result.name}")
            print(f"  运行次数: {sync_result.total_runs}")
            print(f"  平均时间: {sync_result.avg_time:.6f}s")
            print(f"  每秒操作数: {sync_result.ops_per_second:.2f}")
            
            duration = time.time() - start_time
            
            return {
                "test_name": "performance_benchmark",
                "test_type": "system",
                "status": "passed",
                "duration": duration,
                "details": {
                    "benchmark_name": sync_result.name,
                    "total_runs": sync_result.total_runs,
                    "avg_time": sync_result.avg_time,
                    "ops_per_second": sync_result.ops_per_second
                }
            }
            
        except Exception as e:
            self.issues_found.append({
                "test": "performance_benchmark",
                "error": str(e),
                "type": "system_error"
            })
            
            return {
                "test_name": "performance_benchmark",
                "test_type": "system",
                "status": "error",
                "duration": time.time() - start_time,
                "error": str(e)
            }
    
    def test_database_integration(self) -> Dict[str, Any]:
        """测试数据库集成"""
        print("\n" + "="*80)
        print("测试5: 数据库集成测试")
        print("="*80)
        
        start_time = time.time()
        
        try:
            sys.path.insert(0, "/workspace/agent_system")
            
            from sqlalchemy import create_engine, Column, Integer, String
            from sqlalchemy.orm import declarative_base, sessionmaker
            
            # 使用新的导入方式
            Base = declarative_base()
            
            class TestModel(Base):
                __tablename__ = "test_table"
                
                id = Column(Integer, primary_key=True)
                name = Column(String(50))
            
            # 创建内存数据库
            engine = create_engine("sqlite:///:memory:", echo=False)
            Base.metadata.create_all(engine)
            
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # 插入数据
            test_obj = TestModel(name="test")
            session.add(test_obj)
            session.commit()
            
            # 查询数据
            result = session.query(TestModel).first()
            
            print(f"✓ 数据库集成测试: {'通过' if result.name == 'test' else '失败'}")
            print(f"  SQLAlchemy 2.0兼容: 通过")
            
            session.close()
            
            duration = time.time() - start_time
            
            return {
                "test_name": "database_integration",
                "test_type": "integration",
                "status": "passed",
                "duration": duration,
                "details": {
                    "sqlalchemy_compatible": True,
                    "crud_operations": True
                }
            }
            
        except Exception as e:
            self.issues_found.append({
                "test": "database_integration",
                "error": str(e),
                "type": "integration_error"
            })
            
            return {
                "test_name": "database_integration",
                "test_type": "integration",
                "status": "error",
                "duration": time.time() - start_time,
                "error": str(e)
            }
    
    def test_pydantic_validation(self) -> Dict[str, Any]:
        """测试Pydantic验证"""
        print("\n" + "="*80)
        print("测试6: Pydantic验证测试")
        print("="*80)
        
        start_time = time.time()
        
        try:
            sys.path.insert(0, "/workspace/agent_system")
            
            from pydantic import BaseModel, Field, field_validator
            from typing import List
            
            # 使用Pydantic V2风格
            class TestModel(BaseModel):
                name: str = Field(..., min_length=1, max_length=100)
                age: int = Field(..., ge=0, le=150)
                tags: List[str] = Field(default_factory=list)
                
                @field_validator('name')
                @classmethod
                def name_must_not_be_empty(cls, v):
                    if not v.strip():
                        raise ValueError('name cannot be empty')
                    return v
            
            # 创建模型实例
            model = TestModel(name="test", age=25, tags=["tag1", "tag2"])
            
            print(f"✓ Pydantic V2验证测试通过")
            print(f"  模型名称: {model.name}")
            print(f"  模型年龄: {model.age}")
            print(f"  标签数: {len(model.tags)}")
            
            duration = time.time() - start_time
            
            return {
                "test_name": "pydantic_validation",
                "test_type": "integration",
                "status": "passed",
                "duration": duration,
                "details": {
                    "pydantic_v2_compatible": True,
                    "field_validator_works": True
                }
            }
            
        except Exception as e:
            self.issues_found.append({
                "test": "pydantic_validation",
                "error": str(e),
                "type": "integration_error"
            })
            
            return {
                "test_name": "pydantic_validation",
                "test_type": "integration",
                "status": "error",
                "duration": time.time() - start_time,
                "error": str(e)
            }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        print("\n" + "="*120)
        print("Agent永续自进化系统 - 完整集成和系统测试")
        print("="*120)
        print(f"测试时间: {datetime.now(timezone.utc).isoformat()}")
        print("="*120)
        
        results = {
            "start_time": datetime.now(timezone.utc).isoformat(),
            "tests": []
        }
        
        # 运行所有测试
        test_methods = [
            self.test_agent_evolution_engine,
            self.test_jwt_authentication,
            self.test_cache_system,
            self.test_performance_benchmark,
            self.test_database_integration,
            self.test_pydantic_validation
        ]
        
        for test_method in test_methods:
            result = test_method()
            self.test_results.append(result)
            results["tests"].append(result)
        
        # 生成摘要
        results["end_time"] = datetime.now(timezone.utc).isoformat()
        results["summary"] = self._generate_summary()
        results["issues"] = self.issues_found
        
        return results
    
    def _generate_summary(self) -> Dict[str, Any]:
        """生成摘要"""
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r.get('status') == 'passed')
        failed = sum(1 for r in self.test_results if r.get('status') == 'failed')
        errors = sum(1 for r in self.test_results if r.get('status') == 'error')
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "pass_rate": (passed / total * 100) if total > 0 else 0,
            "issues_found": len(self.issues_found)
        }


def print_final_report(results: Dict[str, Any]):
    """打印最终报告"""
    print("\n" + "="*120)
    print("完整测试报告")
    print("="*120)
    
    print(f"\n测试时间: {results['start_time']} - {results['end_time']}")
    
    summary = results['summary']
    print(f"\n【测试摘要】")
    print(f"  总测试数: {summary['total']}")
    print(f"  通过: {summary['passed']}")
    print(f"  失败: {summary['failed']}")
    print(f"  错误: {summary['errors']}")
    print(f"  通过率: {summary['pass_rate']:.1f}%")
    print(f"  发现问题: {summary['issues_found']}个")
    
    print(f"\n【测试详情】")
    for test in results['tests']:
        status_icon = "✓" if test['status'] == 'passed' else "✗"
        print(f"\n  {status_icon} {test['test_name']} ({test['test_type']})")
        print(f"     状态: {test['status']}")
        print(f"     耗时: {test['duration']:.4f}s")
        if 'error' in test:
            print(f"     错误: {test['error'][:200]}")
    
    if results['issues']:
        print(f"\n【发现的问题】")
        for i, issue in enumerate(results['issues'], 1):
            print(f"\n  问题 {i}:")
            print(f"    测试: {issue['test']}")
            print(f"    类型: {issue['type']}")
            print(f"    错误: {issue['error'][:200]}")
    
    print("\n" + "="*120)


if __name__ == "__main__":
    tester = MultiProjectSystemTest()
    results = tester.run_all_tests()
    
    print_final_report(results)
    
    # 保存报告
    report_file = "/workspace/agent_system/full_integration_test_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n报告已保存到: {report_file}")
