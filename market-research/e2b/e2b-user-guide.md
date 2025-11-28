# E2B 用户手册

> Cloud Runtime for AI Agents - 为 AI Agent 设计的云端运行时环境
>
> 文档版本：v1.0 | 基于公开信息整理

---

## 目录

- [简介](#简介)
- [快速开始](#快速开始)
- [核心概念](#核心概念)
- [Python SDK](#python-sdk)
- [JavaScript SDK](#javascript-sdk)
- [模板系统](#模板系统)
- [进阶功能](#进阶功能)
- [API 参考](#api-参考)
- [最佳实践](#最佳实践)
- [故障排查](#故障排查)
- [定价](#定价)

---

## 简介

### 什么是 E2B？

E2B (Execute to Build) 是一个专为 AI Agent 设计的**安全沙箱运行时环境**，让 AI 能够安全地执行代码、操作浏览器和使用完整的桌面环境。

### 核心特性

- ⚡ **快速启动** - 沙箱启动时间 < 2 秒
- 🔒 **安全隔离** - 基于 Firecracker 微虚拟机的硬件级隔离
- 🌍 **全球部署** - 多区域低延迟访问
- 🛠️ **开箱即用** - 预配置的开发环境和工具
- 🔌 **简单集成** - 3 行代码即可使用

### 使用场景

```yaml
代码解释器：
  - AI 生成代码的安全执行
  - 数据分析和可视化
  - 自动化脚本运行

浏览器自动化：
  - 网页抓取和数据提取
  - 表单填写和测试
  - 截图和 PDF 生成

桌面环境：
  - Computer Use Agent
  - GUI 应用测试
  - 远程开发环境
```

---

## 快速开始

### 1. 注册账号

访问 [https://e2b.dev](https://e2b.dev) 创建账号。

### 2. 获取 API Key

```bash
# 在控制台创建 API Key
# 复制并保存到环境变量
export E2B_API_KEY="your_api_key_here"
```

### 3. 安装 SDK

#### Python

```bash
pip install e2b
```

#### JavaScript/TypeScript

```bash
npm install @e2b/sdk
# 或
yarn add @e2b/sdk
```

### 4. 第一个示例

#### Python

```python
from e2b import Sandbox

# 创建沙箱
sandbox = Sandbox.create()

# 执行代码
execution = sandbox.run_code("print('Hello from E2B!')")
print(execution.logs.stdout)  # 输出: Hello from E2B!

# 清理资源
sandbox.kill()
```

#### JavaScript

```javascript
import { Sandbox } from '@e2b/sdk'

// 创建沙箱
const sandbox = await Sandbox.create()

// 执行代码
const execution = await sandbox.runCode("console.log('Hello from E2B!')")
console.log(execution.logs.stdout)  // 输出: Hello from E2B!

// 清理资源
await sandbox.kill()
```

---

## 核心概念

### Sandbox（沙箱）

沙箱是一个完全隔离的运行环境，每个沙箱都是独立的微虚拟机。

```python
# 沙箱生命周期
sandbox = Sandbox.create()  # 创建（< 2 秒）
# ... 使用沙箱
sandbox.kill()              # 销毁
```

**特性：**
- 独立的文件系统
- 独立的网络空间
- 资源隔离（CPU、内存）
- 自动超时清理

### Template（模板）

模板是预配置的沙箱环境，包含特定的软件包和工具。

```python
# 使用不同模板
base_sandbox = Sandbox.create(template="base")
browser_sandbox = Sandbox.create(template="browser")
desktop_sandbox = Sandbox.create(template="desktop")
```

**内置模板：**

| 模板 | 说明 | 用途 |
|------|------|------|
| `base` | Python 3.11 + 常用库 | 代码执行 |
| `browser` | Chromium + Playwright | 浏览器自动化 |
| `desktop` | Ubuntu Desktop + VNC | 完整桌面环境 |

### Process（进程）

在沙箱中运行的程序。

```python
# 启动进程
process = sandbox.process.start("python script.py")

# 等待完成
process.wait()

# 获取输出
print(process.stdout)
```

### Filesystem（文件系统）

沙箱内的文件操作。

```python
# 写入文件
sandbox.filesystem.write("/tmp/data.txt", "content")

# 读取文件
content = sandbox.filesystem.read("/tmp/data.txt")

# 列出目录
files = sandbox.filesystem.list("/tmp")
```

---

## Python SDK

### 安装

```bash
pip install e2b
```

### 基础使用

#### 创建沙箱

```python
from e2b import Sandbox

# 基础创建
sandbox = Sandbox.create()

# 指定模板
sandbox = Sandbox.create(template="browser")

# 设置超时（秒）
sandbox = Sandbox.create(timeout=600)

# 设置环境变量
sandbox = Sandbox.create(
    env_vars={
        "API_KEY": "secret",
        "DEBUG": "true"
    }
)
```

#### 执行代码

```python
# 简单执行
result = sandbox.run_code("print('hello')")
print(result.logs.stdout)  # 'hello\n'
print(result.logs.stderr)  # 错误输出
print(result.error)        # 异常信息

# 多行代码
code = """
import numpy as np
arr = np.array([1, 2, 3])
print(arr.sum())
"""
result = sandbox.run_code(code)

# 捕获返回值
result = sandbox.run_code("2 + 2")
# 注意：run_code 不直接返回表达式值，需要 print
```

#### 进程管理

```python
# 启动进程
process = sandbox.process.start(
    cmd="python app.py",
    cwd="/home/user",
    env_vars={"PORT": "8000"}
)

# 等待完成
exit_code = process.wait()

# 发送输入
process.send_stdin("input data\n")

# 获取输出
output = process.stdout
errors = process.stderr

# 终止进程
process.kill()
```

#### 文件操作

```python
# 写入文件
sandbox.filesystem.write(
    path="/app/config.json",
    content='{"key": "value"}'
)

# 读取文件
content = sandbox.filesystem.read("/app/config.json")

# 写入二进制
with open("local_image.png", "rb") as f:
    data = f.read()
sandbox.filesystem.write("/tmp/image.png", data)

# 列出目录
files = sandbox.filesystem.list("/app")
for file in files:
    print(f"{file.name} - {file.type}")  # name, type, size

# 创建目录
sandbox.filesystem.make_dir("/app/logs")

# 删除文件
sandbox.filesystem.remove("/tmp/temp.txt")
```

#### 下载和上传

```python
# 上传本地文件
sandbox.upload_file(
    src_path="./local_file.txt",
    dest_path="/app/file.txt"
)

# 下载沙箱文件
sandbox.download_file(
    src_path="/app/result.csv",
    dest_path="./result.csv"
)
```

#### 网络访问

```python
# 沙箱默认可以访问外网
result = sandbox.run_code("""
import requests
response = requests.get('https://api.github.com')
print(response.status_code)
""")

# 访问沙箱内的服务（端口映射）
# 如果沙箱内运行了 web 服务在端口 8000
# 可以通过 sandbox 对象获取访问地址
url = sandbox.get_host(8000)
print(f"Service available at: {url}")
```

#### 异常处理

```python
from e2b import Sandbox, TimeoutException, SandboxException

try:
    sandbox = Sandbox.create(timeout=60)
    result = sandbox.run_code("import time; time.sleep(100)")
except TimeoutException:
    print("Sandbox execution timed out")
except SandboxException as e:
    print(f"Sandbox error: {e}")
finally:
    if sandbox:
        sandbox.kill()
```

#### 上下文管理器（推荐）

```python
from e2b import Sandbox

# 自动清理资源
with Sandbox.create() as sandbox:
    result = sandbox.run_code("print('hello')")
    print(result.logs.stdout)
# sandbox 自动被销毁
```

---

## JavaScript SDK

### 安装

```bash
npm install @e2b/sdk
```

### 基础使用

#### 创建沙箱

```typescript
import { Sandbox } from '@e2b/sdk'

// 基础创建
const sandbox = await Sandbox.create()

// 指定模板
const sandbox = await Sandbox.create({ template: 'browser' })

// 设置超时
const sandbox = await Sandbox.create({
  timeout: 600000  // 毫秒
})

// 设置环境变量
const sandbox = await Sandbox.create({
  envVars: {
    API_KEY: 'secret',
    DEBUG: 'true'
  }
})
```

#### 执行代码

```typescript
// 简单执行
const result = await sandbox.runCode("console.log('hello')")
console.log(result.logs.stdout)  // 'hello\n'

// 多行代码
const code = `
const arr = [1, 2, 3]
console.log(arr.reduce((a, b) => a + b))
`
const result = await sandbox.runCode(code)
```

#### 进程管理

```typescript
// 启动进程
const process = await sandbox.process.start({
  cmd: 'node app.js',
  cwd: '/home/user',
  envVars: { PORT: '8000' }
})

// 等待完成
const exitCode = await process.wait()

// 发送输入
await process.sendStdin('input data\n')

// 获取输出
const output = process.stdout
const errors = process.stderr

// 终止进程
await process.kill()
```

#### 文件操作

```typescript
// 写入文件
await sandbox.filesystem.write({
  path: '/app/config.json',
  content: JSON.stringify({ key: 'value' })
})

// 读取文件
const content = await sandbox.filesystem.read('/app/config.json')

// 列出目录
const files = await sandbox.filesystem.list('/app')
files.forEach(file => {
  console.log(`${file.name} - ${file.type}`)
})

// 创建目录
await sandbox.filesystem.makeDir('/app/logs')

// 删除文件
await sandbox.filesystem.remove('/tmp/temp.txt')
```

#### 清理资源

```typescript
// 手动清理
await sandbox.kill()

// 或使用 try-finally
const sandbox = await Sandbox.create()
try {
  const result = await sandbox.runCode("console.log('hello')")
  console.log(result.logs.stdout)
} finally {
  await sandbox.kill()
}
```

---

## 模板系统

### 内置模板

#### Base Template

**标识符：** `base`

**预装软件：**
```yaml
运行时：
  - Python 3.11
  - Node.js 18
  - pip, npm, yarn

Python 包：
  - numpy
  - pandas
  - matplotlib
  - requests
  - beautifulsoup4

工具：
  - git
  - curl
  - vim
  - jq
```

**使用示例：**
```python
sandbox = Sandbox.create(template="base")
sandbox.run_code("""
import pandas as pd
df = pd.DataFrame({'a': [1, 2, 3]})
print(df.sum())
""")
```

#### Browser Template

**标识符：** `browser`

**预装软件：**
```yaml
浏览器：
  - Chromium (最新稳定版)
  - Playwright
  - Selenium

特性：
  - 无头模式支持
  - CDP (Chrome DevTools Protocol)
  - 截图和 PDF 生成
```

**使用示例：**
```python
from playwright.sync_api import sync_playwright

sandbox = Sandbox.create(template="browser")

# 获取浏览器连接 URL
browser_url = sandbox.get_host(9222)  # CDP 端口

# 使用 Playwright 连接
with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(browser_url)
    page = browser.new_page()
    page.goto('https://example.com')
    page.screenshot(path='screenshot.png')
```

#### Desktop Template

**标识符：** `desktop`

**预装软件：**
```yaml
桌面环境：
  - Ubuntu 22.04
  - XFCE Desktop
  - VNC Server

应用：
  - Firefox
  - LibreOffice
  - VS Code
  - Terminal
```

**使用示例：**
```python
sandbox = Sandbox.create(template="desktop")

# 获取 VNC 访问 URL
vnc_url = sandbox.get_vnc_url()
print(f"Access desktop at: {vnc_url}")

# 在桌面中执行命令
sandbox.run_code("xdotool key alt+F2; sleep 1; xdotool type 'firefox'")
```

### 自定义模板

#### 创建自定义模板

```yaml
# e2b.toml
[template]
name = "my-custom-template"
base = "base"

[packages]
python = [
  "tensorflow==2.13.0",
  "transformers",
  "torch"
]
apt = [
  "ffmpeg",
  "imagemagick"
]

[files]
"./config" = "/app/config"
"./scripts" = "/app/scripts"
```

#### 构建和发布

```bash
# 构建模板
e2b template build

# 发布到 E2B
e2b template push my-custom-template

# 使用自定义模板
sandbox = Sandbox.create(template="my-custom-template")
```

---

## 进阶功能

### 长时间运行任务

```python
# 创建长超时的沙箱
sandbox = Sandbox.create(timeout=3600)  # 1 小时

# 运行长任务
process = sandbox.process.start("python long_task.py")

# 异步等待
import asyncio
async def wait_for_process():
    exit_code = await process.wait_async()
    print(f"Process finished with code: {exit_code}")

asyncio.run(wait_for_process())
```

### 流式输出

```python
# 实时获取进程输出
process = sandbox.process.start("python train.py")

# 流式读取 stdout
for line in process.stdout_stream():
    print(f"[stdout] {line}", end="")

# 流式读取 stderr
for line in process.stderr_stream():
    print(f"[stderr] {line}", end="")
```

### 端口转发

```python
# 在沙箱中启动 web 服务
sandbox.process.start("python -m http.server 8000")

# 获取公网访问地址
url = sandbox.get_host(8000)
print(f"Service available at: {url}")

# 访问服务
import requests
response = requests.get(url)
print(response.text)
```

### 数据持久化

```python
# 创建沙箱
sandbox = Sandbox.create()

# 上传数据
sandbox.upload_file("./dataset.csv", "/data/dataset.csv")

# 处理数据
sandbox.run_code("""
import pandas as pd
df = pd.read_csv('/data/dataset.csv')
df['processed'] = df['value'] * 2
df.to_csv('/data/output.csv', index=False)
""")

# 下载结果
sandbox.download_file("/data/output.csv", "./output.csv")

sandbox.kill()
```

### 沙箱快照（Snapshot）

```python
# 创建沙箱并配置环境
sandbox = Sandbox.create()
sandbox.run_code("pip install custom-package")
sandbox.filesystem.write("/app/config.json", "config")

# 创建快照
snapshot_id = sandbox.create_snapshot()

# 从快照创建新沙箱（快速恢复）
new_sandbox = Sandbox.from_snapshot(snapshot_id)
# 环境和文件都已恢复
```

### 并发执行

```python
import asyncio
from e2b import Sandbox

async def run_task(task_id):
    sandbox = Sandbox.create()
    result = sandbox.run_code(f"print('Task {task_id} running')")
    print(result.logs.stdout)
    sandbox.kill()
    return task_id

# 并发运行 10 个任务
async def main():
    tasks = [run_task(i) for i in range(10)]
    results = await asyncio.gather(*tasks)
    print(f"Completed {len(results)} tasks")

asyncio.run(main())
```

---

## API 参考

### Sandbox Class

#### 构造方法

```python
Sandbox.create(
    template: str = "base",
    timeout: int = 300,
    env_vars: Dict[str, str] = None,
    on_exit: Callable = None
) -> Sandbox
```

#### 实例方法

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `run_code(code: str)` | 执行代码 | `Execution` |
| `kill()` | 销毁沙箱 | `None` |
| `get_host(port: int)` | 获取端口访问地址 | `str` |
| `upload_file(src, dest)` | 上传文件 | `None` |
| `download_file(src, dest)` | 下载文件 | `None` |

#### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `sandbox_id` | `str` | 沙箱唯一标识 |
| `template` | `str` | 使用的模板 |
| `process` | `ProcessManager` | 进程管理器 |
| `filesystem` | `FilesystemManager` | 文件系统管理器 |

### ProcessManager Class

```python
class ProcessManager:
    def start(
        self,
        cmd: str,
        cwd: str = "/home/user",
        env_vars: Dict[str, str] = None
    ) -> Process

    def list() -> List[Process]

    def get(pid: int) -> Process
```

### Process Class

```python
class Process:
    pid: int
    stdout: str
    stderr: str
    exit_code: Optional[int]

    def wait() -> int
    def kill() -> None
    def send_stdin(data: str) -> None
    def stdout_stream() -> Iterator[str]
    def stderr_stream() -> Iterator[str]
```

### FilesystemManager Class

```python
class FilesystemManager:
    def write(path: str, content: Union[str, bytes]) -> None
    def read(path: str) -> str
    def list(path: str) -> List[FileInfo]
    def make_dir(path: str) -> None
    def remove(path: str) -> None
    def exists(path: str) -> bool
```

### Execution Class

```python
class Execution:
    logs: ExecutionLogs
    error: Optional[str]

class ExecutionLogs:
    stdout: str
    stderr: str
```

---

## 最佳实践

### 1. 资源管理

#### ✅ 推荐

```python
# 使用上下文管理器
with Sandbox.create() as sandbox:
    result = sandbox.run_code("print('hello')")
# 自动清理

# 或使用 try-finally
sandbox = Sandbox.create()
try:
    result = sandbox.run_code("print('hello')")
finally:
    sandbox.kill()
```

#### ❌ 不推荐

```python
# 忘记清理
sandbox = Sandbox.create()
result = sandbox.run_code("print('hello')")
# 沙箱没有被销毁，持续计费
```

### 2. 错误处理

#### ✅ 推荐

```python
from e2b import Sandbox, TimeoutException

with Sandbox.create(timeout=60) as sandbox:
    try:
        result = sandbox.run_code(user_code)
        if result.error:
            print(f"Execution error: {result.error}")
        else:
            print(result.logs.stdout)
    except TimeoutException:
        print("Execution timed out")
    except Exception as e:
        print(f"Unexpected error: {e}")
```

### 3. 代码安全

#### ✅ 推荐

```python
# 设置合理的超时
sandbox = Sandbox.create(timeout=300)

# 限制网络访问（如果需要）
# 注意：E2B 沙箱默认可以访问外网
# 如需限制，需要在代码层面处理

# 验证用户输入
if len(user_code) > 10000:
    raise ValueError("Code too long")

# 避免注入攻击
# 不要直接拼接用户输入到命令中
# 使用参数化的方式
```

### 4. 性能优化

#### 复用沙箱

```python
# 对于多个相关任务，复用沙箱
sandbox = Sandbox.create()

for task in tasks:
    result = sandbox.run_code(task.code)
    process_result(result)

sandbox.kill()
```

#### 并行处理

```python
# 对于独立任务，并行创建沙箱
import asyncio

async def process_task(task):
    async with Sandbox.create() as sandbox:
        result = await sandbox.run_code_async(task.code)
        return result

tasks = [process_task(t) for t in task_list]
results = await asyncio.gather(*tasks)
```

#### 预热环境

```python
# 提前安装依赖
sandbox = Sandbox.create()
sandbox.run_code("pip install numpy pandas")

# 创建快照
snapshot_id = sandbox.create_snapshot()

# 后续使用快照快速创建
fast_sandbox = Sandbox.from_snapshot(snapshot_id)
```

### 5. 日志和监控

```python
import logging

logger = logging.getLogger(__name__)

def execute_with_logging(code: str):
    logger.info(f"Creating sandbox")
    sandbox = Sandbox.create()

    try:
        logger.info(f"Executing code: {code[:100]}...")
        result = sandbox.run_code(code)

        if result.error:
            logger.error(f"Execution error: {result.error}")
        else:
            logger.info(f"Execution success: {len(result.logs.stdout)} bytes output")

        return result
    finally:
        sandbox.kill()
        logger.info("Sandbox destroyed")
```

---

## 故障排查

### 常见问题

#### 1. 沙箱创建失败

**问题：**
```python
SandboxException: Failed to create sandbox
```

**原因：**
- API Key 无效或过期
- 账号配额用尽
- 网络连接问题

**解决：**
```python
# 检查 API Key
import os
print(os.getenv('E2B_API_KEY'))

# 检查账号配额
# 访问 E2B 控制台查看使用情况

# 测试网络连接
import requests
response = requests.get('https://api.e2b.dev/health')
print(response.status_code)
```

#### 2. 代码执行超时

**问题：**
```python
TimeoutException: Execution timed out after 300 seconds
```

**解决：**
```python
# 增加超时时间
sandbox = Sandbox.create(timeout=600)

# 或优化代码性能
# 或拆分为多个小任务
```

#### 3. 文件不存在

**问题：**
```python
FileNotFoundError: /app/data.txt not found
```

**解决：**
```python
# 确保文件已上传
sandbox.upload_file("./data.txt", "/app/data.txt")

# 或检查文件路径
files = sandbox.filesystem.list("/app")
print([f.name for f in files])
```

#### 4. 依赖包缺失

**问题：**
```python
ModuleNotFoundError: No module named 'custom_package'
```

**解决：**
```python
# 安装依赖
sandbox.run_code("pip install custom_package")

# 或使用自定义模板（推荐）
# 在模板中预装所有依赖
```

#### 5. 内存不足

**问题：**
```python
MemoryError: Out of memory
```

**解决：**
```python
# E2B 沙箱有默认的内存限制
# 优化代码以减少内存使用
# 或分批处理数据

# 示例：分批处理
import pandas as pd

# 不推荐：一次性加载大文件
# df = pd.read_csv('huge_file.csv')

# 推荐：分块读取
for chunk in pd.read_csv('huge_file.csv', chunksize=10000):
    process(chunk)
```

### 调试技巧

#### 1. 详细日志

```python
# 打印详细输出
result = sandbox.run_code(code)
print(f"stdout: {result.logs.stdout}")
print(f"stderr: {result.logs.stderr}")
print(f"error: {result.error}")
```

#### 2. 交互式调试

```python
# 启动交互式进程
process = sandbox.process.start("python -i")

# 发送命令
process.send_stdin("import sys\n")
process.send_stdin("print(sys.version)\n")

# 获取输出
print(process.stdout)
```

#### 3. 检查环境

```python
# 检查 Python 版本
sandbox.run_code("import sys; print(sys.version)")

# 检查已安装的包
sandbox.run_code("pip list")

# 检查环境变量
sandbox.run_code("import os; print(os.environ)")

# 检查文件系统
files = sandbox.filesystem.list("/")
print([f.name for f in files])
```

---

## 定价

### 免费层

```yaml
免费额度：
  - 每月 100 小时沙箱时长
  - 基础模板访问
  - 社区支持

限制：
  - 单个沙箱最长 1 小时
  - 最多 5 个并发沙箱
  - 标准资源配额
```

### 付费层

#### Starter Plan

```yaml
价格: $20/月

包含：
  - 500 小时沙箱时长
  - 所有模板访问
  - 优先支持
  - 更高并发限制（50 个）
  - 更长运行时间（24 小时）

超出计费:
  - $0.04/小时
```

#### Pro Plan

```yaml
价格: $100/月

包含：
  - 3000 小时沙箱时长
  - 所有功能
  - 专属支持
  - 自定义模板
  - SLA 保证

超出计费:
  - $0.03/小时
```

#### Enterprise Plan

```yaml
价格: 联系销售

包含：
  - 无限沙箱时长
  - 私有部署
  - 专属团队支持
  - 定制开发
  - 合同和发票
```

### 计费说明

```yaml
计费单位：
  - 按秒计费，按分钟结算
  - 沙箱创建到销毁的时间

包含内容：
  - CPU 时间
  - 内存使用
  - 网络传输（有限额）
  - 存储（临时，沙箱销毁后清除）

不包含：
  - 外部 API 调用
  - 持久化存储（需单独购买）
```

---

## 集成示例

### 与 LangChain 集成

```python
from langchain.agents import Tool
from langchain.agents import initialize_agent
from langchain.llms import OpenAI
from e2b import Sandbox

def execute_python(code: str) -> str:
    """在 E2B 沙箱中执行 Python 代码"""
    with Sandbox.create() as sandbox:
        result = sandbox.run_code(code)
        if result.error:
            return f"Error: {result.error}"
        return result.logs.stdout

# 创建工具
python_tool = Tool(
    name="Python REPL",
    func=execute_python,
    description="执行 Python 代码。输入应该是有效的 Python 代码。"
)

# 初始化 Agent
llm = OpenAI(temperature=0)
agent = initialize_agent(
    [python_tool],
    llm,
    agent="zero-shot-react-description",
    verbose=True
)

# 使用
agent.run("计算 fibonacci(10) 的值")
```

### 与 AutoGPT 集成

```python
from e2b import Sandbox

class E2BExecutor:
    def __init__(self):
        self.sandbox = None

    def execute_python(self, code: str) -> str:
        """执行 Python 代码"""
        if not self.sandbox:
            self.sandbox = Sandbox.create()

        result = self.sandbox.run_code(code)
        return result.logs.stdout if not result.error else result.error

    def execute_shell(self, command: str) -> str:
        """执行 Shell 命令"""
        if not self.sandbox:
            self.sandbox = Sandbox.create()

        process = self.sandbox.process.start(command)
        process.wait()
        return process.stdout

    def cleanup(self):
        """清理资源"""
        if self.sandbox:
            self.sandbox.kill()
            self.sandbox = None

# 在 AutoGPT 中使用
executor = E2BExecutor()
result = executor.execute_python("import pandas; print(pandas.__version__)")
print(result)
executor.cleanup()
```

### Web 应用集成

```python
from flask import Flask, request, jsonify
from e2b import Sandbox
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/execute', methods=['POST'])
def execute_code():
    """代码执行 API"""
    try:
        code = request.json.get('code')
        language = request.json.get('language', 'python')

        if not code:
            return jsonify({'error': 'No code provided'}), 400

        logging.info(f"Executing {language} code: {code[:50]}...")

        # 创建沙箱并执行
        with Sandbox.create() as sandbox:
            if language == 'python':
                result = sandbox.run_code(code)
            elif language == 'javascript':
                result = sandbox.run_code(f"node -e '{code}'")
            else:
                return jsonify({'error': 'Unsupported language'}), 400

            return jsonify({
                'stdout': result.logs.stdout,
                'stderr': result.logs.stderr,
                'error': result.error
            })

    except Exception as e:
        logging.error(f"Execution error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

---

## 安全建议

### 1. API Key 管理

```bash
# ✅ 推荐：使用环境变量
export E2B_API_KEY="your_key"

# ❌ 不推荐：硬编码
# api_key = "sk_xxxx"  # 不要这样做！
```

### 2. 输入验证

```python
def safe_execute(user_code: str):
    # 验证代码长度
    if len(user_code) > 10000:
        raise ValueError("Code too long")

    # 检查危险操作（简单示例）
    dangerous_patterns = ['__import__', 'eval', 'exec']
    for pattern in dangerous_patterns:
        if pattern in user_code:
            raise ValueError(f"Dangerous operation detected: {pattern}")

    # 执行
    with Sandbox.create(timeout=60) as sandbox:
        return sandbox.run_code(user_code)
```

### 3. 超时设置

```python
# 始终设置合理的超时
sandbox = Sandbox.create(timeout=300)  # 5 分钟

# 防止无限循环
code = """
while True:
    pass  # 会在超时后被终止
"""
```

### 4. 资源限制

```python
# E2B 自动限制资源使用
# - CPU: 默认限制
# - 内存: 默认限制
# - 磁盘: 临时存储，有限额
# - 网络: 有带宽限制

# 企业版可以自定义配额
```

---

## 支持和帮助

### 文档和资源

- 📚 官方文档：https://e2b.dev/docs
- 💬 Discord 社区：https://discord.gg/e2b
- 📧 邮件支持：support@e2b.dev
- 🐛 问题反馈：https://github.com/e2b-dev/e2b/issues

### 状态页面

实时服务状态：https://status.e2b.dev

### 变更日志

最新更新：https://e2b.dev/changelog

---

## 附录

### A. 模板软件包清单

#### Base Template 完整清单

```yaml
Python 包（pip list）:
  - numpy==1.24.3
  - pandas==2.0.3
  - matplotlib==3.7.2
  - scipy==1.11.1
  - scikit-learn==1.3.0
  - requests==2.31.0
  - beautifulsoup4==4.12.2
  - lxml==4.9.3

系统包（apt list）:
  - git
  - curl
  - wget
  - vim
  - nano
  - jq
  - tmux
```

### B. 环境变量

```bash
# E2B 沙箱内的环境变量
USER=user
HOME=/home/user
PATH=/usr/local/bin:/usr/bin:/bin
PYTHON_VERSION=3.11.4
NODE_VERSION=18.17.0
```

### C. 资源限制

```yaml
默认配额：
  CPU: 2 核心
  内存: 4GB
  磁盘: 10GB（临时）
  网络: 100Mbps
  并发进程: 100

企业版：
  CPU: 可定制
  内存: 可定制
  磁盘: 可定制
  网络: 可定制
```

### D. API 速率限制

```yaml
免费版：
  - 100 请求/分钟
  - 1000 请求/小时

付费版：
  - 1000 请求/分钟
  - 10000 请求/小时

企业版：
  - 无限制（在合理范围内）
```

---

*文档版本：v1.0*
*最后更新：2025-11-27*
*基于公开信息整理，具体以官方文档为准*
