#!/usr/bin/env python3
"""
Agent 协调器模式演示

展示如何通过外部协调器（这个 Python 脚本）来协调多个 agents
验证：数据是通过协调器传递，而不是 agents 之间直接通信
"""

from pathlib import Path
from dotenv import load_dotenv
from e2b import Sandbox
import json

# 加载 API Key
load_dotenv(Path(__file__).parent / '.env')

print("=" * 60)
print("Agent 协调器模式演示")
print("=" * 60)

class AgentOrchestrator:
    """
    外部协调器 - 负责：
    1. 创建和管理 sandboxes
    2. 在 agents 之间传递数据
    3. 控制执行流程
    """

    def __init__(self):
        self.sandbox = None
        self.execution_log = []

    def log(self, message):
        """记录执行流程"""
        self.execution_log.append(message)
        print(f"   📝 {message}")

    def create_sandbox(self):
        """创建共享沙箱"""
        self.sandbox = Sandbox.create()
        self.log(f"创建沙箱: {self.sandbox.sandbox_id[:12]}...")

    def run_agent(self, agent_name, script_path, input_data=None):
        """
        运行单个 agent

        关键点：
        1. 协调器将 input_data 写入文件
        2. Agent 从文件读取输入
        3. Agent 将结果输出到 stdout
        4. 协调器读取 agent 的输出
        5. 协调器将输出传递给下一个 agent

        ⚠️ 注意：agents 之间没有直接通信！
        """
        self.log(f"运行 {agent_name}")

        # 📍 步骤 1: 协调器注入输入数据
        if input_data:
            self.sandbox.files.write(
                "/home/user/input.json",
                json.dumps(input_data, indent=2)
            )
            self.log(f"  → 协调器注入输入: {len(json.dumps(input_data))} bytes")

        # 📍 步骤 2: 执行 agent
        result = self.sandbox.commands.run(f"python3 {script_path}")

        if result.exit_code != 0:
            self.log(f"  ✗ Agent 执行失败: {result.stderr}")
            return None

        # 📍 步骤 3: 协调器提取输出
        try:
            output = json.loads(result.stdout)
            self.log(f"  ← 协调器提取输出: {len(result.stdout)} bytes")
            return output
        except json.JSONDecodeError:
            self.log(f"  ✗ 无法解析输出: {result.stdout[:100]}")
            return None

    def execute_workflow(self):
        """
        执行完整的 agent 工作流

        工作流：
        Input → Agent A → Orchestrator → Agent B → Orchestrator → Agent C → Output

        数据流：
        - Input 由协调器提供给 Agent A
        - Agent A 的输出由协调器读取
        - 协调器将 Agent A 的输出传递给 Agent B
        - Agent B 的输出由协调器读取
        - 协调器将 Agent B 的输出传递给 Agent C
        - Agent C 的输出由协调器返回
        """

        print("\n" + "=" * 60)
        print("执行工作流: Agent A → Agent B → Agent C")
        print("=" * 60)

        # 创建 agents 脚本
        self._create_agents()

        # 初始输入
        initial_input = {
            "task": "分析销售数据",
            "data": [100, 150, 200, 180, 220]
        }

        print(f"\n🚀 初始输入: {initial_input}")

        # Agent A: 数据分析
        print("\n" + "-" * 60)
        print("阶段 1: Agent A (数据分析)")
        print("-" * 60)
        result_a = self.run_agent("Agent A", "/home/user/agent_a.py", initial_input)

        if not result_a:
            print("❌ Agent A 失败")
            return

        print(f"\n📊 Agent A 输出: {result_a}")
        print("   ⚠️  注意：这个输出是协调器读取的，不是 Agent B 直接接收的")

        # Agent B: 数据转换
        print("\n" + "-" * 60)
        print("阶段 2: Agent B (数据转换)")
        print("-" * 60)
        print(f"   📥 协调器将 Agent A 的输出传递给 Agent B")
        result_b = self.run_agent("Agent B", "/home/user/agent_b.py", result_a)

        if not result_b:
            print("❌ Agent B 失败")
            return

        print(f"\n🔄 Agent B 输出: {result_b}")

        # Agent C: 报告生成
        print("\n" + "-" * 60)
        print("阶段 3: Agent C (报告生成)")
        print("-" * 60)
        print(f"   📥 协调器将 Agent B 的输出传递给 Agent C")
        result_c = self.run_agent("Agent C", "/home/user/agent_c.py", result_b)

        if not result_c:
            print("❌ Agent C 失败")
            return

        print(f"\n📝 Agent C 输出: {result_c}")

        # 最终结果
        print("\n" + "=" * 60)
        print("✅ 工作流完成")
        print("=" * 60)
        print(f"\n最终结果:\n{json.dumps(result_c, indent=2)}")

        return result_c

    def _create_agents(self):
        """创建 agent 脚本"""

        # Agent A: 数据分析
        agent_a_script = """
import json
import sys

# 📍 Agent A 从文件读取输入（协调器写入的）
with open('/home/user/input.json', 'r') as f:
    input_data = json.load(f)

# 执行分析
data = input_data['data']
analysis = {
    'agent': 'Agent A',
    'task': input_data['task'],
    'total': sum(data),
    'average': sum(data) / len(data),
    'count': len(data)
}

# 📍 Agent A 将结果输出到 stdout（协调器会读取）
print(json.dumps(analysis))

# ⚠️ 注意：Agent A 不知道 Agent B 的存在
# ⚠️ 注意：Agent A 不直接与 Agent B 通信
"""

        # Agent B: 数据转换
        agent_b_script = """
import json

# 📍 Agent B 从文件读取输入（协调器写入的，来自 Agent A）
with open('/home/user/input.json', 'r') as f:
    input_data = json.load(f)

# 执行转换
transformed = {
    'agent': 'Agent B',
    'previous_agent': input_data['agent'],
    'total_sales': input_data['total'],
    'avg_sales': input_data['average'],
    'status': 'transformed'
}

# 📍 Agent B 将结果输出到 stdout（协调器会读取）
print(json.dumps(transformed))

# ⚠️ 注意：Agent B 不知道 Agent A 或 Agent C
# ⚠️ 注意：数据是协调器传递的，不是 Agent A 直接传的
"""

        # Agent C: 报告生成
        agent_c_script = """
import json

# 📍 Agent C 从文件读取输入（协调器写入的，来自 Agent B）
with open('/home/user/input.json', 'r') as f:
    input_data = json.load(f)

# 生成报告
report = {
    'agent': 'Agent C',
    'report_type': 'Sales Summary',
    'total_sales': f"${input_data['total_sales']}",
    'average_sales': f"${input_data['avg_sales']:.2f}",
    'status': input_data['status'],
    'generated_by': f"{input_data['previous_agent']} → Agent C"
}

# 📍 Agent C 将结果输出到 stdout（协调器会读取）
print(json.dumps(report))

# ⚠️ 注意：Agent C 是工作流的最后一个环节
# ⚠️ 注意：所有数据都是通过协调器流动的
"""

        self.sandbox.files.write("/home/user/agent_a.py", agent_a_script)
        self.sandbox.files.write("/home/user/agent_b.py", agent_b_script)
        self.sandbox.files.write("/home/user/agent_c.py", agent_c_script)
        self.log("创建 3 个 agent 脚本")

    def visualize_data_flow(self):
        """可视化数据流"""
        print("\n" + "=" * 60)
        print("数据流可视化")
        print("=" * 60)
        print("""
协调器模式的数据流：

        ┌─────────────┐
        │  协调器     │  ← 你的 Python 脚本
        │ (Orchestr.) │
        └──────┬──────┘
               │
               ├─→ 1. 注入输入数据
               │
        ┌──────▼──────┐
        │  Agent A    │
        └──────┬──────┘
               │
               ├─→ 2. 输出到 stdout
               │
        ┌──────▼──────┐
        │  协调器读取  │  ← 协调器提取数据
        └──────┬──────┘
               │
               ├─→ 3. 注入到 Agent B
               │
        ┌──────▼──────┐
        │  Agent B    │
        └──────┬──────┘
               │
               ├─→ 4. 输出到 stdout
               │
        ┌──────▼──────┐
        │  协调器读取  │  ← 协调器提取数据
        └──────┬──────┘
               │
               ├─→ 5. 注入到 Agent C
               │
        ┌──────▼──────┐
        │  Agent C    │
        └──────┬──────┘
               │
               └─→ 6. 最终输出

⚠️  关键点：
   - Agents 之间没有直接通信
   - 所有数据都通过协调器中转
   - Agents 不知道彼此的存在
   - 协调器控制整个数据流
""")

    def cleanup(self):
        """清理资源"""
        if self.sandbox:
            self.sandbox.kill()
            self.log("清理沙箱")


# 主程序
if __name__ == "__main__":
    orchestrator = AgentOrchestrator()

    try:
        # 创建沙箱
        orchestrator.create_sandbox()

        # 可视化数据流
        orchestrator.visualize_data_flow()

        # 执行工作流
        result = orchestrator.execute_workflow()

        # 显示执行日志
        print("\n" + "=" * 60)
        print("执行日志")
        print("=" * 60)
        for i, log in enumerate(orchestrator.execution_log, 1):
            print(f"{i}. {log}")

        print("\n" + "=" * 60)
        print("✅ 演示完成")
        print("=" * 60)

        print("\n💡 关键结论：")
        print("   1. ✅ 数据通过协调器传递，不是 agents 直接通信")
        print("   2. ✅ E2B 不需要实现 sandbox 网络互通")
        print("   3. ✅ 这是集中式协调模式（Orchestrator Pattern）")
        print("   4. ✅ 协调器充当消息总线的角色")

    finally:
        orchestrator.cleanup()
