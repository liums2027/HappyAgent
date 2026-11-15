from pathlib import Path
import inspect
from pydantic import create_model, ValidationError


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


def model_from_func(func):
    """
    使用当前function创建一个model，用于给pydantic检验参数
    :param func: 需要检验参数的方法
    :return: model
    """
    sig = inspect.signature(func)
    fields = {}
    for name, p in sig.parameters.items():
        if p.kind in (p.VAR_KEYWORD, p.VAR_POSITIONAL):
            continue
        if name in ("self", "cls"):
            continue
        ann = p.annotation if p.annotation is not inspect.Parameter.empty else str
        default = ... if p.default is inspect.Parameter.empty else p.default
        fields[name] = (ann, default)
    return create_model(f"{func.__name__}Args", **fields)

def check_params_error(func, raw_json:str):
    """
    使用pydantic检查当前参数是否符合当前方法的要求
    :param func:被检查的方法
    :param raw_json:json参数
    :return:参数验证结果
    """
    Model = model_from_func(func)
    try:
        Model.model_validate_json(raw_json)
    except ValidationError as e:
        return e
    return None