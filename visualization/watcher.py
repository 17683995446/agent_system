#!/usr/bin/env python3
"""
可视化网站自动化更新脚本
监控项目文件变化，自动更新可视化网站
"""
import os
import sys
import time
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class ArchitectureWatcher(FileSystemEventHandler):
    """架构文件监视器"""
    
    def __init__(self, generator_path: str, html_path: str, debounce_seconds: int = 2):
        super().__init__()
        self.generator_path = Path(generator_path)
        self.html_path = Path(html_path)
        self.debounce_seconds = debounce_seconds
        self.last_update = 0
        self.file_hashes = {}
        
        # 初始化文件哈希
        self._update_file_hashes()
    
    def _update_file_hashes(self):
        """更新文件哈希"""
        project_path = self.generator_path.parent
        
        for ext in ["*.py", "*.json", "*.yaml"]:
            for file_path in project_path.rglob(ext):
                if file_path.is_file():
                    try:
                        content = file_path.read_bytes()
                        self.file_hashes[str(file_path)] = hashlib.md5(content).hexdigest()
                    except:
                        pass
    
    def _should_update(self) -> bool:
        """检查是否应该更新"""
        current_time = time.time()
        if current_time - self.last_update < self.debounce_seconds:
            return False
        return True
    
    def _regenerate_visualization(self):
        """重新生成可视化"""
        try:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔄 检测到文件变化，正在更新可视化...")
            
            # 运行生成器
            result = subprocess.run(
                [sys.executable, str(self.generator_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 可视化更新成功！")
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 📁 查看: {self.html_path}")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 更新失败: {result.stderr[:200]}")
            
            self.last_update = time.time()
            
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 更新出错: {e}")
    
    def on_modified(self, event):
        """文件修改事件"""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # 忽略可视化目录本身
        if "visualization" in str(file_path) or "node_modules" in str(file_path):
            return
        
        # 检查是否是项目文件
        if file_path.suffix not in [".py", ".json", ".yaml", ".toml"]:
            return
        
        try:
            # 检查文件内容是否真的变化
            current_content = file_path.read_bytes()
            current_hash = hashlib.md5(current_content).hexdigest()
            old_hash = self.file_hashes.get(str(file_path), "")
            
            if current_hash != old_hash:
                self.file_hashes[str(file_path)] = current_hash
                
                if self._should_update():
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 📝 文件已修改: {file_path.name}")
                    self._regenerate_visualization()
                    
        except Exception as e:
            print(f"检查文件变化时出错: {e}")
    
    def on_created(self, event):
        """文件创建事件"""
        if not event.is_directory:
            file_path = Path(event.src_path)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✨ 新文件: {file_path.name}")
            
            if self._should_update():
                self._regenerate_visualization()
    
    def on_deleted(self, event):
        """文件删除事件"""
        if not event.is_directory:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🗑️  文件删除: {Path(event.src_path).name}")


def run_watcher(generator_path: str, html_path: str, watch_path: str = None):
    """运行文件监视器"""
    if watch_path is None:
        watch_path = Path(generator_path).parent
    
    print("="*80)
    print("🔍 Agent永续自进化系统 - 可视化自动更新")
    print("="*80)
    print(f"📁 监视目录: {watch_path}")
    print(f"📝 生成器: {generator_path}")
    print(f"🌐 输出文件: {html_path}")
    print("="*80)
    print("提示: 修改Python文件后，可视化网站将自动更新")
    print("按 Ctrl+C 停止监视")
    print("="*80)
    
    event_handler = ArchitectureWatcher(generator_path, html_path)
    observer = Observer()
    observer.schedule(event_handler, str(watch_path), recursive=True)
    observer.start()
    
    try:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🚀 监视已启动...")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n\n[{datetime.now().strftime('%H:%M:%S')}] 🛑 正在停止监视...")
        observer.stop()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 监视已停止")
    
    observer.join()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="可视化网站自动更新工具")
    parser.add_argument(
        "--generator",
        default="/workspace/agent_system/visualization/generator.py",
        help="生成器脚本路径"
    )
    parser.add_argument(
        "--output",
        default="/workspace/agent_system/visualization/index.html",
        help="输出HTML路径"
    )
    parser.add_argument(
        "--watch",
        default=None,
        help="监视的目录路径"
    )
    
    args = parser.parse_args()
    
    run_watcher(args.generator, args.output, args.watch)
