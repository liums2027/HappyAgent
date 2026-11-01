from agent import HappyAgent
from tools import list_files

agent = HappyAgent()
agent.add_tools([list_files])
result = agent.run("看下这个路径下有哪些文件：G:\\AIWorkSpace\\HappyCoding")
print(result)
