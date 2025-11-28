from dotenv import load_dotenv
from ppio_sandbox.code_interpreter import Sandbox

# The .env file should be located in the project root directory
# dotenv will automatically look for .env in the current working directory
load_dotenv()

# Or 
# You can set the environment variable in the command line
# export PPIO_API_KEY=sk_***

sbx = Sandbox.create()
execution = sbx.run_code("print('hello world')")
print(execution.logs)

files = sbx.files.list("/")
print(files)

# 不再使用时，关闭沙箱
sbx.kill()