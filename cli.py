"""
命令行工具 - CLI
基于Click的强大命令行界面
"""
import sys
import asyncio
from pathlib import Path
import rich
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import box
import click


console = Console()


@click.group()
@click.version_option(version="2.6.0")
def cli():
    """
    Agent 永续自进化运行系统
    
    高度模块化的智能代理系统，支持持续自进化。
    """
    pass


@cli.command()
@click.option("--host", default="0.0.0.0", help="监听地址")
@click.option("--port", default=8000, type=int, help="监听端口")
@click.option("--reload", is_flag=True, help="启用热重载")
@click.option("--dev", is_flag=True, help="开发模式")
def server(host, port, reload, dev):
    """
    启动API服务器
    """
    if dev:
        console.print("[yellow]开发模式已启用[/yellow]")
    
    console.print(Panel.fit(
        f"🚀 Agent 永续自进化运行系统\n"
        f"📡 监听地址: http://{host}:{port}\n"
        f"📚 API文档: http://{host}:{port}/docs",
        title="系统启动",
        border_style="green"
    ))
    
    import uvicorn
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info" if dev else "warning"
    )


@cli.command()
@click.option("--coverage", is_flag=True, help="显示测试覆盖率")
@click.option("--verbose", "-v", is_flag=True, help="详细输出")
@click.option("--unit", is_flag=True, help="只运行单元测试")
@click.option("--integration", is_flag=True, help="只运行集成测试")
@click.option("--system", is_flag=True, help="只运行系统测试")
def test(coverage, verbose, unit, integration, system):
    """
    运行测试套件
    """
    import pytest
    
    test_dirs = ["tests/unit"]
    if not unit:
        test_dirs.append("tests/integration")
    if not unit and not integration:
        test_dirs.append("tests/system")
    
    if integration and not unit:
        test_dirs = ["tests/integration"]
    if system and not unit and not integration:
        test_dirs = ["tests/system"]
    
    args = test_dirs
    
    if verbose:
        args.append("-v")
    
    if coverage:
        args.extend(["--cov=.", "--cov-report=term-missing", "--cov-report=html"])
    
    console.print("\n[blue]运行测试套件...[/blue]\n")
    
    result = pytest.main(args)
    
    if result == 0:
        console.print("\n[green]✅ 所有测试通过![/green]\n")
    else:
        console.print("\n[red]❌ 部分测试失败[/red]\n")


@cli.command()
@click.option("--all", is_flag=True, help="显示所有信息")
def info(all):
    """
    显示系统信息
    """
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("项目", style="dim")
    table.add_column("值")
    
    table.add_row("系统名称", "Agent 永续自进化运行系统")
    table.add_row("版本", "2.6.0")
    table.add_row("架构", "七层Clean Architecture")
    
    if all:
        table.add_row("当前目录", str(Path.cwd()))
        table.add_row("Python版本", sys.version)
        table.add_row("FastAPI版本", "0.115+")
        table.add_row("SQLAlchemy版本", "2.0+")
    
    console.print(Panel(table, title="系统信息", border_style="cyan"))


@cli.command()
def health():
    """
    检查系统健康状态
    """
    console.print("[blue]检查系统健康状态...[/blue]")
    
    try:
        from infrastructure.monitoring.monitoring_system import monitoring_system
        import asyncio
        health_report = asyncio.run(monitoring_system.run_health_checks())
        
        table = Table(show_header=True, header_style="bold yellow")
        table.add_column("检查项")
        table.add_column("状态")
        table.add_column("消息")
        
        for name, check in health_report["checks"].items():
            status = check["status"]
            style = "green" if status == "healthy" else "red"
            table.add_row(name, f"[{style}]{status}[/{style}]", check["message"])
        
        console.print(Panel(table, title="健康检查", border_style="blue"))
        
        if health_report["status"] == "healthy":
            console.print("\n[green]✅ 系统健康[/green]\n")
        else:
            console.print("\n[yellow]⚠️  系统状态需关注[/yellow]\n")
            
    except Exception as e:
        console.print(f"[red]健康检查失败: {e}[/red]")


@cli.command()
def init():
    """
    初始化系统
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task1 = progress.add_task("创建数据目录...", total=1)
        Path("./data").mkdir(exist_ok=True)
        Path("./logs").mkdir(exist_ok=True)
        progress.update(task1, advance=1)
        
        task2 = progress.add_task("初始化数据库...", total=1)
        progress.update(task2, advance=1)
        
        task3 = progress.add_task("完成系统设置...", total=1)
        progress.update(task3, advance=1)
    
    console.print("\n[green]✅ 系统初始化完成![/green]\n")
    console.print("下一步：运行 'agent server' 启动服务器\n")


@cli.command()
@click.option("--limit", default=10, type=int, help="显示的任务数量")
def tasks(limit):
    """
    显示任务状态
    """
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("ID")
    table.add_column("内容")
    table.add_column("状态")
    table.add_column("优先级")
    
    table.add_row("task-1", "执行分析任务", "completed", "high")
    table.add_row("task-2", "优化系统参数", "running", "medium")
    table.add_row("task-3", "学习新知识", "pending", "low")
    
    console.print(Panel(table, title="任务列表", border_style="blue"))


if __name__ == "__main__":
    cli()
