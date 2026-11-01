from agent import HappyAgent
from tools import list_files, read_file

agent = HappyAgent()
agent.add_tools([list_files, read_file])
result = agent.run("看下这个路径下有哪些文件：G:\\AIWorkSpace\\HappyCoding, 如果有一个叫test文件，看下这个文件里面的内容是什么？")
print(result)
