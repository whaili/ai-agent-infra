# E2B Agents 协作模式指南

## 概述

本文档介绍如何使用 E2B 实现多个 AI Agents 之间的数据交互和协作。

## 📚 示例文件

- [agents_collaboration.py](agents_collaboration.py) - 单沙箱内多 agents 协作
- [multi_sandbox_agents.py](multi_sandbox_agents.py) - 多沙箱间 agents 协作

## 🎯 协作模式

### 1. 单沙箱协作模式

多个 agents 在同一个沙箱中运行，通过文件系统共享数据。

**适用场景：**
- Agents 需要共享环境
- 低延迟数据交换
- 资源节约

**示例：**

```python
from e2b import Sandbox

# 创建共享沙箱
sandbox = Sandbox.create()

# Agent 1: 生成数据
sandbox.files.write("/tmp/shared/data.json", json.dumps(data))

# Agent 2: 处理数据
result = sandbox.commands.run("python3 /tmp/shared/process.py")

# Agent 3: 生成报告
result = sandbox.commands.run("python3 /tmp/shared/report.py")

sandbox.kill()
```

### 2. 多沙箱协作模式

每个 agent 在独立沙箱中运行，通过外部协调器传递数据。

**适用场景：**
- 需要强隔离性
- 不同 agents 需要不同环境
- 安全性要求高

**示例：**

```python
# Agent 1 在沙箱 1
sandbox1 = Sandbox.create()
result1 = sandbox1.commands.run("python3 generate.py")
data = json.loads(result1.stdout)
sandbox1.kill()

# Agent 2 在沙箱 2（接收 Agent 1 的数据）
sandbox2 = Sandbox.create()
sandbox2.files.write("/tmp/input.json", json.dumps(data))
result2 = sandbox2.commands.run("python3 process.py")
sandbox2.kill()
```

## 🔄 协作模式详解

### 模式 1: 文件系统共享

**原理：** Agents 通过读写共享文件系统位置来交换数据。

**实现：**

```python
# Agent A 写入数据
sandbox.files.write("/tmp/shared/data.json", json.dumps({
    "message": "Hello from Agent A"
}))

# Agent B 读取并处理
script = """
import json

with open('/tmp/shared/data.json', 'r') as f:
    data = json.load(f)

# 处理数据
result = {'processed': data['message'].upper()}

with open('/tmp/shared/result.json', 'w') as f:
    json.dump(result, f)

print('Done')
"""

sandbox.files.write("/tmp/agent_b.py", script)
sandbox.commands.run("python3 /tmp/agent_b.py")
```

**优点：**
- ✅ 简单直观
- ✅ 低延迟
- ✅ 支持大数据传输

**缺点：**
- ❌ 需要文件命名规范
- ❌ 并发访问需要同步机制

### 模式 2: 流水线处理（Pipeline）

**原理：** 数据按顺序经过多个处理阶段。

```
Data → Agent 1 → Agent 2 → Agent 3 → Result
```

**实现：**

```python
# Stage 1: 清洗
sandbox.commands.run("python3 /tmp/stage1_clean.py")
# 输出: /tmp/stage1_output.json

# Stage 2: 转换（读取 stage1 输出）
sandbox.commands.run("python3 /tmp/stage2_transform.py")
# 输出: /tmp/stage2_output.json

# Stage 3: 聚合（读取 stage2 输出）
sandbox.commands.run("python3 /tmp/stage3_aggregate.py")
# 输出: /tmp/final_result.json
```

**优点：**
- ✅ 清晰的数据流
- ✅ 易于调试
- ✅ 可以单独测试每个阶段

**适用场景：**
- 数据处理流程
- ETL (Extract, Transform, Load)
- 多步骤分析

### 模式 3: 并行协作

**原理：** 多个 agents 同时处理不同任务，最后汇总结果。

```
           ┌─ Agent A ─┐
Input ─────┼─ Agent B ─┼─→ Coordinator → Result
           └─ Agent C ─┘
```

**实现：**

```python
# 创建输入数据
sandbox.files.write("/tmp/parallel/input.json", json.dumps(data))

# 并行执行 Agent A 和 Agent B
sandbox.commands.run("python3 /tmp/agent_a.py")  # 输出到 agent_a_result.json
sandbox.commands.run("python3 /tmp/agent_b.py")  # 输出到 agent_b_result.json

# Coordinator 汇总结果
sandbox.commands.run("python3 /tmp/coordinator.py")
```

**优点：**
- ✅ 提高吞吐量
- ✅ 充分利用资源
- ✅ 可扩展

**适用场景：**
- 批量任务处理
- 独立的子任务
- 需要高性能的场景

### 模式 4: Master-Worker

**原理：** Master 负责任务调度，Workers 执行具体任务。

```
Master → Task Queue → [Worker 1, Worker 2, Worker 3, ...]
```

**实现：**

**使用单沙箱：**

```python
# Master 创建任务队列
state = {
    "tasks": ["task1", "task2", "task3"],
    "results": []
}
sandbox.files.write("/tmp/state.json", json.dumps(state))

# Workers 处理任务
for i in range(3):
    # 每个 worker 从队列取任务并处理
    sandbox.commands.run(f"python3 /tmp/worker.py")
```

**使用多沙箱（真正并行）：**

```python
# Master 生成任务
tasks = ["task1", "task2", "task3"]

# 创建多个 worker 沙箱
workers = [Sandbox.create() for _ in range(3)]

results = []
for worker, task in zip(workers, tasks):
    # 分配任务
    worker.files.write("/tmp/task.json", json.dumps(task))
    result = worker.commands.run("python3 /tmp/worker.py")
    results.append(json.loads(result.stdout))

# 清理
for worker in workers:
    worker.kill()
```

**优点：**
- ✅ 动态任务分配
- ✅ 负载均衡
- ✅ 可扩展

**适用场景：**
- 大量小任务
- 动态任务生成
- 需要负载均衡

### 模式 5: 状态共享与同步

**原理：** 使用共享状态文件协调多个 agents。

**实现：**

```python
# 初始化共享状态
state = {
    "task_queue": ["task1", "task2", "task3"],
    "completed": [],
    "agent_status": {}
}
sandbox.files.write("/tmp/shared_state.json", json.dumps(state))

# Agent 脚本模板
agent_script = """
import json

# 读取共享状态
with open('/tmp/shared_state.json', 'r') as f:
    state = json.load(f)

# 获取任务
if state['task_queue']:
    task = state['task_queue'].pop(0)

    # 处理任务
    result = f"Completed: {task}"
    state['completed'].append(result)

    # 更新状态
    with open('/tmp/shared_state.json', 'w') as f:
        json.dump(state, f)

    print(result)
"""
```

**注意事项：**
- ⚠️ 需要处理并发访问（如果是真正并行）
- ⚠️ 可能需要锁机制
- ⚠️ 单沙箱内串行执行不会有并发问题

## 📊 数据交换格式

### JSON（推荐）

```python
# 写入
data = {"key": "value", "numbers": [1, 2, 3]}
sandbox.files.write("/tmp/data.json", json.dumps(data, indent=2))

# 读取
content = sandbox.files.read("/tmp/data.json")
data = json.loads(content)
```

### CSV

```python
# 写入 CSV
csv_data = "name,age\nAlice,30\nBob,25"
sandbox.files.write("/tmp/data.csv", csv_data)

# 读取并处理
script = """
import csv

with open('/tmp/data.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(row)
"""
```

### 二进制数据

```python
# 写入二进制
with open("local_file.bin", "rb") as f:
    binary_data = f.read()

sandbox.files.write("/tmp/data.bin", binary_data)
```

## 🔐 最佳实践

### 1. 文件命名规范

```python
# 使用清晰的命名
/tmp/shared/raw_data.json          # 原始数据
/tmp/shared/cleaned_data.json      # 清洗后数据
/tmp/shared/analysis_result.json   # 分析结果

# 使用阶段标识
/tmp/pipeline/stage1_output.json
/tmp/pipeline/stage2_output.json

# 使用 agent 标识
/tmp/parallel/agent_a_result.json
/tmp/parallel/agent_b_result.json
```

### 2. 错误处理

```python
# Agent 脚本中包含错误处理
script = """
import json
import sys

try:
    # 处理逻辑
    with open('/tmp/input.json', 'r') as f:
        data = json.load(f)

    result = process(data)

    with open('/tmp/output.json', 'w') as f:
        json.dump({'status': 'success', 'data': result}, f)

except Exception as e:
    # 记录错误
    with open('/tmp/output.json', 'w') as f:
        json.dump({'status': 'error', 'error': str(e)}, f)
    sys.exit(1)
"""
```

### 3. 资源管理

```python
# 单沙箱模式
sandbox = Sandbox.create()
try:
    # 使用沙箱
    pass
finally:
    sandbox.kill()  # 确保清理

# 多沙箱模式
sandboxes = []
try:
    # 创建和使用多个沙箱
    sandboxes = [Sandbox.create() for _ in range(3)]
    # ...
finally:
    # 清理所有沙箱
    for sb in sandboxes:
        sb.kill()
```

### 4. 日志和调试

```python
# 在 agent 脚本中添加日志
script = """
import json
import sys

# 写入日志
def log(message):
    with open('/tmp/agent_log.txt', 'a') as f:
        f.write(f"{message}\\n")

log("Agent started")

try:
    # 处理逻辑
    log("Processing data...")
    result = process_data()
    log("Processing complete")

except Exception as e:
    log(f"Error: {e}")
    raise
"""
```

## 🚀 运行示例

### 单沙箱协作

```bash
cd /Users/haili/src/ai-infra/e2b
python3 agents_collaboration.py
```

**演示内容：**
1. ✅ 文件系统数据共享
2. ✅ 流水线处理
3. ✅ 并行任务协作
4. ✅ 状态同步

### 多沙箱协作

```bash
cd /Users/haili/src/ai-infra/e2b
python3 multi_sandbox_agents.py
```

**演示内容：**
1. ✅ 跨沙箱数据传递
2. ✅ 并行沙箱处理
3. ✅ Master-Worker 模式
4. ✅ 外部协调器

## 📈 性能考虑

### 单沙箱 vs 多沙箱

| 特性 | 单沙箱 | 多沙箱 |
|------|--------|--------|
| 隔离性 | 弱（共享环境） | 强（独立环境） |
| 性能 | 高（无创建开销） | 低（需创建沙箱） |
| 费用 | 低（一个沙箱） | 高（多个沙箱） |
| 并行性 | 串行执行 | 真正并行 |
| 适用场景 | 简单协作 | 复杂/安全需求 |

### 优化建议

1. **复用沙箱** - 对于连续任务，复用同一个沙箱
2. **批量处理** - 合并小任务减少沙箱创建次数
3. **异步执行** - 使用 AsyncSandbox 实现真正的并行

```python
# 异步示例
from e2b import AsyncSandbox
import asyncio

async def process_task(task):
    sandbox = await AsyncSandbox.create()
    try:
        result = await sandbox.commands.run(f"python3 /tmp/task.py")
        return result
    finally:
        await sandbox.kill()

# 并行处理多个任务
tasks = [process_task(t) for t in task_list]
results = await asyncio.gather(*tasks)
```

## 🔗 参考资源

- [API-REFERENCE.md](API-REFERENCE.md) - E2B SDK API 参考
- [example.py](example.py) - 基础示例
- [test_e2b.py](test_e2b.py) - 测试脚本

## 💡 使用提示

1. **选择合适的协作模式** - 根据需求选择单沙箱或多沙箱
2. **定义清晰的数据格式** - 使用 JSON 作为标准交换格式
3. **添加错误处理** - 每个 agent 都应该有健壮的错误处理
4. **监控资源使用** - 注意沙箱数量和运行时间
5. **测试各个环节** - 单独测试每个 agent 后再组合

## ⚠️ 注意事项

1. **文件系统隔离** - 多个沙箱之间文件系统是隔离的
2. **状态持久化** - 沙箱销毁后数据会丢失，需要及时提取结果
3. **并发控制** - 单沙箱内的文件操作是串行的，不需要锁
4. **资源限制** - 注意 E2B 的并发沙箱数量限制
5. **费用控制** - 每个沙箱都会计费，记得及时清理
