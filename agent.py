import inspect
import json
import os
import traceback
from logging import error
from typing import Dict, Callable, List, Any
from unittest import result

from docstring_parser import parse
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageFunctionToolCall
from referencing import retrieval

from security import check_allow

type_mapping = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object"
}


def finish_chat(final_answer: str):
    """
    如果当前对话已经结束，必须调用这个方法来结束对话循环
    例如一个简单问答结束，或者一个循环任务结束，最终必须调用这个方法来结束循环
    :param final_answer: 最终给用户的回答
    :return: 最终给用户的回答
    """
    return final_answer


def _parse_tool(tool_call: ChatCompletionMessageFunctionToolCall):
    """
    {
      "id": "call_abc123XYZ",
      "type": "function",
      "function": {
        "name": "get_current_weather",
        "arguments": "{\"location\": \"Tokyo, Japan\", \"unit\": \"celsius\"}"
      }
    }
    :param tool_call:
    :return:
    """
    function_ = tool_call.function
    return tool_call.id, function_.name, function_.arguments


def _tool_schema(tool):
    """
    将一个方法解析成以下json schema格式
    tools = [
        {
            "type": "function",
            "function": {
                "name": "list_files",
                "description": "List files in a directory.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The directory path to list."
                        },
                        "recursive": {
                            "type": "boolean",
                            "description": "Whether to recursively list subdirectories."
                        }
                    },
                    "required": [],
                    "additionalProperties": False
                }
            }
        }
    ]
    :param tool:
    :return:
    """
    tool_json_schema: dict[str, Any] = {"type": "function"}
    functions = {"name": tool.__name__, "description": tool.__doc__}
    tool_json_schema["function"] = functions
    parameters: dict[str, Any] = {"type": "object", "additionalProperties": False}
    functions["parameters"] = parameters
    properties = {}

    required = []
    tool__parameters = inspect.signature(tool).parameters
    param_annotation_map = {}
    for name, param in tool__parameters.items():
        param_annotation_map[name] = type_mapping.get(param.annotation)
        if param.default == inspect.Parameter.empty:
            required.append(name)

    doc = parse(tool.__doc__)
    for param in doc.params:
        properties[param.arg_name] = {"type": param_annotation_map[param.arg_name], "description": param.description}
    parameters["required"] = required
    parameters["properties"] = properties

    return tool_json_schema


class HappyAgent:
    def __init__(self, work_space: str):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com")
        self.max_step = 20
        self.memory: List = []
        self.tool_map: Dict[str, Callable] = {}
        self.tools: list = []
        self.add_tools([finish_chat])
        self.white_list: list = [work_space]
        print("HappyAgent 已启动...")

    def run(self, prompt):
        print("开始执行任务...")
        self._add_memory("user", prompt)
        final_result = self._loop()
        return final_result

    def _loop(self):
        finish = False
        step = 0
        final_result = ""
        while not finish and step <= self.max_step:
            step += 1
            message = self._call_llm()
            self._add_memory("assistant", message.content, message.reasoning_content, message.tool_calls)
            finish, final_result = self._step(message.tool_calls)
        return final_result

    def _step(self, tool_call_list):
        finish = False
        final_result = ""
        if tool_call_list:
            for tool_call_json in tool_call_list:
                tool_call_id, name, arguments = _parse_tool(tool_call_json)
                if name != "finish_chat":
                    print(f"正在调用工具：{name}")
                result = self._call_tool(name, arguments)
                self._add_memory("tool", result, None, None, tool_call_id=tool_call_id)
                if name == 'finish_chat':
                    finish = True
                    final_result = result
        else:
            finish = True
        return finish, final_result

    def _add_memory(self, role, content, reasoning_content: str | None = None, tool_calls: list | None = None,
                    tool_call_id: str | None = None):
        content_ = {"role": role, "content": content}
        if reasoning_content:
            content_["reasoning_content"] = reasoning_content
        if tool_call_id:
            content_["tool_call_id"] = tool_call_id
        if tool_calls:
            content_["tool_calls"] = tool_calls
        self.memory.append(content_)

    def _call_tool(self, tool_name, params):
        if tool_name not in self.tool_map:
            return f"tool call error: {tool_name} not exists"
        tool = self.tool_map[tool_name]
        if tool_name == "finish_chat":
            return json.loads(params)["final_answer"]
        try:
            tool_params = json.loads(params)
            is_allowed, path = self._check_path_allowed(tool, tool_params)
            if not is_allowed:
                result = f"path not allowed: {path}"
            else:
                result = tool(**tool_params)
        except Exception as e:
            traceback.print_exc()
            result = f"tool call error:{e}"
        return json.dumps(result)

    def _check_path_allowed(self, tool, params):
        required_params = getattr(tool, "__required_path_params__")
        if required_params:
            for required_param in required_params:
                real_param = params.get(required_param)
                if not check_allow(self.white_list, real_param):
                    return False, real_param
            return True, None
        else:
            return True, None

    def _call_llm(self):
        response = self.client.chat.completions.create(
            model="deepseek-flash",
            messages=self.memory,
            reasoning_effort="high",
            tools=self.tools
        )
        return response.choices[0].message

    def add_tools(self, tool_list):
        for tool in tool_list:
            if inspect.isfunction(tool) or inspect.ismethod(tool):
                self.tool_map[tool.__name__] = tool
                tool_schema = _tool_schema(tool)
                self.tools.append(tool_schema)
            else:
                raise RuntimeError(f"{tool}注册失败")
