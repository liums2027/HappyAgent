import os


def list_files(path: str):
    """
    递归获取当前路径下的所有文件
    :param path: 路径
    :return: 一个列表，当前路径下的所有文件
    """
    result = []
    if os.path.isfile(path):
        result.append(path)
    elif os.path.isdir(path):
        dir_list = os.listdir(path)
        if dir_list:
            for item in dir_list:
                if item.startswith("."):
                    continue
                temp = os.path.join(path, item)
                if os.path.isfile(temp):
                    result.append(temp)
                elif os.path.isdir(temp):
                    temp_result = list_files(temp)
                    if temp_result:
                        result.append(temp_result)
    return result

def read_file(path: str):
    """
    读取当前文件的所有内容，如果是文件夹则返回为空
    :param path: 文件路径
    :return: 文件内容
    """
    if os.path.isdir(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return content
