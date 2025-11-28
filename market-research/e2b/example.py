#!/usr/bin/env python3
"""
E2B 示例代码 - 使用 .env 文件中的 API Key
"""

from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件（只需要这两行！）
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# 之后直接使用 E2B SDK，API Key 会自动从环境变量读取
from e2b import Sandbox

print("创建沙箱...")
sandbox = Sandbox.create()

try:
    # 示例 1: 执行简单命令
    print("\n示例 1: 执行 Python 代码")
    result = sandbox.commands.run("python3 -c \"print('Hello from E2B!')\"")
    print(f"输出: {result.stdout.strip()}")

    # 示例 2: 执行数据处理（使用内置库）
    print("\n示例 2: 数据处理")
    code = """
data_a = [1, 2, 3]
data_b = [4, 5, 6]
print('Sum of a:', sum(data_a))
print('Sum of b:', sum(data_b))
print('Total:', sum(data_a) + sum(data_b))
"""
    result = sandbox.commands.run(f'python3 -c "{code}"')
    print(f"结果:\n{result.stdout}")

    # 示例 3: 文件操作
    print("\n示例 3: 文件操作")
    sandbox.files.write("/tmp/test.txt", "Hello E2B!")
    content = sandbox.files.read("/tmp/test.txt")
    print(f"文件内容: {content}")

    # 示例 4: 列出文件
    print("\n示例 4: 列出目录")
    result = sandbox.commands.run("ls -la /tmp")
    print(result.stdout)

    # 示例 5: 使用 Python 内置功能
    print("\n示例 5: JSON 处理")
    result = sandbox.commands.run("python3 -c \"import json; data = {'name': 'E2B', 'version': 1}; print(json.dumps(data, indent=2))\"")
    print(result.stdout.strip())

finally:
    # 清理资源
    sandbox.kill()
    print("\n✅ 测试完成!")
