#!/usr/bin/env python3
"""
E2B Agents 协作示例
演示多个 agents 如何在沙箱中交互和共享数据

场景：
1. 数据分析师 Agent - 处理和分析数据
2. 可视化 Agent - 生成图表
3. 报告生成 Agent - 创建最终报告
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
print("E2B Agents 协作演示")
print("=" * 60)

# 创建共享的沙箱环境
print("\n🚀 创建共享沙箱环境...")
sandbox = Sandbox.create()
print(f"✅ 沙箱 ID: {sandbox.sandbox_id}")

try:
    # ============================================
    # 场景 1: 通过文件系统共享数据
    # ============================================
    print("\n" + "=" * 60)
    print("场景 1: Agent 通过文件系统共享数据")
    print("=" * 60)

    # Agent 1: 数据采集
    print("\n📊 Agent 1: 数据采集")
    raw_data = {
        "sales": [100, 150, 200, 180, 220],
        "months": ["Jan", "Feb", "Mar", "Apr", "May"],
        "product": "Widget A"
    }

    # 将数据写入共享位置
    sandbox.files.write(
        "/tmp/shared/raw_data.json",
        json.dumps(raw_data, indent=2)
    )
    print(f"✅ 数据已保存到: /tmp/shared/raw_data.json")
    print(f"   数据: {raw_data}")

    # Agent 2: 数据分析
    print("\n🔍 Agent 2: 数据分析")
    analysis_script = """
import json

# 读取 Agent 1 的数据
with open('/tmp/shared/raw_data.json', 'r') as f:
    data = json.load(f)

# 执行分析
sales = data['sales']
analysis = {
    'total_sales': sum(sales),
    'average_sales': sum(sales) / len(sales),
    'max_sales': max(sales),
    'min_sales': min(sales),
    'product': data['product']
}

# 保存分析结果供其他 agents 使用
with open('/tmp/shared/analysis_result.json', 'w') as f:
    json.dump(analysis, f, indent=2)

print('分析完成！')
print(json.dumps(analysis, indent=2))
"""

    sandbox.files.write("/tmp/shared/analyze.py", analysis_script)
    result = sandbox.commands.run("python3 /tmp/shared/analyze.py")
    print(f"✅ 分析结果:\n{result.stdout}")

    # Agent 3: 报告生成
    print("\n📝 Agent 3: 报告生成")
    report_script = """
import json

# 读取原始数据和分析结果
with open('/tmp/shared/raw_data.json', 'r') as f:
    raw_data = json.load(f)

with open('/tmp/shared/analysis_result.json', 'r') as f:
    analysis = json.load(f)

# 生成报告
report = f'''
销售报告 - {analysis['product']}
{'=' * 40}

总销售额: ${analysis['total_sales']}
平均销售额: ${analysis['average_sales']:.2f}
最高销售额: ${analysis['max_sales']}
最低销售额: ${analysis['min_sales']}

月度明细:
'''

for month, sale in zip(raw_data['months'], raw_data['sales']):
    report += f"  {month}: ${sale}\\n"

# 保存报告
with open('/tmp/shared/final_report.txt', 'w') as f:
    f.write(report)

print(report)
"""

    sandbox.files.write("/tmp/shared/generate_report.py", report_script)
    result = sandbox.commands.run("python3 /tmp/shared/generate_report.py")
    print(f"✅ 最终报告:\n{result.stdout}")

    # ============================================
    # 场景 2: 流水线处理（Pipeline）
    # ============================================
    print("\n" + "=" * 60)
    print("场景 2: Agent 流水线处理")
    print("=" * 60)

    # Pipeline Stage 1: 数据清洗
    print("\n🧹 Stage 1: 数据清洗 Agent")
    cleaning_script = """
import json

# 模拟含有噪声的数据
raw_data = [100, 150, -1, 200, None, 180, 220, 999999]

# 清洗数据
cleaned_data = [x for x in raw_data if x is not None and 0 < x < 1000]

result = {
    'stage': 'cleaning',
    'input_count': len(raw_data),
    'output_count': len(cleaned_data),
    'data': cleaned_data
}

with open('/tmp/pipeline/stage1_output.json', 'w') as f:
    json.dump(result, f)

print(f'清洗完成: {len(raw_data)} -> {len(cleaned_data)} 条记录')
"""

    sandbox.files.write("/tmp/pipeline/stage1_clean.py", cleaning_script)
    result = sandbox.commands.run("python3 /tmp/pipeline/stage1_clean.py")
    print(f"✅ {result.stdout}")

    # Pipeline Stage 2: 数据转换
    print("\n🔄 Stage 2: 数据转换 Agent")
    transform_script = """
import json

# 读取上一阶段的输出
with open('/tmp/pipeline/stage1_output.json', 'r') as f:
    stage1 = json.load(f)

# 转换数据（例如：标准化）
data = stage1['data']
mean = sum(data) / len(data)
std = (sum((x - mean) ** 2 for x in data) / len(data)) ** 0.5

normalized_data = [(x - mean) / std for x in data]

result = {
    'stage': 'transform',
    'mean': mean,
    'std': std,
    'normalized_data': normalized_data
}

with open('/tmp/pipeline/stage2_output.json', 'w') as f:
    json.dump(result, f)

print(f'转换完成: mean={mean:.2f}, std={std:.2f}')
"""

    sandbox.files.write("/tmp/pipeline/stage2_transform.py", transform_script)
    result = sandbox.commands.run("python3 /tmp/pipeline/stage2_transform.py")
    print(f"✅ {result.stdout}")

    # Pipeline Stage 3: 结果聚合
    print("\n📊 Stage 3: 结果聚合 Agent")
    aggregate_script = """
import json

# 读取所有阶段的输出
with open('/tmp/pipeline/stage1_output.json', 'r') as f:
    stage1 = json.load(f)

with open('/tmp/pipeline/stage2_output.json', 'r') as f:
    stage2 = json.load(f)

# 聚合结果
final_result = {
    'pipeline_summary': {
        'stage1_cleaning': f"{stage1['input_count']} -> {stage1['output_count']} records",
        'stage2_transform': f"mean={stage2['mean']:.2f}, std={stage2['std']:.2f}",
    },
    'final_data': stage2['normalized_data']
}

with open('/tmp/pipeline/final_result.json', 'w') as f:
    json.dump(final_result, f, indent=2)

print('Pipeline 完成！')
print(json.dumps(final_result, indent=2))
"""

    sandbox.files.write("/tmp/pipeline/stage3_aggregate.py", aggregate_script)
    result = sandbox.commands.run("python3 /tmp/pipeline/stage3_aggregate.py")
    print(f"✅ {result.stdout}")

    # ============================================
    # 场景 3: 并行 Agents 处理
    # ============================================
    print("\n" + "=" * 60)
    print("场景 3: 并行 Agents 协作")
    print("=" * 60)

    # 创建共享输入数据
    shared_input = {
        "text": "E2B provides secure sandboxed environments for AI agents",
        "numbers": [1, 2, 3, 4, 5]
    }
    sandbox.files.write("/tmp/parallel/input.json", json.dumps(shared_input))

    # Agent A: 文本处理
    print("\n📝 Agent A: 文本分析")
    text_agent = """
import json

with open('/tmp/parallel/input.json', 'r') as f:
    data = json.load(f)

text = data['text']
result = {
    'agent': 'text_processor',
    'word_count': len(text.split()),
    'char_count': len(text),
    'uppercase': text.upper()
}

with open('/tmp/parallel/agent_a_result.json', 'w') as f:
    json.dump(result, f, indent=2)

print(f"文本处理完成: {result['word_count']} words")
"""

    sandbox.files.write("/tmp/parallel/agent_a.py", text_agent)
    result = sandbox.commands.run("python3 /tmp/parallel/agent_a.py")
    print(f"✅ {result.stdout}")

    # Agent B: 数值处理
    print("\n🔢 Agent B: 数值计算")
    number_agent = """
import json

with open('/tmp/parallel/input.json', 'r') as f:
    data = json.load(f)

numbers = data['numbers']
result = {
    'agent': 'number_processor',
    'sum': sum(numbers),
    'average': sum(numbers) / len(numbers),
    'squared': [x**2 for x in numbers]
}

with open('/tmp/parallel/agent_b_result.json', 'w') as f:
    json.dump(result, f, indent=2)

print(f"数值处理完成: sum={result['sum']}")
"""

    sandbox.files.write("/tmp/parallel/agent_b.py", number_agent)
    result = sandbox.commands.run("python3 /tmp/parallel/agent_b.py")
    print(f"✅ {result.stdout}")

    # Coordinator Agent: 整合结果
    print("\n🎯 Coordinator Agent: 整合所有结果")
    coordinator = """
import json

# 读取所有 agent 的结果
with open('/tmp/parallel/agent_a_result.json', 'r') as f:
    agent_a = json.load(f)

with open('/tmp/parallel/agent_b_result.json', 'r') as f:
    agent_b = json.load(f)

# 整合结果
combined = {
    'agents_completed': ['text_processor', 'number_processor'],
    'results': {
        'text_analysis': agent_a,
        'number_analysis': agent_b
    },
    'summary': f"处理了 {agent_a['word_count']} 个单词和 {agent_b['sum']} 的数字总和"
}

print('所有 Agents 协作完成！')
print(json.dumps(combined, indent=2))
"""

    sandbox.files.write("/tmp/parallel/coordinator.py", coordinator)
    result = sandbox.commands.run("python3 /tmp/parallel/coordinator.py")
    print(f"✅ {result.stdout}")

    # ============================================
    # 场景 4: 状态共享与同步
    # ============================================
    print("\n" + "=" * 60)
    print("场景 4: Agent 状态共享")
    print("=" * 60)

    # 使用锁文件和状态文件进行协调
    print("\n🔄 初始化共享状态")
    initial_state = {
        "task_queue": ["task1", "task2", "task3", "task4"],
        "completed_tasks": [],
        "agents_status": {}
    }
    sandbox.files.write("/tmp/state/shared_state.json", json.dumps(initial_state, indent=2))

    # 模拟多个 agent 处理任务
    for i in range(1, 4):
        agent_id = f"Agent_{i}"
        print(f"\n🤖 {agent_id} 处理任务")

        # Agent 工作器脚本
        worker_script = f"""
import json

agent_id = '{agent_id}'

# 读取共享状态
with open('/tmp/state/shared_state.json', 'r') as f:
    state = json.load(f)

# 从队列中获取任务
if state['task_queue']:
    task = state['task_queue'].pop(0)

    # 执行任务（模拟）
    result = agent_id + " completed " + task
    state['completed_tasks'].append(result)
    state['agents_status'][agent_id] = 'completed'

    # 更新状态
    with open('/tmp/state/shared_state.json', 'w') as f:
        json.dump(state, f, indent=2)

    print(agent_id + ': ' + result)
else:
    print(agent_id + ': No tasks available')
"""

        script = worker_script
        sandbox.files.write(f"/tmp/state/worker_{i}.py", script)
        result = sandbox.commands.run(f"python3 /tmp/state/worker_{i}.py")
        print(f"   {result.stdout.strip()}")

    # 查看最终状态
    print("\n📊 查看最终共享状态")
    final_state = sandbox.files.read("/tmp/state/shared_state.json")
    print(f"✅ 最终状态:\n{final_state}")

    # ============================================
    # 查看所有共享文件
    # ============================================
    print("\n" + "=" * 60)
    print("📁 共享文件系统概览")
    print("=" * 60)

    for directory in ["/tmp/shared", "/tmp/pipeline", "/tmp/parallel", "/tmp/state"]:
        result = sandbox.commands.run(f"find {directory} -type f 2>/dev/null || echo 'Directory not found'")
        if result.stdout.strip() and "not found" not in result.stdout:
            print(f"\n{directory}:")
            for line in result.stdout.strip().split('\n'):
                print(f"  - {line}")

finally:
    # 清理资源
    print("\n" + "=" * 60)
    print("🧹 清理沙箱资源...")
    sandbox.kill()
    print("✅ 完成！")
    print("=" * 60)

print("\n💡 总结:")
print("   1. 文件系统共享 - Agents 通过 JSON 文件交换数据")
print("   2. 流水线处理 - Agent 链式处理，输出作为下一个的输入")
print("   3. 并行协作 - 多个 Agents 同时处理，Coordinator 整合结果")
print("   4. 状态同步 - 共享状态文件协调任务分配")
print("\n🔗 这些模式可以组合使用，构建复杂的 Multi-Agent 系统")
