"""
可视化网站生成器 - Agent永续自进化系统
自动从代码生成架构图、流程图和时序图
"""
import os
import json
from pathlib import Path
from datetime import datetime, timezone


class ArchitectureVisualizer:
    """架构可视化生成器"""
    
    def __init__(self, project_path: str = "/workspace/agent_system"):
        self.project_path = Path(project_path)
        self.diagrams = {}
        self.metrics = {}
    
    def generate_architecture_diagrams(self) -> dict:
        """生成架构图"""
        print("\n" + "="*80)
        print("生成架构图")
        print("="*80)
        
        diagrams = {
            "seven_layer": self._generate_seven_layer_diagram(),
            "data_flow": self._generate_data_flow_diagram(),
            "evolution_flow": self._generate_evolution_flow_diagram(),
            "sequence": self._generate_sequence_diagram(),
            "component": self._generate_component_diagram()
        }
        
        self.diagrams = diagrams
        return diagrams
    
    def _generate_seven_layer_diagram(self) -> str:
        """生成七层架构图"""
        diagram = '''```mermaid
graph TB
    subgraph API["第一层: API接入层"]
        A1[JWT认证]
        A2[请求验证]
        A3[限流控制]
    end
    
    subgraph ENDPOINTS["第二层: API端点层"]
        E1[任务端点]
        E2[记忆端点]
        E3[知识端点]
    end
    
    subgraph APPLICATION["第三层: 应用服务层"]
        S1[性能基准]
        S2[任务服务]
        S3[进化服务]
    end
    
    subgraph DOMAIN_LOGIC["第四层: 领域逻辑层"]
        D1[任务逻辑]
        D2[记忆逻辑]
        D3[进化引擎]
    end
    
    subgraph DOMAIN_MODEL["第五层: 领域模型层"]
        M1[任务实体]
        M2[记忆实体]
        M3[知识实体]
        M4[策略实体]
    end
    
    subgraph DATA_ACCESS["第六层: 数据访问层"]
        R1[任务仓储]
        R2[记忆仓储]
        R3[知识仓储]
    end
    
    subgraph INFRA["第七层: 基础设施层"]
        I1[日志系统]
        I2[缓存系统]
        I3[监控系统]
        I4[数据库连接]
    end
    
    A1 --> A2 --> A3 --> E1
    A3 --> E2
    A3 --> E3
    
    E1 --> S1 --> D1 --> M1 --> R1 --> I4
    E2 --> S2 --> D2 --> M2 --> R2 --> I4
    E3 --> S3 --> D3 --> M3 --> R3 --> I4
    
    I1 --> INFRA
    I2 --> INFRA
    I3 --> INFRA
    I4 --> INFRA
```'''
        print("✓ 七层架构图生成完成")
        return diagram
    
    def _generate_data_flow_diagram(self) -> str:
        """生成数据流图"""
        diagram = '''```mermaid
flowchart LR
    subgraph INPUT["输入"]
        U[用户请求]
        A[Agent任务]
        S[调度器]
    end
    
    subgraph PROCESSING["处理"]
        V[验证层]
        L[日志层]
        C[缓存层]
        D[领域层]
    end
    
    subgraph OUTPUT["输出"]
        R[结果]
        M[监控数据]
        L2[日志]
    end
    
    INPUT --> V --> C --> D --> R
    D --> L --> L2
    C --> M
    D --> M
```'''
        print("✓ 数据流图生成完成")
        return diagram
    
    def _generate_evolution_flow_diagram(self) -> str:
        """生成进化流程图"""
        diagram = '''```mermaid
flowchart TD
    START([启动]) --> INIT[初始化种群]
    INIT --> EVAL[评估适应度]
    EVAL --> SELECT[选择父代]
    SELECT --> CROSS[基因交叉]
    CROSS --> MUTATE[基因突变]
    MUTATE --> NEW_GEN[生成新种群]
    NEW_GEN --> EVAL
    EVAL --> CHECK{收敛?}
    CHECK -->|否| SELECT
    CHECK -->|是| COMPLETE([进化完成])
```'''
        print("✓ 进化流程图生成完成")
        return diagram
    
    def _generate_sequence_diagram(self) -> str:
        """生成时序图"""
        diagram = '''```mermaid
sequenceDiagram
    participant C as 客户端
    participant G as API网关
    participant A as 应用服务
    participant D as 领域逻辑
    participant R as 数据访问
    participant DB as 数据库
    
    C->>G: 发送请求
    G->>G: JWT验证
    G->>A: 转发请求
    A->>D: 调用领域逻辑
    D->>R: 数据操作
    R->>DB: 数据库查询
    DB-->>R: 返回结果
    R-->>D: 返回数据
    D-->>A: 返回结果
    A-->>G: 返回响应
    G-->>C: 返回结果
```'''
        print("✓ 时序图生成完成")
        return diagram
    
    def _generate_component_diagram(self) -> str:
        """生成组件图"""
        diagram = '''```mermaid
graph LR
    subgraph FRONTEND["前端"]
        W[Web界面]
        API[API文档]
    end
    
    subgraph BACKEND["后端"]
        MAIN[主应用]
        subgraph LAYERS["七层架构"]
            L1[API接入层]
            L2[API端点层]
            L3[应用服务层]
            L4[领域逻辑层]
            L5[领域模型层]
            L6[数据访问层]
            L7[基础设施层]
        end
    end
    
    subgraph DATA["数据层"]
        SQL[(SQLite)]
        CACHE[(Redis)]
        LOG[日志]
    end
    
    W --> L1
    API --> L2
    L1 --> L2 --> L3 --> L4 --> L5 --> L6 --> L7
    L6 --> SQL
    L7 --> CACHE
    L7 --> LOG
```'''
        print("✓ 组件图生成完成")
        return diagram
    
    def collect_metrics(self) -> dict:
        """收集系统指标"""
        print("\n" + "="*80)
        print("收集系统指标")
        print("="*80)
        
        metrics = {
            "files": self._count_files(),
            "layers": self._analyze_layers(),
            "tests": self._analyze_tests(),
            "dependencies": self._analyze_dependencies()
        }
        
        self.metrics = metrics
        return metrics
    
    def _count_files(self) -> dict:
        """统计文件"""
        counts = {
            "total": 0,
            "python": 0,
            "test": 0,
            "config": 0
        }
        
        for ext in ["*.py", "*.json", "*.yaml", "*.toml"]:
            for f in self.project_path.rglob(ext):
                if f.is_file():
                    counts["total"] += 1
                    if ext == "*.py":
                        counts["python"] += 1
                        if "test" in f.name or "tests" in str(f):
                            counts["test"] += 1
                    elif ext in ["*.json", "*.yaml", "*.toml"]:
                        counts["config"] += 1
        
        print(f"✓ 文件统计: {counts}")
        return counts
    
    def _analyze_layers(self) -> dict:
        """分析架构层"""
        layers = {
            "api_access": {"files": 0, "description": "API接入层"},
            "api_endpoints": {"files": 0, "description": "API端点层"},
            "application_services": {"files": 0, "description": "应用服务层"},
            "domain_logic": {"files": 0, "description": "领域逻辑层"},
            "domain_model": {"files": 0, "description": "领域模型层"},
            "data_access": {"files": 0, "description": "数据访问层"},
            "infrastructure": {"files": 0, "description": "基础设施层"}
        }
        
        for layer_name in layers.keys():
            layer_path = self.project_path / layer_name
            if layer_path.exists():
                layers[layer_name]["files"] = len(list(layer_path.rglob("*.py")))
        
        print(f"✓ 架构层分析完成")
        return layers
    
    def _analyze_tests(self) -> dict:
        """分析测试"""
        tests = {
            "unit": 0,
            "integration": 0,
            "system": 0
        }
        
        tests_dir = self.project_path / "tests"
        if tests_dir.exists():
            for subdir in ["unit", "integration", "system", "real_project"]:
                subdir_path = tests_dir / subdir
                if subdir_path.exists():
                    tests[subdir] = len(list(subdir_path.rglob("test_*.py")))
        
        print(f"✓ 测试分析完成: {tests}")
        return tests
    
    def _analyze_dependencies(self) -> dict:
        """分析依赖"""
        deps = {
            "total": 0,
            "main": [],
            "dev": []
        }
        
        req_file = self.project_path / "requirements.txt"
        if req_file.exists():
            with open(req_file, 'r') as f:
                lines = f.readlines()
                deps["total"] = len([l for l in lines if l.strip() and not l.startswith("#")])
                deps["main"] = [l.strip().split(">=")[0].split("==")[0] for l in lines if ">=" in l][:5]
        
        print(f"✓ 依赖分析完成: {deps['total']}个")
        return deps
    
    def generate_html(self, output_path: str = "/workspace/agent_system/visualization/index.html"):
        """生成HTML可视化页面"""
        print("\n" + "="*80)
        print("生成HTML可视化页面")
        print("="*80)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        html_content = self._create_html_content()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ HTML页面已生成: {output_path}")
        return output_path
    
    def _create_html_content(self) -> str:
        """创建HTML内容"""
        diagrams_json = json.dumps(self.diagrams, ensure_ascii=False)
        metrics_json = json.dumps(self.metrics, ensure_ascii=False)
        
        html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent永续自进化系统 - 架构可视化</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        :root {
            --primary: #6366f1;
            --secondary: #8b5cf6;
            --accent: #ec4899;
            --bg-dark: #0f172a;
            --bg-card: #1e293b;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --border: #334155;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            line-height: 1.6;
        }
        
        .header {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            padding: 2rem;
            text-align: center;
            box-shadow: 0 4px 20px rgba(99, 102, 241, 0.3);
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            background: linear-gradient(to right, #fff, #e0e7ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .header p {
            color: #c7d2fe;
            font-size: 1.1rem;
        }
        
        .nav {
            background: var(--bg-card);
            padding: 1rem 2rem;
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            border-bottom: 1px solid var(--border);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .nav-btn {
            background: var(--bg-dark);
            border: 1px solid var(--border);
            color: var(--text-primary);
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 0.95rem;
        }
        
        .nav-btn:hover {
            background: var(--primary);
            border-color: var(--primary);
            transform: translateY(-2px);
        }
        
        .nav-btn.active {
            background: var(--primary);
            border-color: var(--primary);
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .metric-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            transition: all 0.3s;
        }
        
        .metric-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 25px rgba(99, 102, 241, 0.2);
        }
        
        .metric-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: var(--primary);
            margin-bottom: 0.5rem;
        }
        
        .metric-label {
            color: var(--text-secondary);
            font-size: 0.9rem;
        }
        
        .section {
            display: none;
        }
        
        .section.active {
            display: block;
        }
        
        .diagram-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
        }
        
        .diagram-title {
            font-size: 1.5rem;
            margin-bottom: 1.5rem;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .diagram-title::before {
            content: '';
            width: 4px;
            height: 24px;
            background: linear-gradient(to bottom, var(--primary), var(--accent));
            border-radius: 2px;
        }
        
        .mermaid {
            background: var(--bg-dark);
            border-radius: 8px;
            padding: 1.5rem;
            overflow-x: auto;
        }
        
        .layer-list {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
        }
        
        .layer-item {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            transition: all 0.3s;
        }
        
        .layer-item:hover {
            border-color: var(--primary);
            transform: translateX(4px);
        }
        
        .layer-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        
        .layer-name {
            font-weight: 600;
            color: var(--text-primary);
        }
        
        .layer-badge {
            background: var(--primary);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.85rem;
        }
        
        .layer-desc {
            color: var(--text-secondary);
            font-size: 0.9rem;
        }
        
        .layer-files {
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border);
            color: var(--text-secondary);
            font-size: 0.85rem;
        }
        
        .footer {
            text-align: center;
            padding: 2rem;
            color: var(--text-secondary);
            border-top: 1px solid var(--border);
            margin-top: 3rem;
        }
        
        .timestamp {
            color: var(--primary);
            font-weight: 600;
        }
        
        @media (max-width: 768px) {
            .header h1 {
                font-size: 1.8rem;
            }
            
            .nav {
                padding: 1rem;
            }
            
            .nav-btn {
                padding: 0.5rem 1rem;
                font-size: 0.85rem;
            }
            
            .container {
                padding: 1rem;
            }
        }
        
        .fade-in {
            animation: fadeIn 0.5s ease-in;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 Agent永续自进化系统</h1>
        <p>七层Clean Architecture 架构可视化</p>
    </div>
    
    <nav class="nav">
        <button class="nav-btn active" onclick="showSection('overview')">📊 总览</button>
        <button class="nav-btn" onclick="showSection('architecture')">🏗️ 架构图</button>
        <button class="nav-btn" onclick="showSection('flow')">📈 流程图</button>
        <button class="nav-btn" onclick="showSection('sequence')">⏱️ 时序图</button>
        <button class="nav-btn" onclick="showSection('layers')">📁 架构层</button>
        <button class="nav-btn" onclick="location.reload()">🔄 刷新</button>
    </nav>
    
    <div class="container">
        <section id="overview" class="section active">
            <div class="metrics-grid" id="metricsGrid">
                <!-- Metrics will be inserted here -->
            </div>
        </section>
        
        <section id="architecture" class="section">
            <div class="diagram-card fade-in">
                <h2 class="diagram-title">七层Clean Architecture架构图</h2>
                <div class="mermaid" id="sevenLayerDiagram"></div>
            </div>
            
            <div class="diagram-card fade-in">
                <h2 class="diagram-title">组件关系图</h2>
                <div class="mermaid" id="componentDiagram"></div>
            </div>
        </section>
        
        <section id="flow" class="section">
            <div class="diagram-card fade-in">
                <h2 class="diagram-title">数据流图</h2>
                <div class="mermaid" id="dataFlowDiagram"></div>
            </div>
            
            <div class="diagram-card fade-in">
                <h2 class="diagram-title">进化流程图</h2>
                <div class="mermaid" id="evolutionFlowDiagram"></div>
            </div>
        </section>
        
        <section id="sequence" class="section">
            <div class="diagram-card fade-in">
                <h2 class="diagram-title">请求处理时序图</h2>
                <div class="mermaid" id="sequenceDiagram"></div>
            </div>
        </section>
        
        <section id="layers" class="section">
            <div class="layer-list" id="layerList">
                <!-- Layers will be inserted here -->
            </div>
        </section>
    </div>
    
    <footer class="footer">
        <p>最后更新: <span class="timestamp" id="lastUpdate"></span></p>
        <p style="margin-top: 0.5rem;">Agent永续自进化系统 v2.7.0 | 可视化版本</p>
    </footer>
    
    <script>
        mermaid.initialize({
            startOnLoad: true,
            theme: 'dark',
            themeVariables: {
                primaryColor: '#6366f1',
                primaryTextColor: '#f1f5f9',
                primaryBorderColor: '#8b5cf6',
                lineColor: '#94a3b8',
                secondaryColor: '#1e293b',
                tertiaryColor: '#0f172a'
            }
        });
        
        const diagrams = ''' + diagrams_json + ''';
        const metrics = ''' + metrics_json + ''';
        
        function showSection(sectionId) {
            document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
            document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
            
            document.getElementById(sectionId).classList.add('active');
            event.target.classList.add('active');
            
            if (sectionId === 'architecture' || sectionId === 'flow' || sectionId === 'sequence') {
                mermaid.run();
            }
        }
        
        function renderMetrics() {
            const grid = document.getElementById('metricsGrid');
            grid.innerHTML = `
                <div class="metric-card">
                    <div class="metric-value">${metrics.files.total}</div>
                    <div class="metric-label">总文件数</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${metrics.files.python}</div>
                    <div class="metric-label">Python文件</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${metrics.files.test}</div>
                    <div class="metric-label">测试文件</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${metrics.dependencies.total}</div>
                    <div class="metric-label">依赖数量</div>
                </div>
            `;
        }
        
        function renderLayers() {
            const list = document.getElementById('layerList');
            const layerNames = {
                "api_access": "API接入层",
                "api_endpoints": "API端点层",
                "application_services": "应用服务层",
                "domain_logic": "领域逻辑层",
                "domain_model": "领域模型层",
                "data_access": "数据访问层",
                "infrastructure": "基础设施层"
            };
            
            const layerDescs = {
                "api_access": "处理JWT认证、请求验证和限流控制",
                "api_endpoints": "定义RESTful API端点",
                "application_services": "提供业务用例和应用逻辑",
                "domain_logic": "封装核心业务规则和领域模型",
                "domain_model": "定义实体、值对象和聚合根",
                "data_access": "实现Repository模式和数据库操作",
                "infrastructure": "提供日志、缓存、监控等基础设施"
            };
            
            let html = '';
            let i = 1;
            for (const [key, data] of Object.entries(metrics.layers)) {
                html += `
                    <div class="layer-item">
                        <div class="layer-header">
                            <span class="layer-name">第${i}层: ${layerNames[key] || key}</span>
                            <span class="layer-badge">${data.files} 文件</span>
                        </div>
                        <p class="layer-desc">${layerDescs[key] || data.description}</p>
                    </div>
                `;
                i++;
            }
            list.innerHTML = html;
        }
        
        function renderDiagrams() {
            document.getElementById('sevenLayerDiagram').innerHTML = diagrams.seven_layer;
            document.getElementById('componentDiagram').innerHTML = diagrams.component;
            document.getElementById('dataFlowDiagram').innerHTML = diagrams.data_flow;
            document.getElementById('evolutionFlowDiagram').innerHTML = diagrams.evolution_flow;
            document.getElementById('sequenceDiagram').innerHTML = diagrams.sequence;
        }
        
        function updateTimestamp() {
            const now = new Date();
            document.getElementById('lastUpdate').textContent = now.toLocaleString('zh-CN');
        }
        
        document.addEventListener('DOMContentLoaded', () => {
            renderMetrics();
            renderLayers();
            renderDiagrams();
            updateTimestamp();
        });
    </script>
</body>
</html>'''
        return html
    
    def generate(self):
        """生成所有可视化内容"""
        print("\n" + "="*120)
        print("Agent永续自进化系统 - 可视化网站生成器")
        print("="*120)
        
        # 生成架构图
        self.generate_architecture_diagrams()
        
        # 收集指标
        self.collect_metrics()
        
        # 生成HTML
        html_path = self.generate_html()
        
        print("\n" + "="*120)
        print("✅ 可视化网站生成完成！")
        print("="*120)
        print(f"📁 文件位置: {html_path}")
        print(f"📊 架构图: 5个")
        print(f"📈 指标数据: {self.metrics['files']['total']}个文件")
        print("="*120)
        
        return html_path


if __name__ == "__main__":
    visualizer = ArchitectureVisualizer()
    html_path = visualizer.generate()
    print(f"\n✨ 打开 {html_path} 查看可视化效果")
