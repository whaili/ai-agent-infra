# E2B Agent 通信架构说明

## 🎯 核心问题

**Agents 之间如何传递数据？**

在 E2B 中，agents 之间的数据传递有两种模式：

## 📊 模式对比

### 模式 1: 外部协调器模式（当前示例使用）

```
┌─────────────┐
│ 协调程序     │ ← 这是你的 Python 测试脚本
└──────┬──────┘
       │
       ├─→ Sandbox 1 (Agent A) → 输出数据
       │        ↓
       │    读取结果
       │        ↓
       └─→ Sandbox 2 (Agent B) ← 输入数据
```

**数据流：**
```python
# Agent A 运行
sandbox1 = Sandbox.create()
result1 = sandbox1.commands.run("python3 agent_a.py")
data = json.loads(result1.stdout)  # 📍 协调程序提取数据
sandbox1.kill()

# Agent B 运行（接收 Agent A 的数据）
sandbox2 = Sandbox.create()
# 📍 协调程序注入数据
sandbox2.files.write("/tmp/input.json", json.dumps(data))
result2 = sandbox2.commands.run("python3 agent_b.py")
sandbox2.kill()
```

**特点：**
- ✅ **Agents 不需要网络互通**
- ✅ **E2B 基础设施不需要实现 sandbox 间通信**
- ✅ 协调程序充当"消息总线"
- ✅ 简单、安全、可控
- ❌ 需要外部程序协调
- ❌ 不是真正的"直接通信"

---

### 模式 2: 直接通信模式（需要网络）

```
┌──────────────┐          ┌──────────────┐
│  Sandbox 1   │  HTTP/   │  Sandbox 2   │
│  (Agent A)   │ ──TCP──→ │  (Agent B)   │
└──────────────┘          └──────────────┘
```

**需要的基础设施：**
1. Sandboxes 之间的网络互通
2. 某个 sandbox 运行 HTTP 服务器
3. 其他 sandbox 可以访问该服务器

**是否可行？**

理论上可以，但有限制：

#### 方式 A: 通过外部 URL（可行但间接）

```python
# Agent A: 启动 HTTP 服务
sandbox1 = Sandbox.create()
sandbox1.commands.run("python3 -m http.server 8000 &")

# 获取公网访问地址
url = sandbox1.get_host(8000)
# url = "https://xxx.e2b.dev:8000"

# Agent B: 通过公网 URL 访问 Agent A
sandbox2 = Sandbox.create()
script = f"""
import requests
data = requests.get('{url}/data.json').json()
print(data)
"""
sandbox2.files.write("/tmp/fetch.py", script)
result = sandbox2.commands.run("python3 /tmp/fetch.py")
```

**特点：**
- ✅ Agents "间接"通信
- ⚠️ 实际是通过 E2B 的边缘网络
- ⚠️ 不是直接的内网通信
- ⚠️ 有网络延迟

#### 方式 B: 直接内网通信（目前不支持）

```python
# 这种方式目前 E2B 不支持
sandbox1 = Sandbox.create()
sandbox2 = Sandbox.create()

# ❌ sandbox1 和 sandbox2 之间没有直接的网络路由
# ❌ 无法通过内网 IP 直接访问
```

**为什么不支持？**
- E2B sandboxes 是隔离的微虚拟机
- 出于安全考虑，sandboxes 之间网络隔离
- 每个 sandbox 独立的网络命名空间

---

## 🏗️ E2B 基础设施架构

### 当前架构（隔离模式）

```
┌─────────────────────────────────────────┐
│         E2B Cloud                       │
│                                         │
│  ┌──────────┐    ┌──────────┐         │
│  │Sandbox 1 │    │Sandbox 2 │         │
│  │(隔离)    │    │(隔离)    │         │
│  └────┬─────┘    └────┬─────┘         │
│       │               │                │
│       └───────┬───────┘                │
│               ↓                        │
│         边缘网络/代理                   │
└───────────────┼────────────────────────┘
                ↓
         你的协调程序
```

**网络策略：**
- Sandbox 1 ❌ 不能直接访问 Sandbox 2
- Sandbox 1 ✅ 可以访问外网
- Sandbox 1 ✅ 可以通过公网 URL 暴露服务
- 协调程序 ✅ 可以与所有 sandboxes 通信

### 如果要支持直接通信（假设）

```
┌─────────────────────────────────────────┐
│         E2B Cloud                       │
│                                         │
│  ┌──────────┐    ┌──────────┐         │
│  │Sandbox 1 │◄──►│Sandbox 2 │ 内网互通  │
│  │10.0.0.1  │    │10.0.0.2  │         │
│  └──────────┘    └──────────┘         │
│       ↑               ↑                │
│       └──── VPC ──────┘                │
└────────────────────────────────────────┘
```

**需要实现：**
- ❌ 内部 VPC 网络
- ❌ 服务发现机制
- ❌ 安全组策略
- ❌ 复杂的网络配置

**E2B 选择不实现的原因：**
1. **安全性** - 隔离是安全沙箱的基本要求
2. **简单性** - 避免复杂的网络配置
3. **实用性** - 外部协调器模式已经够用

---

## 💡 实际应用中的数据传递模式

### 单沙箱内（agents_collaboration.py）

```python
# 所有 agents 在同一个 sandbox
sandbox = Sandbox.create()

# Agent A 写入
sandbox.files.write("/tmp/shared/data.json", data)

# Agent B 读取（同一文件系统）
sandbox.commands.run("python3 agent_b.py")  # 读取 /tmp/shared/data.json

# ✅ 直接文件系统共享
# ✅ 无需网络通信
```

### 多沙箱间（multi_sandbox_agents.py）

```python
# 方式 1: 通过协调程序（当前使用）
sandbox1 = Sandbox.create()
result = sandbox1.commands.run("python3 agent_a.py")
data = result.stdout  # 协调程序中转

sandbox2 = Sandbox.create()
sandbox2.files.write("/tmp/input.txt", data)  # 协调程序注入

# 方式 2: 通过外部存储（如果需要）
# Agent A 上传到 S3/数据库
# Agent B 从 S3/数据库下载

# 方式 3: 通过公网 HTTP（间接）
# Agent A 启动 HTTP 服务
# Agent B 通过 sandbox.get_host() 获取的 URL 访问
```

---

## 🎯 结论

### 你的理解完全正确：

1. ✅ **数据通过测试程序（协调器）传递**
   - 不是 agents 之间直接通信
   - 协调程序充当"消息总线"

2. ✅ **E2B 基础设施不需要实现 sandbox 网络互通**
   - Sandboxes 之间是隔离的
   - 这是安全设计的一部分

3. ✅ **这是常见的 Multi-Agent 架构模式**
   - 称为"集中式协调"或"编排器模式"
   - 类似于 Kubernetes 的控制平面

### 架构对比

| 特性 | 外部协调器 | 直接通信 |
|------|-----------|---------|
| 实现难度 | 简单 | 复杂 |
| 安全性 | 高（隔离） | 低（需要网络） |
| E2B 支持 | ✅ 完全支持 | ❌ 不支持内网，✅ 支持公网 |
| 适用场景 | 大多数场景 | 实时交互需求 |
| 延迟 | 中等 | 低（如果内网） |

### 最佳实践

**对于大多数 AI Agent 应用：**

```python
# ✅ 推荐：外部协调器模式
class AgentOrchestrator:
    def __init__(self):
        self.sandbox = Sandbox.create()

    def run_agent_a(self, input_data):
        self.sandbox.files.write("/tmp/input.json", json.dumps(input_data))
        result = self.sandbox.commands.run("python3 agent_a.py")
        return json.loads(result.stdout)

    def run_agent_b(self, data_from_a):
        self.sandbox.files.write("/tmp/input.json", json.dumps(data_from_a))
        result = self.sandbox.commands.run("python3 agent_b.py")
        return json.loads(result.stdout)

    def execute_workflow(self):
        # 协调器控制数据流
        result_a = self.run_agent_a({"task": "analyze"})
        result_b = self.run_agent_b(result_a)
        return result_b
```

---

## 🌐 如果真的需要 Agents 直接通信

### 使用外部消息队列

```python
# 使用 Redis/RabbitMQ/Kafka 作为中间件

# Agent A (Sandbox 1)
import redis
r = redis.Redis(host='your-redis.com', port=6379)
r.set('task_result', json.dumps(data))

# Agent B (Sandbox 2)
import redis
r = redis.Redis(host='your-redis.com', port=6379)
data = json.loads(r.get('task_result'))
```

### 使用云存储

```python
# Agent A (Sandbox 1)
import boto3
s3 = boto3.client('s3')
s3.put_object(Bucket='agent-data', Key='task_result.json', Body=json.dumps(data))

# Agent B (Sandbox 2)
import boto3
s3 = boto3.client('s3')
obj = s3.get_object(Bucket='agent-data', Key='task_result.json')
data = json.loads(obj['Body'].read())
```

### 使用数据库

```python
# Agent A (Sandbox 1)
import psycopg2
conn = psycopg2.connect("dbname=agents user=agent")
cur = conn.cursor()
cur.execute("INSERT INTO results (data) VALUES (%s)", [json.dumps(data)])
conn.commit()

# Agent B (Sandbox 2)
import psycopg2
conn = psycopg2.connect("dbname=agents user=agent")
cur = conn.cursor()
cur.execute("SELECT data FROM results ORDER BY id DESC LIMIT 1")
data = json.loads(cur.fetchone()[0])
```

---

## 📚 总结

**E2B 的设计哲学：**

1. **安全优先** - Sandboxes 默认隔离
2. **简单实用** - 通过协调器模式已经够用
3. **灵活扩展** - 如需复杂通信，使用外部服务

**你的理解是正确的：**
- ✅ 数据不是在 agents 之间直接传递
- ✅ 总是通过外部程序（协调器）传递
- ✅ E2B 基础设施不需要实现 sandbox 网络互通
- ✅ 这是一个经过深思熟虑的设计选择

这种架构既保证了安全性，又提供了足够的灵活性来构建复杂的 Multi-Agent 系统！
