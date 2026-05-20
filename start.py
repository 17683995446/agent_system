#!/usr/bin/env python3
"""
Agent永续自进化系统 - 快速启动脚本
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path


def print_banner():
    """打印欢迎横幅"""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   🤖  AGENT ETERNAL EVOLUTION SYSTEM v2.7.2                  ║
║                                                               ║
║   7-Layer Clean Architecture AI Agent Self-Evolution        ║
║                                                               ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def setup_environment():
    """设置环境"""
    print("\n📋 正在检查环境...")
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version < (3, 9):
        print(f"⚠️  Python版本过低 (3.9+ 推荐，当前: {python_version.major}.{python_version.minor}")
    else:
        print(f"✅ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 检查依赖
    requirements_file = Path(__file__).parent / "requirements.txt"
    if requirements_file.exists():
        print(f"✅ 找到requirements.txt")
    else:
        print(f"⚠️  未找到requirements.txt")


def install_dependencies():
    """安装依赖"""
    print("\n📦 正在检查依赖...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✅ 依赖安装成功")
        else:
            print(f"⚠️  依赖安装完成 (returncode: {result.returncode}")
    except Exception as e:
        print(f"⚠️  依赖安装遇到问题: {e}")


def run_tests():
    """运行所有测试"""
    print("\n🧪 正在运行综合测试...")
    try:
        result = subprocess.run(
            [sys.executable, "tests/run_all_tests.py"],
            capture_output=False
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 测试运行失败: {e}")
        return False


def start_server():
    """启动Web服务器"""
    print("\n🌐 启动可视化Web服务器...")
    print("   访问地址: http://localhost:8000")
    print("   按 Ctrl+C 停止服务器\n")
    
    try:
        os.chdir(Path(__file__).parent / "visualization")
        subprocess.run([sys.executable, "-m", "http.server", "8000"])
    except KeyboardInterrupt:
        print("\n\n👋 服务器已停止")


def generate_visualization():
    """生成可视化文件"""
    print("\n📊 正在生成可视化文件...")
    try:
        os.chdir(Path(__file__).parent)
        result = subprocess.run(
            [sys.executable, "visualization/generator.py"],
            capture_output=False
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 可视化生成失败: {e}")
        return False


def show_help():
    """显示帮助信息"""
    help_text = """
🤖 Agent永续自进化系统 - 使用指南
═══════════════════════════════════
使用方法:
  python start.py [命令]

命令:
  install    安装依赖
  test      运行综合测试
  visual    生成可视化文件
  serve     启动可视化Web服务器
  all       一键启动完整流程

示例:
  python start.py all      # 安装依赖 → 运行测试 → 启动服务器
  python start.py test     # 只运行测试
  python start.py serve  # 启动服务器
    """
    print(help_text)


def main():
    parser = argparse.ArgumentParser(description="Agent永续自进化系统 - 快速启动")
    parser.add_argument("command", choices=["install", "test", "visual", "serve", "all"],
                        help="要执行的命令 (install, test, visual, serve, all)")
    
    args = parser.parse_args()
    
    print_banner()
    
    if args.command == "install":
        setup_environment()
        install_dependencies()
    elif args.command == "test":
        setup_environment()
        run_tests()
    elif args.command == "visual":
        setup_environment()
        generate_visualization()
    elif args.command == "serve":
        setup_environment()
        start_server()
    elif args.command == "all":
        setup_environment()
        install_dependencies()
        if run_tests():
            generate_visualization()
            start_server()
    else:
        show_help()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_banner()
        show_help()
    else:
        main()
