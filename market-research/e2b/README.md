# E2B 测试环境

## 快速开始

### 1. 配置 API Key

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑 .env 文件，填入你的 API Key
# 从 https://e2b.dev 控制台获取
vim .env
```

### 2. 安装依赖

```bash
# 安装 E2B SDK
pip install e2b

# 如果使用 .env 文件，安装 python-dotenv
pip install python-dotenv
```

### 3. 运行测试

```bash
# 运行测试脚本
python test_e2b.py
```

## 配置方法

### 方法 1: 使用 `.env` 文件（推荐）

在项目目录下创建 `.env` 文件：
```bash
E2B_API_KEY="your_api_key_here"
```

然后在代码中加载：
```python
from dotenv import load_dotenv
load_dotenv()

from e2b import Sandbox
sandbox = Sandbox.create()
```

### 方法 2: 使用 shell 环境变量

在 `~/.zshrc` 或 `~/.bashrc` 中添加：
```bash
export E2B_API_KEY="your_api_key_here"
```

然后重新加载：
```bash
source ~/.zshrc  # 或 source ~/.bashrc
```

### 方法 3: 临时设置（仅当前会话）

```bash
export E2B_API_KEY="your_api_key_here"
python test_e2b.py
```

## 安全提醒

⚠️ **重要**:
- `.env` 文件已添加到 `.gitignore`，不会被提交到 git
- 不要在代码中硬编码 API Key
- 不要将 `.env` 文件分享或上传到公开仓库

## 文档

- [API-REFERENCE.md](API-REFERENCE.md) - **E2B SDK API 快速参考**（必看！）
- [AGENTS-COLLABORATION.md](AGENTS-COLLABORATION.md) - **Agents 协作模式指南**
- [AGENT-COMMUNICATION-ARCHITECTURE.md](AGENT-COMMUNICATION-ARCHITECTURE.md) - **Agent 通信架构说明**（重要！）
- [e2b-user-guide.md](e2b-user-guide.md) - 完整的 E2B 用户手册
- [e2b-solutions-analysis.md](e2b-solutions-analysis.md) - E2B 解决方案分析

## 示例代码

### 基础示例

```python
from e2b import Sandbox

# 创建沙箱
sandbox = Sandbox.create()

# 执行命令（注意：使用 commands.run，不是 run_code）
result = sandbox.commands.run("python3 -c \"print('Hello from E2B!')\"")
print(result.stdout)

# 清理
sandbox.kill()
```

### Agents 协作示例

查看完整示例：
- [quick_test_agents.py](quick_test_agents.py) - **快速测试**（推荐先运行）
- [orchestrator_pattern.py](orchestrator_pattern.py) - **协调器模式演示**（理解架构）
- [agents_collaboration.py](agents_collaboration.py) - 单沙箱内多 agents 协作
- [multi_sandbox_agents.py](multi_sandbox_agents.py) - 多沙箱间 agents 协作

```bash
# 快速测试
python3 quick_test_agents.py          # 3分钟快速演示

# 理解架构（重要！）
python3 orchestrator_pattern.py       # 展示数据如何通过协调器传递

# 完整演示
python3 agents_collaboration.py       # 演示 4 种协作模式
python3 multi_sandbox_agents.py       # 演示跨沙箱协作
```

### 🎯 重要概念

**Agents 之间如何通信？**

在 E2B 中，**agents 不直接通信**，而是通过**外部协调器**（你的 Python 脚本）传递数据：

```
Agent A → 协调器 → Agent B
```

**而不是：**
```
Agent A → 直接 → Agent B  ❌
```

**这意味着：**
- ✅ Agents 之间不需要网络互通
- ✅ E2B 基础设施不需要实现 sandbox 间通信
- ✅ 协调器充当"消息总线"的角色
- ✅ 简单、安全、可控

详细说明请查看 [AGENT-COMMUNICATION-ARCHITECTURE.md](AGENT-COMMUNICATION-ARCHITECTURE.md)
