"""
GitHub真实项目集成测试框架
使用真实的大项目进行单元测试、集成测试和系统测试
"""
import os
import sys
import asyncio
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class TestResult:
    """测试结果"""
    test_name: str
    project_name: str
    test_type: str
    status: str  # passed, failed, error, skipped
    duration: float
    message: str = ""
    error_details: str = ""
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


class GitHubProjectDownloader:
    """GitHub项目下载器"""
    
    def __init__(self, temp_dir: Optional[str] = None):
        self.temp_dir = temp_dir or tempfile.mkdtemp(prefix="github_test_")
        self.downloaded_projects: Dict[str, str] = {}
    
    def clone_project(self, repo_url: str, branch: str = "main") -> str:
        """克隆GitHub项目"""
        repo_name = repo_url.split("/")[-1].replace(".git", "")
        target_dir = os.path.join(self.temp_dir, repo_name)
        
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        
        print(f"正在克隆 {repo_url} (分支: {branch})...")
        result = subprocess.run(
            ["git", "clone", "--branch", branch, "--depth", "1", repo_url, target_dir],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode != 0:
            raise Exception(f"克隆失败: {result.stderr}")
        
        self.downloaded_projects[repo_name] = target_dir
        print(f"✓ 克隆成功: {target_dir}")
        return target_dir
    
    def install_dependencies(self, project_dir: str, requirements_file: str = "requirements.txt"):
        """安装项目依赖"""
        requirements_path = os.path.join(project_dir, requirements_file)
        
        if not os.path.exists(requirements_path):
            print(f"⚠ 未找到 {requirements_file}")
            return
        
        print(f"正在安装依赖...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "-r", requirements_path],
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if result.returncode != 0:
            print(f"⚠ 依赖安装警告: {result.stderr[:200]}")
        else:
            print(f"✓ 依赖安装成功")
    
    def cleanup(self):
        """清理临时目录"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


class RealProjectTester:
    """真实项目测试器"""
    
    def __init__(self, downloader: GitHubProjectDownloader):
        self.downloader = downloader
        self.test_results: List[TestResult] = []
    
    def run_unit_tests(self, project_dir: str, project_name: str) -> List[TestResult]:
        """运行单元测试"""
        results = []
        test_dir = os.path.join(project_dir, "tests", "unit")
        
        if not os.path.exists(test_dir):
            print(f"⚠ 未找到单元测试目录")
            return results
        
        print(f"\n运行 {project_name} 单元测试...")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_dir, "-v", "--tb=short", "-x"],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=project_dir
            )
            
            duration = 0.0
            if "passed" in result.stdout:
                lines = result.stdout.split("\n")
                for line in lines:
                    if "passed" in line:
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if "passed" in part and i > 0:
                                try:
                                    duration = float(parts[i-1].replace("s", ""))
                                except:
                                    pass
            
            status = "passed" if result.returncode == 0 else "failed"
            
            results.append(TestResult(
                test_name=f"{project_name}_unit_tests",
                project_name=project_name,
                test_type="unit",
                status=status,
                duration=duration,
                message=result.stdout[-500:] if len(result.stdout) > 500 else result.stdout,
                error_details=result.stderr[-500:] if len(result.stderr) > 500 else result.stderr
            ))
            
            print(f"{'✓' if status == 'passed' else '✗'} 单元测试: {status}")
            
        except subprocess.TimeoutExpired:
            results.append(TestResult(
                test_name=f"{project_name}_unit_tests",
                project_name=project_name,
                test_type="unit",
                status="error",
                duration=300.0,
                message="测试超时"
            ))
        except Exception as e:
            results.append(TestResult(
                test_name=f"{project_name}_unit_tests",
                project_name=project_name,
                test_type="unit",
                status="error",
                duration=0.0,
                message=str(e)
            ))
        
        self.test_results.extend(results)
        return results
    
    def run_integration_tests(self, project_dir: str, project_name: str) -> List[TestResult]:
        """运行集成测试"""
        results = []
        test_dir = os.path.join(project_dir, "tests", "integration")
        
        if not os.path.exists(test_dir):
            print(f"⚠ 未找到集成测试目录")
            return results
        
        print(f"\n运行 {project_name} 集成测试...")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_dir, "-v", "--tb=short", "-x"],
                capture_output=True,
                text=True,
                timeout=600,
                cwd=project_dir
            )
            
            status = "passed" if result.returncode == 0 else "failed"
            
            results.append(TestResult(
                test_name=f"{project_name}_integration_tests",
                project_name=project_name,
                test_type="integration",
                status=status,
                duration=0.0,
                message=result.stdout[-500:],
                error_details=result.stderr[-500:]
            ))
            
            print(f"{'✓' if status == 'passed' else '✗'} 集成测试: {status}")
            
        except subprocess.TimeoutExpired:
            results.append(TestResult(
                test_name=f"{project_name}_integration_tests",
                project_name=project_name,
                test_type="integration",
                status="error",
                duration=600.0,
                message="测试超时"
            ))
        except Exception as e:
            results.append(TestResult(
                test_name=f"{project_name}_integration_tests",
                project_name=project_name,
                test_type="integration",
                status="error",
                duration=0.0,
                message=str(e)
            ))
        
        self.test_results.extend(results)
        return results
    
    def run_system_tests(self, project_dir: str, project_name: str) -> List[TestResult]:
        """运行系统测试"""
        results = []
        test_dir = os.path.join(project_dir, "tests", "system")
        
        if not os.path.exists(test_dir):
            print(f"⚠ 未找到系统测试目录")
            return results
        
        print(f"\n运行 {project_name} 系统测试...")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_dir, "-v", "--tb=short", "-x"],
                capture_output=True,
                text=True,
                timeout=900,
                cwd=project_dir
            )
            
            status = "passed" if result.returncode == 0 else "failed"
            
            results.append(TestResult(
                test_name=f"{project_name}_system_tests",
                project_name=project_name,
                test_type="system",
                status=status,
                duration=0.0,
                message=result.stdout[-500:],
                error_details=result.stderr[-500:]
            ))
            
            print(f"{'✓' if status == 'passed' else '✗'} 系统测试: {status}")
            
        except subprocess.TimeoutExpired:
            results.append(TestResult(
                test_name=f"{project_name}_system_tests",
                project_name=project_name,
                test_type="system",
                status="error",
                duration=900.0,
                message="测试超时"
            ))
        except Exception as e:
            results.append(TestResult(
                test_name=f"{project_name}_system_tests",
                project_name=project_name,
                test_type="system",
                status="error",
                duration=0.0,
                message=str(e)
            ))
        
        self.test_results.extend(results)
        return results
    
    def run_all_tests(self, project_dir: str, project_name: str) -> Dict[str, List[TestResult]]:
        """运行所有测试"""
        return {
            "unit": self.run_unit_tests(project_dir, project_name),
            "integration": self.run_integration_tests(project_dir, project_name),
            "system": self.run_system_tests(project_dir, project_name)
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """获取测试摘要"""
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r.status == "passed")
        failed = sum(1 for r in self.test_results if r.status == "failed")
        errors = sum(1 for r in self.test_results if r.status == "error")
        skipped = sum(1 for r in self.test_results if r.status == "skipped")
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "skipped": skipped,
            "pass_rate": (passed / total * 100) if total > 0 else 0,
            "results": self.test_results
        }


class GitHubRealProjectTestRunner:
    """GitHub真实项目测试运行器"""
    
    def __init__(self):
        self.downloader = GitHubProjectDownloader()
        self.tester = RealProjectTester(self.downloader)
        self.projects_to_test = [
            {
                "name": "FastAPI",
                "repo": "https://github.com/tiangolo/fastapi",
                "branch": "master",
                "description": "Modern Python web framework"
            },
            {
                "name": "SQLAlchemy",
                "repo": "https://github.com/sqlalchemy/sqlalchemy",
                "branch": "main",
                "description": "Database toolkit and ORM"
            },
            {
                "name": "Pydantic",
                "repo": "https://github.com/pydantic/pydantic",
                "branch": "main",
                "description": "Data validation using Python type hints"
            },
            {
                "name": "Redis-py",
                "repo": "https://github.com/redis/redis-py",
                "branch": "master",
                "description": "Redis Python client"
            },
            {
                "name": "Prometheus",
                "repo": "https://github.com/prometheus/client_python",
                "branch": "master",
                "description": "Python client for Prometheus"
            }
        ]
    
    def test_project(self, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """测试单个项目"""
        print(f"\n{'='*80}")
        print(f"测试项目: {project_info['name']}")
        print(f"描述: {project_info['description']}")
        print(f"{'='*80}")
        
        try:
            project_dir = self.downloader.clone_project(
                project_info["repo"],
                project_info["branch"]
            )
            
            self.downloader.install_dependencies(project_dir)
            
            test_results = self.tester.run_all_tests(project_dir, project_info["name"])
            
            return {
                "project": project_info["name"],
                "status": "completed",
                "results": test_results
            }
            
        except Exception as e:
            print(f"✗ 测试失败: {str(e)}")
            return {
                "project": project_info["name"],
                "status": "error",
                "error": str(e),
                "results": None
            }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有项目的测试"""
        print(f"\n开始GitHub真实项目集成测试")
        print(f"项目数量: {len(self.projects_to_test)}")
        print(f"临时目录: {self.downloader.temp_dir}")
        
        all_results = {
            "start_time": datetime.utcnow().isoformat(),
            "projects": []
        }
        
        for project_info in self.projects_to_test:
            result = self.test_project(project_info)
            all_results["projects"].append(result)
        
        all_results["end_time"] = datetime.utcnow().isoformat()
        all_results["summary"] = self.tester.get_summary()
        
        return all_results
    
    def cleanup(self):
        """清理资源"""
        self.downloader.cleanup()


def generate_test_report(results: Dict[str, Any]) -> str:
    """生成测试报告"""
    report = f"""
{'='*120}
GitHub真实项目集成测试报告
{'='*120}
测试时间: {results['start_time']} - {results['end_time']}

【测试摘要】
总计测试: {results['summary']['total']}
通过: {results['summary']['passed']} ({results['summary']['pass_rate']:.1f}%)
失败: {results['summary']['failed']}
错误: {results['summary']['errors']}
跳过: {results['summary']['skipped']}

{'='*120}
【各项目测试详情】
{'='*120}
"""
    
    for project_result in results['projects']:
        report += f"\n项目: {project_result['project']}\n"
        report += f"状态: {project_result['status']}\n"
        
        if project_result.get('results'):
            for test_type, tests in project_result['results'].items():
                if tests:
                    for test in tests:
                        status_icon = "✓" if test.status == "passed" else "✗"
                        report += f"  {status_icon} {test.test_name}: {test.status}\n"
                        if test.status != "passed":
                            report += f"    错误: {test.message[:200]}\n"
    
    report += f"""
{'='*120}
【发现问题汇总】
{'='*120}
"""
    
    failed_tests = [r for r in results['summary']['results'] if r.status != 'passed']
    
    if failed_tests:
        for i, test in enumerate(failed_tests, 1):
            report += f"\n问题 {i}: {test.test_name}\n"
            report += f"  项目: {test.project_name}\n"
            report += f"  类型: {test.test_type}\n"
            report += f"  状态: {test.status}\n"
            report += f"  消息: {test.message[:300]}\n"
            if test.error_details:
                report += f"  详情: {test.error_details[:300]}\n"
    else:
        report += "\n✓ 所有测试通过，未发现问题\n"
    
    report += f"""
{'='*120}
"""
    
    return report


if __name__ == "__main__":
    print("="*120)
    print("GitHub真实项目集成测试")
    print("="*120)
    
    runner = GitHubRealProjectTestRunner()
    
    try:
        results = runner.run_all_tests()
        report = generate_test_report(results)
        print(report)
        
        report_file = "/workspace/agent_system/github_integration_test_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n报告已保存到: {report_file}")
        
    finally:
        runner.cleanup()
