#!/usr/bin/env python3
"""
E2B 测试脚本示例
使用 .env 文件中的 API Key
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载当前目录的 .env 文件
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# 验证 API Key 是否加载
api_key = os.getenv('E2B_API_KEY')
if not api_key or api_key == 'your_api_key_here':
    print("❌ 错误: 请在 .env 文件中设置你的 E2B_API_KEY")
    print("   1. 访问 https://e2b.dev 获取 API Key")
    print("   2. 编辑 e2b/.env 文件，替换 'your_api_key_here' 为你的真实 API Key")
    exit(1)

print(f"✅ API Key 已加载: {api_key[:10]}...")

# 现在可以使用 E2B SDK 了
try:
    from e2b import Sandbox

    print("\n🚀 创建沙箱...")
    sandbox = Sandbox.create()
    print("✅ 沙箱创建成功!")

    print("\n📝 执行测试代码...")
    result = sandbox.commands.run("python3 -c \"print('Hello from E2B!')\"")
    print(f"退出码: {result.exit_code}")
    print(f"输出: {result.stdout.strip()}")

    # 测试文件操作
    print("\n📁 测试文件操作...")
    sandbox.files.write("/tmp/test.txt", "Hello E2B!")
    content = sandbox.files.read("/tmp/test.txt")
    print(f"文件内容: {content}")

    # 清理
    sandbox.kill()
    print("\n🎉 测试完成!")

except ImportError:
    print("\n⚠️  E2B SDK 未安装")
    print("   运行: pip install e2b")
except Exception as e:
    print(f"\n❌ 错误: {e}")
