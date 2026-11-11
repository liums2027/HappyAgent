from agent import HappyAgent
from tools import list_files, read_file

agent = HappyAgent(r"G:\AIWorkSpace\HappyCoding")
agent.add_tools([list_files, read_file])
result = agent.run("看下这个文件里的内容是什么：G:\\AIWorkSpace\\HappyCoding\\test_link\\not_link.txt")
print(result)
