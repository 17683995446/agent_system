import React, { useState } from 'react';
import { Card } from '../components/Card';
import { MermaidDiagram } from '../components/MermaidDiagram';

export const Architecture: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');

  const tabs = [
    { id: 'overview', name: '系统概览' },
    { id: 'dataflow', name: '数据流图' },
    { id: 'sequence', name: '时序图' },
    { id: 'deployment', name: '部署架构' },
    { id: 'er', name: '数据模型' },
  ];

  const systemArchitecture = `graph TB
    subgraph Frontend[前端层]
        FE[React + TypeScript<br/>Tailwind CSS<br/>Vite]
    end
    
    subgraph API[API网关层]
        APIGW[FastAPI REST API<br/>CORS & Auth Middleware<br/>Request Validator]
    end
    
    subgraph Services[核心业务层]
        TENANT[多租户服务<br/>TenantService]
        SERV[服务网格<br/>ServiceMeshService]
        EVO[AI进化引擎<br/>EvolutionService]
        MEM[记忆系统<br/>MemoryService]
        TSK[任务系统<br/>TaskService]
    end
    
    subgraph Infra[基础设施层]
        DB[数据库<br/>SQLite/PostgreSQL]
        CACHE[缓存<br/>Redis]
        MONITOR[监控系统<br/>Prometheus + Grafana]
    end

    FE--&gt;|HTTP/REST|APIGW
    APIGW--&gt;|调用|TENANT
    APIGW--&gt;|调用|SERV
    APIGW--&gt;|调用|EVO
    APIGW--&gt;|调用|MEM
    APIGW--&gt;|调用|TSK
    TENANT--&gt;|读写|DB
    SERV--&gt;|使用|CACHE
    EVO--&gt;|读写|DB
    MEM--&gt;|读写|DB
    MONITOR--&gt;|监控|APIGW
    MONITOR--&gt;|监控|TENANT
    MONITOR--&gt;|监控|SERV
`;

  const dataFlow = `graph LR
    subgraph UserLayer[用户交互层]
        User[用户请求]
    end
    
    subgraph RequestLayer[请求处理层]
        Router[API路由]
        Auth[认证鉴权]
        Validator[参数验证]
    end
    
    subgraph LogicLayer[业务逻辑层]
        Logic[业务处理]
        Cache[缓存检查]
        DB[数据库操作]
    end
    
    subgraph ResponseLayer[响应返回层]
        Transform[数据转换]
        Response[响应返回]
    end

    User--&gt;|1. HTTP Request|Router
    Router--&gt;|2. 路由分发|Auth
    Auth--&gt;|3. 验证通过|Validator
    Validator--&gt;|4. 参数合法|Logic
    Logic--&gt;|5. 检查缓存|Cache
    Cache--&gt;|6a. 缓存命中|Transform
    Cache--&gt;|6b. 缓存未命中|DB
    DB--&gt;|7. 数据返回|Logic
    Logic--&gt;|8. 更新缓存|Cache
    Logic--&gt;|9. 处理结果|Transform
    Transform--&gt;|10. HTTP Response|Response
    Response--&gt;|11. 渲染展示|User
`;

  const sequenceDiagram = `sequenceDiagram
    autonumber
    participant User
    participant FE as 前端
    participant API as API网关
    participant Auth as 认证服务
    participant Tenant as 租户服务
    participant DB as 数据库

    User-&gt;&gt;FE: 访问系统
    FE-&gt;&gt;API: 请求 API
    API-&gt;&gt;Auth: 验证 Token
    Auth--&gt;&gt;API: 认证通过
    API-&gt;&gt;Tenant: 获取租户信息
    Tenant-&gt;&gt;DB: 查询数据
    DB--&gt;&gt;Tenant: 返回结果
    Tenant--&gt;&gt;API: 处理结果
    API--&gt;&gt;FE: JSON 响应
    FE--&gt;&gt;User: 渲染页面
`;

  const deploymentArchitecture = `graph TB
    subgraph K8S[Kubernetes 集群]
        subgraph FrontendSvc[前端服务]
            FE[Frontend Pods<br/>React + Vite]
        end
        
        subgraph BackendSvc[后端服务]
            API[API Pods<br/>FastAPI]
            Worker[Worker Pods<br/>AI Evolution]
        end
        
        subgraph DataSvc[数据服务]
            DB[(PostgreSQL HA)]
            Redis[(Redis Cluster)]
        end
        
        subgraph MonitorSvc[监控服务]
            Prom[Prometheus]
            Grafana[Grafana]
        end
        
        LB[LoadBalancer<br/>Ingress Nginx]
        LB--&gt;FE
        LB--&gt;API
        FE--&gt;API
        API--&gt;Worker
        API--&gt;DB
        API--&gt;Redis
        Worker--&gt;DB
        Prom--&gt;API
        Prom--&gt;Worker
        Grafana--&gt;Prom
    end
    
    CDN[CDN / Cloudflare]
    CDN--&gt;LB
    
    User[用户]
    User--&gt;CDN
`;

  const erDiagram = `erDiagram
    TENANT ||--o{ TENANT_USER : has
    TENANT ||--o{ TENANT_QUOTA : has
    TENANT ||--o{ TENANT_API_KEY : has
    TENANT ||--o{ MEMORY : owns
    TENANT ||--o{ TASK : manages
    SERVICE_INSTANCE ||--o{ SERVICE_METRIC : generates

    TENANT {
        string tenant_id PK
        string name
        string slug
        string email
        string owner_id
        string status
        string tier
        datetime created_at
        datetime updated_at
    }

    TENANT_USER {
        string user_id PK
        string tenant_id FK
        string username
        string email
        string role
        string password_hash
    }

    TENANT_QUOTA {
        string quota_id PK
        string tenant_id FK
        int max_agents
        int max_storage_mb
        int max_requests_per_minute
        int max_api_keys
    }

    TENANT_API_KEY {
        string key_id PK
        string tenant_id FK
        string name
        string hashed_key
        string key_prefix
        datetime expires_at
        boolean is_active
    }

    SERVICE_INSTANCE {
        string instance_id PK
        string service_name
        string service_type
        string version
        string host
        int port
        string status
        float health_score
        float load_factor
        datetime started_at
        datetime last_heartbeat
    }

    SERVICE_METRIC {
        string metric_id PK
        string instance_id FK
        float cpu_usage
        float memory_usage
        int request_count
        float response_time
        datetime timestamp
    }

    MEMORY {
        string memory_id PK
        string tenant_id FK
        string content
        string importance_level
        json metadata
        datetime created_at
    }

    TASK {
        string task_id PK
        string tenant_id FK
        string title
        string description
        string status
        string priority
        datetime created_at
        datetime updated_at
    }
`;

  const renderDiagram = () => {
    switch (activeTab) {
      case 'overview':
        return systemArchitecture;
      case 'dataflow':
        return dataFlow;
      case 'sequence':
        return sequenceDiagram;
      case 'deployment':
        return deploymentArchitecture;
      case 'er':
        return erDiagram;
      default:
        return systemArchitecture;
    }
  };

  const getDescription = () => {
    switch (activeTab) {
      case 'overview':
        return '展示系统的整体架构，从前端到后端各层的关系';
      case 'dataflow':
        return '展示用户请求在系统中的完整处理流程';
      case 'sequence':
        return '展示各组件之间的交互时序';
      case 'deployment':
        return '展示系统的生产环境部署架构';
      case 'er':
        return '展示系统的数据模型和关系';
      default:
        return '';
    }
  };

  const FallbackDisplay = ({ type }: { type: string }) => {
    const descriptions: Record<string, JSX.Element> = {
      overview: (
        <div className="space-y-4">
          <h3 className="text-xl font-semibold text-slate-100">系统架构概览</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-slate-800 p-4 rounded-lg">
              <h4 className="font-semibold text-blue-400 mb-2">前端层</h4>
              <p className="text-slate-300">React + TypeScript + Tailwind CSS</p>
            </div>
            <div className="bg-slate-800 p-4 rounded-lg">
              <h4 className="font-semibold text-cyan-400 mb-2">API网关层</h4>
              <p className="text-slate-300">FastAPI REST API + CORS</p>
            </div>
            <div className="bg-slate-800 p-4 rounded-lg">
              <h4 className="font-semibold text-green-400 mb-2">核心业务层</h4>
              <ul className="text-slate-300 text-sm space-y-1">
                <li>• 多租户服务</li>
                <li>• 服务网格</li>
                <li>• AI进化引擎</li>
                <li>• 记忆系统</li>
                <li>• 任务系统</li>
              </ul>
            </div>
            <div className="bg-slate-800 p-4 rounded-lg">
              <h4 className="font-semibold text-yellow-400 mb-2">基础设施层</h4>
              <ul className="text-slate-300 text-sm space-y-1">
                <li>• 数据库 (SQLite/PostgreSQL)</li>
                <li>• Redis 缓存</li>
                <li>• Prometheus 监控</li>
              </ul>
            </div>
          </div>
        </div>
      ),
      dataflow: (
        <div className="space-y-4">
          <h3 className="text-xl font-semibold text-slate-100">数据流处理流程</h3>
          <div className="bg-slate-800 p-4 rounded-lg">
            <ol className="list-decimal list-inside space-y-2 text-slate-300">
              <li>用户发送 HTTP 请求</li>
              <li>API 路由分发请求</li>
              <li>认证鉴权验证</li>
              <li>参数验证</li>
              <li>检查缓存</li>
              <li>缓存命中/未命中处理</li>
              <li>数据库操作（如需要）</li>
              <li>更新缓存</li>
              <li>数据转换</li>
              <li>返回响应</li>
              <li>前端渲染展示</li>
            </ol>
          </div>
        </div>
      ),
      sequence: (
        <div className="space-y-4">
          <h3 className="text-xl font-semibold text-slate-100">系统交互时序</h3>
          <div className="bg-slate-800 p-4 rounded-lg">
            <div className="space-y-2 text-slate-300">
              <p>1. 用户访问前端</p>
              <p>2. 前端请求 API</p>
              <p>3. API 网关验证认证</p>
              <p>4. 调用租户服务</p>
              <p>5. 查询数据库</p>
              <p>6. 返回 JSON 响应</p>
              <p>7. 前端渲染页面</p>
            </div>
          </div>
        </div>
      ),
      deployment: (
        <div className="space-y-4">
          <h3 className="text-xl font-semibold text-slate-100">部署架构</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-slate-800 p-4 rounded-lg">
              <h4 className="font-semibold text-blue-400 mb-2">Kubernetes 集群</h4>
              <ul className="text-slate-300 text-sm space-y-1">
                <li>• 前端 Pods</li>
                <li>• API Pods</li>
                <li>• Worker Pods</li>
                <li>• Ingress 负载均衡</li>
              </ul>
            </div>
            <div className="bg-slate-800 p-4 rounded-lg">
              <h4 className="font-semibold text-green-400 mb-2">数据与监控</h4>
              <ul className="text-slate-300 text-sm space-y-1">
                <li>• PostgreSQL HA</li>
                <li>• Redis Cluster</li>
                <li>• Prometheus</li>
                <li>• Grafana</li>
              </ul>
            </div>
          </div>
        </div>
      ),
      er: (
        <div className="space-y-4">
          <h3 className="text-xl font-semibold text-slate-100">数据模型</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="bg-slate-800 p-4 rounded-lg">
              <h4 className="font-semibold text-blue-400 mb-2">TENANT</h4>
              <p className="text-slate-300 text-sm">租户信息</p>
            </div>
            <div className="bg-slate-800 p-4 rounded-lg">
              <h4 className="font-semibold text-green-400 mb-2">SERVICE_INSTANCE</h4>
              <p className="text-slate-300 text-sm">服务实例</p>
            </div>
            <div className="bg-slate-800 p-4 rounded-lg">
              <h4 className="font-semibold text-yellow-400 mb-2">MEMORY</h4>
              <p className="text-slate-300 text-sm">记忆数据</p>
            </div>
            <div className="bg-slate-800 p-4 rounded-lg">
              <h4 className="font-semibold text-cyan-400 mb-2">TASK</h4>
              <p className="text-slate-300 text-sm">任务信息</p>
            </div>
            <div className="bg-slate-800 p-4 rounded-lg">
              <h4 className="font-semibold text-red-400 mb-2">TENANT_QUOTA</h4>
              <p className="text-slate-300 text-sm">租户配额</p>
            </div>
          </div>
        </div>
      ),
    };
    
    return descriptions[type] || null;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">系统架构</h1>
          <p className="mt-2 text-slate-600">可视化系统架构、数据流和设计</p>
        </div>
      </div>

      <div className="border-b border-slate-200">
        <nav className="flex space-x-8" aria-label="Tabs">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
              }`}
            >
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      <Card className="p-6">
        <div className="mb-4">
          <p className="text-slate-600">{getDescription()}</p>
        </div>
        <div className="bg-slate-900 rounded-lg p-4 border border-slate-700 min-h-[400px]">
          <MermaidDiagram chart={renderDiagram()} />
        </div>
        <div className="mt-4">
          <FallbackDisplay type={activeTab} />
        </div>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="p-4">
          <h3 className="text-lg font-semibold text-slate-900 mb-2">技术栈</h3>
          <ul className="space-y-2 text-slate-600 text-sm">
            <li>• React 18 + TypeScript</li>
            <li>• FastAPI + Python</li>
            <li>• Tailwind CSS</li>
            <li>• Vite 构建工具</li>
            <li>• Zustand 状态管理</li>
          </ul>
        </Card>

        <Card className="p-4">
          <h3 className="text-lg font-semibold text-slate-900 mb-2">核心模块</h3>
          <ul className="space-y-2 text-slate-600 text-sm">
            <li>• 多租户管理</li>
            <li>• 服务网格</li>
            <li>• AI 自进化引擎</li>
            <li>• 记忆系统</li>
            <li>• 监控系统</li>
          </ul>
        </Card>

        <Card className="p-4">
          <h3 className="text-lg font-semibold text-slate-900 mb-2">设计原则</h3>
          <ul className="space-y-2 text-slate-600 text-sm">
            <li>• 模块化架构</li>
            <li>• 高可用设计</li>
            <li>• 可扩展性</li>
            <li>• 安全性优先</li>
            <li>• 持续演进</li>
          </ul>
        </Card>
      </div>
    </div>
  );
};
