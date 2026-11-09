import functools
from pathlib import Path


def require_path(*param_names):
    def decorator(func):
        func.__required_path_params__ = param_names
        return func

    return decorator

def check_allow(white_list: list[str], target: str):
    """
    检查当前路径是否处于白名单文件夹下
    :param white_list:白名单路径
    :param target:当前路径
    :return:True可用，False不可用
    """
    try:
        resolve_path = Path(target).resolve()
    except (OSError, ValueError):
        return False

    for path in white_list:
        if not path:
            continue
        try:
            allowed = Path(path).resolve()
        except (OSError, ValueError):
            continue

        if resolve_path.is_relative_to(allowed):
            return True
    return False