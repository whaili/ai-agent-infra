import asyncio
import os
import time

from browser_use import Agent, BrowserSession
from browser_use.llm import ChatOpenAI
from e2b_code_interpreter import Sandbox

async def screenshot(agent: Agent):
  # 截图功能
  print("开始截图...")  
  page = await agent.browser_session.get_current_page()
  screenshot_bytes = await page.screenshot(full_page=True, type='png')
  # screenshot 方法返回图像的二进制数据，将其保存为 PNG 文件
  screenshots_dir = os.path.join(".", "screenshots")
  os.makedirs(screenshots_dir, exist_ok=True)
  screenshot_path = os.path.join(screenshots_dir, f"{time.time()}.png")
  with open(screenshot_path, "wb") as f:
    f.write(screenshot_bytes)
  print(f"截图已保存至 {screenshot_path}")

async def main():
    # 创建 E2B 沙箱实例
    sandbox = Sandbox.create(
        timeout=600,  # 超时时间（秒）
        template="browser-chromium",  # 该模板包含 chromium 浏览器，且暴露 9223 端口用于远程连接
    )

    try:
        # 获取沙箱的 Chrome 调试端口地址
        host = sandbox.get_host(9223) # 获取沙箱 9223 端口的地址
        cdp_url = f"https://{host}"
        print(f"Chrome 调试协议地址: {cdp_url}")

        # 创建 Browser-use 会话
        browser_session = BrowserSession(cdp_url=cdp_url) # 使用 cdp 协议连接远程沙箱中的浏览器
        await browser_session.start()
        print("Browser-use 会话创建成功")

        # 创建 AI Agent
        agent = Agent(
            task="去百度搜索 Browser-use 的相关信息，并总结出 3 个使用场景",
            llm=ChatOpenAI(
                api_key=os.getenv("LLM_API_KEY"),
                base_url=os.getenv("LLM_BASE_URL"),
                model=os.getenv("LLM_MODEL"),
                temperature=1
            ),
            browser_session=browser_session,
        )

        # 运行 Agent 任务
        print("开始执行 Agent 任务...")
        await agent.run(
          on_step_end=screenshot, # 在每个步骤结束时调用 screenshot 截图
        )

        # 关闭浏览器会话
        await browser_session.close()
        print("任务执行完成")

    finally:
        # 清理沙箱资源
        sandbox.kill()
        print("沙箱资源已清理")

if __name__ == "__main__":
    asyncio.run(main())