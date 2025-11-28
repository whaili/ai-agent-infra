import time
from e2b_desktop import Sandbox

# 创建虚拟桌面实例
desktop = Sandbox.create()

# 启动桌面流
desktop.stream.start()

# 获取可交互的 VNC 访问地址
url = desktop.stream.get_url()
print(url)
# 输出示例：
# 可以通过浏览器打开下面的链接，与虚拟桌面进行交互。您也可以将这个地址集成到应用中。
# https://6080-igocd05ju4yp564wxbgz0-66280ac2.sandbox.ppio.cn/vnc.html?autoconnect=true&resize=scale

# 获取只读模式的 VNC 访问地址（禁用用户交互）
url_readonly = desktop.stream.get_url(view_only=True)
print(url_readonly)
# 输出示例：
# 可以通过浏览器打开下面的链接，查看虚拟桌面（只读模式）。您也可以将这个地址集成到应用中。
# https://6080-igocd05ju4yp564wxbgz0-66280ac2.sandbox.ppio.cn/vnc.html?autoconnect=true&view_only=true&resize=scale

# 等待用户按下 Ctrl+C 来停止程序
try:
    print("桌面流已启动，按 Ctrl+C 停止程序...")
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\n程序被中断，正在清理资源...")

# 清理资源
desktop.stream.stop()  # 停止流
desktop.kill()        # 销毁沙箱