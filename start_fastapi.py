#!/usr/bin/env python3
"""
Agent永续自进化系统 - 快速启动脚本
一键启动Web服务
"""
import sys
import os
import subprocess
from pathlib import Path

def print_banner():
    """打印横幅"""
    print("=" * 80)
    print("  Agent永续自进化系统 v2.8.0")
    print("  FastAPI Web服务启动器")
    print("=" * 80)
    print()

def check_dependencies():
    """检查依赖"""
    print("1. 检查依赖...")
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "sqlalchemy",
        "structlog"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✓ {package}")
        except ImportError:
            print(f"   ✗ {package} (缺失)")
            missing.append(package)
    
    if missing:
        print(f"\n缺少依赖包: {', '.join(missing)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    print("   ✓ 所有依赖已就绪\n")
    return True

def run_tests():
    """运行测试"""
    print("2. 运行测试...")
    
    test_script = Path(__file__).parent / "test_fastapi_app.py"
    
    if test_script.exists():
        result = subprocess.run([sys.executable, str(test_script)], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("   ✓ 测试通过\n")
            return True
        else:
            print("   ✗ 测试失败")
            print(result.stdout)
            print(result.stderr)
            return False
    else:
        print("   ⚠ 测试脚本不存在，跳过测试\n")
        return True

def start_server():
    """启动服务器"""
    print("3. 启动Web服务...")
    print()
    print("服务地址:")
    print("   - 主地址: http://localhost:8000")
    print("   - API文档: http://localhost:8000/docs")
    print("   - ReDoc文档: http://localhost:8000/redoc")
    print()
    print("按 Ctrl+C 停止服务")
    print("=" * 80)
    print()
    
    try:
        import uvicorn
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n服务已停止")
    except Exception as e:
        print(f"\n启动失败: {str(e)}")
        return False
    
    return True

def main():
    """主函数"""
    print_banner()
    
    if not check_dependencies():
        sys.exit(1)
    
    if not run_tests():
        response = input("\n测试失败，是否继续启动服务? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    start_server()

if __name__ == "__main__":
    main()
