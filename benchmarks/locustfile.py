# Agent 永续自进化运行系统 - 性能基准测试
from locust import HttpUser, task, between, constant
import random
import json

class AgentSystemUser(HttpUser):
    wait_time = between(0.5, 2.0)

    def on_start(self):
        self.client.headers.update({
            "Content-Type": "application/json",
        })

    @task(10)
    def health_check(self):
        self.client.get("/health")

    @task(8)
    def get_metrics(self):
        self.client.get("/metrics")

    @task(6)
    def create_agent(self):
        agent_data = {
            "name": f"test-agent-{random.randint(1, 1000)}",
            "type": "evolution",
            "config": {"learning_rate": 0.01, "population_size": 100}
        }
        self.client.post("/api/v1/agents", json=agent_data)

    @task(4)
    def list_agents(self):
        self.client.get("/api/v1/agents")

    @task(2)
    def trigger_evolution(self):
        self.client.post("/api/v1/evolution/trigger")
