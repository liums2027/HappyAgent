import os

from langchain_classic.tools.file_management import list_dir

from security import require_path


@require_path("path")
def list_files(path: str):
    """
    递归获取当前路径下的所有文件
    :param path: 路径
    :return: 一个列表，当前路径下的所有文件
    """
    result = []
    if os.path.islink(path):
        return result
    elif os.path.isfile(path):
        result.append(path)
    elif os.path.isdir(path):
        dir_list = os.listdir(path)
        if dir_list:
            for item in dir_list:
                if item.startswith("."):
                    continue
                temp = os.path.join(path, item)
                if os.path.islink(temp):
                    continue
                if os.path.isfile(temp):
                    result.append(temp)
                elif os.path.isdir(temp):
                    temp_result = list_files(temp)
                    if temp_result:
                        for p in temp_result:
                            result.append(list_files(p))

    return result


@require_path("path")
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
