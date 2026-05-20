# Agent永续自进化系统 - 可视化网站

## 📖 概述

本目录包含Agent永续自进化系统的完整可视化网站，展示系统的架构图、流程图和时序图。

## 📁 目录结构

```
visualization/
├── index.html      # 可视化网站主页面
├── generator.py    # 可视化生成器
├── watcher.py      # 文件变化监视器
└── README.md       # 本文档
```

## 🚀 快速开始

### 1. 查看可视化

直接在浏览器中打开 `index.html` 文件：

```bash
# Linux/macOS
xdg-open visualization/index.html
open visualization/index.html

# Windows
start visualization/index.html
```

### 2. 自动更新可视化

运行文件监视器，当代码文件变化时自动更新可视化：

```bash
cd /workspace/agent_system
python visualization/watcher.py
```

修改任何 `.py` 文件后，可视化网站将自动重新生成。

### 3. 手动重新生成

如果需要手动重新生成可视化：

```bash
cd /workspace/agent_system
python visualization/generator.py
```

## 📊 可视化内容

### 1. 架构图
- **七层Clean Architecture架构图**: 展示系统的七层架构
- **组件关系图**: 展示各组件之间的关系

### 2. 流程图
- **数据流图**: 展示数据在系统中的流动
- **进化流程图**: 展示遗传算法的进化过程

### 3. 时序图
- **请求处理时序图**: 展示请求处理的完整流程

### 4. 架构层详情
- 七层架构的详细说明
- 每层的功能描述
- 文件数量统计

## 🎨 网站功能

### 导航栏
- **总览**: 显示系统指标统计
- **架构图**: 显示架构相关图表
- **流程图**: 显示流程相关图表
- **时序图**: 显示时序相关图表
- **架构层**: 显示各层详细信息
- **刷新**: 重新加载页面

### 指标卡片
- 总文件数
- Python文件数
- 测试文件数
- 依赖数量

## 🔧 技术栈

- **Mermaid.js**: 图表渲染
- **纯HTML/CSS/JS**: 无需构建工具
- **响应式设计**: 支持移动端访问

## 📝 自动化

### 文件监视器

`watcher.py` 使用 `watchdog` 库监控项目文件变化：

- 监视所有 `.py`、`.json`、`.yaml` 文件
- 防抖处理：避免频繁更新
- 自动重新生成可视化

安装依赖：

```bash
pip install watchdog
```

## 🎯 使用场景

1. **项目演示**: 向团队展示系统架构
2. **文档生成**: 自动生成架构文档
3. **代码审查**: 可视化代码结构
4. **教学培训**: 帮助理解系统设计

## 📦 生成器API

### ArchitectureVisualizer 类

```python
from visualization.generator import ArchitectureVisualizer

# 创建可视化器
visualizer = ArchitectureVisualizer("/path/to/project")

# 生成所有图表
diagrams = visualizer.generate_architecture_diagrams()

# 收集系统指标
metrics = visualizer.collect_metrics()

# 生成HTML文件
html_path = visualizer.generate_html()

# 一键生成所有内容
visualizer.generate()
```

### 自定义图表

可以在 `generator.py` 中添加新的图表：

```python
def _generate_custom_diagram(self) -> str:
    """生成自定义图表"""
    return '''```mermaid
    flowchart TD
        A[开始] --> B[处理]
        B --> C[结束]
    ```'''
```

## 📄 文件说明

### generator.py
- 自动分析项目结构
- 生成Mermaid图表代码
- 收集系统指标
- 生成完整的HTML页面

### watcher.py
- 使用 watchdog 监控文件变化
- 防抖处理避免频繁更新
- 自动调用生成器

### index.html
- 响应式设计
- Mermaid.js图表渲染
- 实时指标显示
- 自动刷新支持

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📜 许可证

本项目采用 MIT 许可证。

---

**最后更新**: [[last-update]]
**版本**: 2.7.0
