# Agent 永续自进化运行系统 - 运维手册

## 快速开始

### Docker Compose 开发环境

```bash
# 启动开发环境
docker-compose -f docker-compose.dev.yml up -d

# 查看日志
docker-compose -f docker-compose.dev.yml logs -f

# 停止
docker-compose -f docker-compose.dev.yml down
```

### Docker Compose 生产环境

```bash
# 启动生产环境
docker-compose -f docker-compose.prod.yml up -d

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f

# 停止
docker-compose -f docker-compose.prod.yml down
```

### Kubernetes 部署

```bash
# 应用所有配置
kubectl apply -f k8s/

# 查看 Pod 状态
kubectl get pods -n agent-evolution-system

# 查看服务
kubectl get svc -n agent-evolution-system

# 查看日志
kubectl logs -f deployment/agent-evolution-api -n agent-evolution-system
```

## 监控与告警

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

## 备份与恢复

### 数据库备份

```bash
# PostgreSQL 备份
kubectl exec -it <postgres-pod> -n agent-evolution-system -- pg_dump -U agent_user agent_db > backup.sql

# 恢复
kubectl exec -i <postgres-pod> -n agent-evolution-system -- psql -U agent_user agent_db < backup.sql
```

## 故障排除

### 常见问题

1. **Pod 无法启动** - 检查事件和日志
2. **健康检查失败** - 验证依赖服务
3. **性能问题** - 查看 Prometheus 指标
4. **网络问题** - 检查 Service 和 Ingress 配置
