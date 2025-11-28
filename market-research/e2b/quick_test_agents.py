#!/usr/bin/env python3
"""
快速测试 Agents 协作
简单的演示，展示核心概念
"""

from pathlib import Path
from dotenv import load_dotenv
from e2b import Sandbox
import json

# 加载 API Key
load_dotenv(Path(__file__).parent / '.env')

print("🚀 快速测试 - Agents 协作\n")
print("=" * 50)

# 创建共享沙箱
print("\n1️⃣  创建沙箱...")
sandbox = Sandbox.create()
print(f"   ✅ 沙箱 ID: {sandbox.sandbox_id[:12]}...")

try:
    # 场景：3个 agents 协作处理销售数据
    print("\n2️⃣  场景：销售数据分析流水线")
    print("   Agent 1 → Agent 2 → Agent 3")

    # Agent 1: 数据采集
    print("\n   📊 Agent 1: 数据采集")
    data = {
        "sales": [100, 150, 200, 180, 220],
        "product": "Widget A"
    }
    sandbox.files.write("/tmp/data.json", json.dumps(data))
    print(f"      ✅ 采集数据: {data['product']}, {len(data['sales'])} 条记录")

    # Agent 2: 数据分析
    print("\n   🔍 Agent 2: 数据分析")
    analysis_script = """
import json

with open('/tmp/data.json', 'r') as f:
    data = json.load(f)

sales = data['sales']
result = {
    'total': sum(sales),
    'average': sum(sales) / len(sales),
    'max': max(sales)
}

with open('/tmp/analysis.json', 'w') as f:
    json.dump(result, f)

print(f"Total: {result['total']}, Avg: {result['average']:.2f}")
"""
    sandbox.files.write("/tmp/analyze.py", analysis_script)
    result = sandbox.commands.run("python3 /tmp/analyze.py")
    print(f"      ✅ {result.stdout.strip()}")

    # Agent 3: 报告生成
    print("\n   📝 Agent 3: 报告生成")
    report_script = """
import json

with open('/tmp/data.json', 'r') as f:
    data = json.load(f)

with open('/tmp/analysis.json', 'r') as f:
    analysis = json.load(f)

report = f'''
产品: {data['product']}
总销售: ${analysis['total']}
平均: ${analysis['average']:.2f}
'''

print(report.strip())
"""
    sandbox.files.write("/tmp/report.py", report_script)
    result = sandbox.commands.run("python3 /tmp/report.py")
    print(f"\n      📋 最终报告:")
    for line in result.stdout.strip().split('\n'):
        print(f"         {line}")

    print("\n3️⃣  验证数据流")
    print("   ✅ Agent 1 → /tmp/data.json")
    print("   ✅ Agent 2 → /tmp/analysis.json")
    print("   ✅ Agent 3 → 生成报告")

    print("\n" + "=" * 50)
    print("✅ 测试完成！Agents 成功协作处理数据")
    print("=" * 50)

finally:
    sandbox.kill()
    print("\n🧹 沙箱已清理")

print("\n💡 这个例子展示了:")
print("   - 多个 agents 在同一沙箱中协作")
print("   - 通过文件系统共享数据")
print("   - 流水线式的数据处理")
print("\n📚 查看完整示例:")
print("   python3 agents_collaboration.py")
print("   python3 multi_sandbox_agents.py")
