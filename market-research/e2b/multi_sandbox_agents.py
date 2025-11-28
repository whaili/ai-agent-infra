#!/usr/bin/env python3
"""
多沙箱 Agents 协作示例
演示多个独立沙箱中的 agents 如何协作

场景：
- 每个 agent 在独立的沙箱中运行（隔离性更强）
- 通过外部协调器传递数据
- 适合需要不同环境或安全隔离的场景
"""

from pathlib import Path
from dotenv import load_dotenv
from e2b import Sandbox
import json
import time

# 加载 API Key
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

print("=" * 60)
print("多沙箱 Agents 协作演示")
print("=" * 60)

# ============================================
# 场景 1: 数据处理流水线（每个阶段独立沙箱）
# ============================================
print("\n场景 1: 跨沙箱数据流水线")
print("=" * 60)

# Stage 1: 数据生成器 Agent
print("\n📊 Stage 1: 数据生成器")
sandbox1 = Sandbox.create()
print(f"   沙箱 1 ID: {sandbox1.sandbox_id[:8]}...")

generate_script = """
import json
import random

# 生成模拟数据
data = {
    'sensor_readings': [random.randint(20, 30) for _ in range(10)],
    'timestamp': '2025-01-01T00:00:00Z',
    'sensor_id': 'SENSOR_001'
}

# 输出 JSON 供外部程序使用
print(json.dumps(data))
"""

sandbox1.files.write("/tmp/generate.py", generate_script)
result1 = sandbox1.commands.run("python3 /tmp/generate.py")
stage1_data = json.loads(result1.stdout)

print(f"✅ 生成数据: {stage1_data}")

# 清理沙箱1
sandbox1.kill()
print("   沙箱 1 已清理")

# Stage 2: 数据处理器 Agent
print("\n🔄 Stage 2: 数据处理器")
sandbox2 = Sandbox.create()
print(f"   沙箱 2 ID: {sandbox2.sandbox_id[:8]}...")

# 将 stage1 的数据传入 stage2
process_script = f"""
import json

# 从外部接收数据
input_data = {json.dumps(stage1_data)}

# 处理数据：计算统计信息
readings = input_data['sensor_readings']
processed = {{
    'sensor_id': input_data['sensor_id'],
    'avg_temp': sum(readings) / len(readings),
    'max_temp': max(readings),
    'min_temp': min(readings),
    'sample_count': len(readings)
}}

print(json.dumps(processed))
"""

sandbox2.files.write("/tmp/process.py", process_script)
result2 = sandbox2.commands.run("python3 /tmp/process.py")
stage2_data = json.loads(result2.stdout)

print(f"✅ 处理结果: {stage2_data}")

# 清理沙箱2
sandbox2.kill()
print("   沙箱 2 已清理")

# Stage 3: 报告生成器 Agent
print("\n📝 Stage 3: 报告生成器")
sandbox3 = Sandbox.create()
print(f"   沙箱 3 ID: {sandbox3.sandbox_id[:8]}...")

report_script = f"""
import json

# 从外部接收处理后的数据
stats = {json.dumps(stage2_data)}

# 生成报告
report = f'''
传感器报告
{'=' * 40}
传感器 ID: {{stats['sensor_id']}}
样本数量: {{stats['sample_count']}}
平均温度: {{stats['avg_temp']:.2f}}°C
最高温度: {{stats['max_temp']}}°C
最低温度: {{stats['min_temp']}}°C
'''

print(report)
"""

sandbox3.files.write("/tmp/report.py", report_script)
result3 = sandbox3.commands.run("python3 /tmp/report.py")

print(f"✅ 最终报告:\n{result3.stdout}")

# 清理沙箱3
sandbox3.kill()
print("   沙箱 3 已清理")

# ============================================
# 场景 2: 并行任务处理
# ============================================
print("\n" + "=" * 60)
print("场景 2: 并行 Agents 处理（多沙箱）")
print("=" * 60)

# 准备任务列表
tasks = [
    {"task_id": 1, "operation": "sum", "data": [1, 2, 3, 4, 5]},
    {"task_id": 2, "operation": "product", "data": [2, 3, 4]},
    {"task_id": 3, "operation": "average", "data": [10, 20, 30, 40]}
]

# 为每个任务创建独立沙箱
sandboxes = []
results = []

print(f"\n🚀 启动 {len(tasks)} 个并行 Agents...")

for i, task in enumerate(tasks, 1):
    print(f"\n🤖 Agent {i}: {task['operation']}")

    # 创建沙箱
    sb = Sandbox.create()
    sandboxes.append(sb)
    print(f"   沙箱 ID: {sb.sandbox_id[:8]}...")

    # 创建任务脚本
    task_script = f"""
import json

task = {json.dumps(task)}
data = task['data']
operation = task['operation']

if operation == 'sum':
    result = sum(data)
elif operation == 'product':
    result = 1
    for x in data:
        result *= x
elif operation == 'average':
    result = sum(data) / len(data)
else:
    result = None

output = {{
    'task_id': task['task_id'],
    'operation': operation,
    'result': result
}}

print(json.dumps(output))
"""

    # 执行任务
    sb.files.write(f"/tmp/task_{i}.py", task_script)
    result = sb.commands.run(f"python3 /tmp/task_{i}.py")

    task_result = json.loads(result.stdout)
    results.append(task_result)
    print(f"   ✅ 结果: {task_result['result']}")

# 汇总结果
print("\n📊 汇总所有 Agent 结果:")
for r in results:
    print(f"   Task {r['task_id']} ({r['operation']}): {r['result']}")

# 清理所有沙箱
print("\n🧹 清理所有沙箱...")
for i, sb in enumerate(sandboxes, 1):
    sb.kill()
    print(f"   ✅ 沙箱 {i} 已清理")

# ============================================
# 场景 3: Master-Worker 模式
# ============================================
print("\n" + "=" * 60)
print("场景 3: Master-Worker 模式")
print("=" * 60)

# Master Agent
print("\n👑 Master Agent: 任务调度器")
master_sandbox = Sandbox.create()
print(f"   Master 沙箱 ID: {master_sandbox.sandbox_id[:8]}...")

# Master 生成任务
master_script = """
import json

# 生成任务列表
tasks = []
for i in range(5):
    tasks.append({
        'worker_id': i + 1,
        'task': f'process_batch_{i + 1}',
        'data_range': [i * 10, (i + 1) * 10]
    })

# 输出任务
for task in tasks:
    print(json.dumps(task))
"""

master_sandbox.files.write("/tmp/master.py", master_script)
result = master_sandbox.commands.run("python3 /tmp/master.py")

# 解析任务
worker_tasks = [json.loads(line) for line in result.stdout.strip().split('\n')]
print(f"✅ Master 生成了 {len(worker_tasks)} 个任务")

master_sandbox.kill()

# Worker Agents
print("\n👷 Worker Agents: 执行任务")
worker_results = []

for task in worker_tasks[:3]:  # 只执行前3个，节省资源
    print(f"\n   Worker {task['worker_id']}: {task['task']}")

    # 创建 worker 沙箱
    worker_sb = Sandbox.create()

    worker_script = f"""
import json

task = {json.dumps(task)}
start, end = task['data_range']

# 模拟处理
result = {{
    'worker_id': task['worker_id'],
    'task': task['task'],
    'processed_count': end - start,
    'status': 'completed'
}}

print(json.dumps(result))
"""

    worker_sb.files.write("/tmp/worker.py", worker_script)
    result = worker_sb.commands.run("python3 /tmp/worker.py")

    worker_result = json.loads(result.stdout)
    worker_results.append(worker_result)
    print(f"      ✅ 处理了 {worker_result['processed_count']} 条记录")

    worker_sb.kill()

# 汇总 Worker 结果
print("\n📊 所有 Workers 完成:")
total_processed = sum(r['processed_count'] for r in worker_results)
print(f"   总共处理: {total_processed} 条记录")

# ============================================
# 场景 4: 使用外部存储协调（模拟）
# ============================================
print("\n" + "=" * 60)
print("场景 4: 通过外部协调器共享状态")
print("=" * 60)

# 模拟外部状态存储
external_state = {
    "jobs": ["job_a", "job_b", "job_c"],
    "results": {}
}

print(f"\n📦 初始状态: {len(external_state['jobs'])} 个待处理任务")

# Agent 1 处理
print("\n🤖 Agent 1 处理")
agent1_sb = Sandbox.create()

job = external_state['jobs'].pop(0)
script1 = f"""
job = '{job}'
result = f"Agent 1 processed {{job}}"
print(result)
"""

agent1_sb.files.write("/tmp/agent.py", script1)
result = agent1_sb.commands.run("python3 /tmp/agent.py")
external_state['results']['agent_1'] = result.stdout.strip()
print(f"   ✅ {result.stdout.strip()}")
agent1_sb.kill()

# Agent 2 处理
print("\n🤖 Agent 2 处理")
agent2_sb = Sandbox.create()

job = external_state['jobs'].pop(0)
script2 = f"""
job = '{job}'
result = f"Agent 2 processed {{job}}"
print(result)
"""

agent2_sb.files.write("/tmp/agent.py", script2)
result = agent2_sb.commands.run("python3 /tmp/agent.py")
external_state['results']['agent_2'] = result.stdout.strip()
print(f"   ✅ {result.stdout.strip()}")
agent2_sb.kill()

# 最终状态
print(f"\n📊 最终状态:")
print(f"   剩余任务: {external_state['jobs']}")
print(f"   完成任务: {list(external_state['results'].values())}")

# ============================================
# 总结
# ============================================
print("\n" + "=" * 60)
print("✅ 演示完成！")
print("=" * 60)

print("\n💡 Multi-Sandbox Agents 协作模式:")
print("   1. 流水线模式 - 数据在沙箱间传递，每阶段独立运行")
print("   2. 并行处理 - 多个沙箱同时处理不同任务")
print("   3. Master-Worker - 主控调度，工作器执行")
print("   4. 外部协调 - 通过外部状态管理器协调多沙箱")

print("\n🔐 优势:")
print("   - 更强的隔离性（每个 agent 独立环境）")
print("   - 安全性（一个沙箱故障不影响其他）")
print("   - 可扩展性（可以动态创建/销毁沙箱）")
print("   - 并行性（真正的并行执行）")

print("\n⚠️  注意:")
print("   - 每个沙箱都需要资源和费用")
print("   - 创建沙箱有时间开销（约2秒）")
print("   - 需要外部协调机制传递数据")
