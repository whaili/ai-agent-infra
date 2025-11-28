# E2B SDK API 快速参考

## 正确的 API 使用方法

### 基础设置

```python
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件中的 API Key
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

from e2b import Sandbox
```

## 核心 API

### 1. 创建和销毁沙箱

```python
# 创建沙箱
sandbox = Sandbox.create()

# 使用沙箱...

# 销毁沙箱（重要！）
sandbox.kill()
```

### 2. 执行命令 - `sandbox.commands`

```python
# 执行命令
result = sandbox.commands.run("ls -la")

# 获取结果
print(result.exit_code)   # 退出码
print(result.stdout)      # 标准输出
print(result.stderr)      # 标准错误

# 执行 Python 代码
result = sandbox.commands.run("python3 -c \"print('Hello')\"")
print(result.stdout)

# 执行多行 Python 代码（使用文件）
sandbox.files.write("/tmp/script.py", """
import pandas as pd
data = {'a': [1, 2, 3]}
df = pd.DataFrame(data)
print(df.sum())
""")
result = sandbox.commands.run("python3 /tmp/script.py")
print(result.stdout)
```

### 3. 文件操作 - `sandbox.files`

```python
# 写入文件
sandbox.files.write("/tmp/test.txt", "Hello World!")

# 读取文件
content = sandbox.files.read("/tmp/test.txt")
print(content)  # "Hello World!"

# 列出目录（使用 commands）
result = sandbox.commands.run("ls -la /tmp")
print(result.stdout)
```

### 4. PTY (伪终端) - `sandbox.pty`

```python
# 启动交互式进程
pty = sandbox.pty.create("python3")

# 发送输入
pty.send_stdin("import sys\n")
pty.send_stdin("print(sys.version)\n")

# 读取输出
# 注意：PTY 是异步的，需要等待输出
```

### 5. 获取沙箱信息

```python
# 获取沙箱 ID
print(sandbox.sandbox_id)

# 检查沙箱是否运行中
if sandbox.is_running():
    print("沙箱正在运行")

# 获取沙箱信息
info = sandbox.get_info()
print(info)

# 获取沙箱指标
metrics = sandbox.get_metrics()
print(metrics)
```

### 6. 获取主机地址

```python
# 如果沙箱内运行了 web 服务
sandbox.commands.run("python3 -m http.server 8000 &")

# 获取访问地址
url = sandbox.get_host(8000)
print(f"访问地址: {url}")
```

## 完整示例

```python
from pathlib import Path
from dotenv import load_dotenv

# 加载 API Key
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

from e2b import Sandbox

# 创建沙箱
sandbox = Sandbox.create()

try:
    # 1. 执行简单命令
    result = sandbox.commands.run("echo 'Hello from E2B'")
    print(result.stdout)

    # 2. 执行 Python 代码
    result = sandbox.commands.run("python3 -c \"print(2 + 2)\"")
    print(result.stdout)  # "4"

    # 3. 文件操作
    sandbox.files.write("/tmp/data.txt", "Some data")
    content = sandbox.files.read("/tmp/data.txt")
    print(content)

    # 4. 运行脚本
    script = """
import pandas as pd
df = pd.DataFrame({'a': [1, 2, 3]})
print(df.sum())
"""
    sandbox.files.write("/tmp/script.py", script)
    result = sandbox.commands.run("python3 /tmp/script.py")
    print(result.stdout)

finally:
    # 清理资源
    sandbox.kill()
```

## 常用命令模式

### 执行 Python 代码片段

```python
# 简单表达式
result = sandbox.commands.run("python3 -c \"print(2 + 2)\"")

# 导入库
result = sandbox.commands.run("python3 -c \"import numpy as np; print(np.version.version)\"")

# 多行代码（使用三引号）
code = """
import pandas as pd
import numpy as np

data = {'x': [1, 2, 3], 'y': [4, 5, 6]}
df = pd.DataFrame(data)
print(df.describe())
"""
sandbox.files.write("/tmp/analysis.py", code)
result = sandbox.commands.run("python3 /tmp/analysis.py")
print(result.stdout)
```

### 安装和使用包

```python
# 安装 Python 包
result = sandbox.commands.run("pip install requests")
print(result.stdout)

# 使用安装的包
result = sandbox.commands.run("python3 -c \"import requests; print(requests.__version__)\"")
print(result.stdout)
```

### 系统命令

```python
# 列出文件
result = sandbox.commands.run("ls -la /home")

# 查看系统信息
result = sandbox.commands.run("uname -a")

# 查看磁盘使用
result = sandbox.commands.run("df -h")

# 查看进程
result = sandbox.commands.run("ps aux")
```

## 注意事项

1. **始终清理资源**: 使用 `sandbox.kill()` 销毁沙箱
2. **API Key**: 确保 `.env` 文件中设置了 `E2B_API_KEY`
3. **命令格式**: 使用 `sandbox.commands.run()` 而不是 `sandbox.run_code()`
4. **文件路径**: 沙箱内的路径，如 `/tmp/`, `/home/user/` 等
5. **返回值**: `CommandResult` 对象包含 `exit_code`, `stdout`, `stderr`

## 错误处理

```python
from e2b import Sandbox, SandboxException

try:
    sandbox = Sandbox.create()
    result = sandbox.commands.run("python3 -c \"1/0\"")

    if result.exit_code != 0:
        print(f"命令失败: {result.stderr}")
    else:
        print(f"成功: {result.stdout}")

except SandboxException as e:
    print(f"沙箱错误: {e}")
finally:
    if sandbox:
        sandbox.kill()
```

## 更多资源

- 官方文档: https://e2b.dev/docs
- GitHub: https://github.com/e2b-dev/e2b
- 本地示例: [example.py](example.py)
- 测试脚本: [test_e2b.py](test_e2b.py)
