import inspect
import os
from codecs import namereplace_errors
from typing import Dict, Callable, List, Any
from docstring_parser import parse
import json

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageFunctionToolCall

type_mapping = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object"
}

def finish_chat():
    """
    如果当前对话已经结束，必须调用这个方法来结束对话循环
    例如一个简单问答结束，或者一个循环任务结束，最终必须调用这个方法来结束循环
    返回一个布尔值True
    :return: 一个布尔值，True
    """
    return True


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
    parameters: dict[str,Any] = {"type": "object", "additionalProperties": False}
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
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com")
        self.max_step = 20
        self.memory: List = []
        self.tool_map: Dict[str, Callable] = {}
        self.tools: list = []
        self.add_tools([finish_chat])

    def run(self, prompt):
        self._add_memory("user", prompt)
        self._loop()
        return self.memory

    def _loop(self):
        finish = False
        step = 0
        while not finish and step <= self.max_step:
            step += 1
            message = self._call_llm()
            self._add_memory("assistant", message.content, message.reasoning_content, message.tool_calls)
            finish = self._step(message.content, message.reasoning_content, message.tool_calls)

    def _step(self, content, reasoning_content, tool_call_list):
        finish = False
        if tool_call_list:
            for tool_call_json in tool_call_list:
                tool_call_id, name, arguments = _parse_tool(tool_call_json)
                if name == 'finish_chat':
                    finish = True
                    break
                result = self._call_tool(name, arguments, tool_call_id)
                self._add_memory("tool", result, None, None, tool_call_id = tool_call_id)

        if content:
            self._add_memory("assistant", content, reasoning_content)

        return finish

    def _add_memory(self, role, content, reasoning_content: str| None= None, tool_calls:list|None = None, tool_call_id: str | None = None):
        content_ = {"role": role, "content": content}
        if reasoning_content:
            content_["reasoning_content"] = reasoning_content
        if tool_call_id:
            content_["tool_call_id"] = tool_call_id
        if tool_calls:
            content_["tool_calls"] = tool_calls
        self.memory.append(content_)

    def _call_tool(self, tool_name, params, id1):
        tool = self.tool_map[tool_name]
        if tool:
            result = tool(**json.loads(params))
            return json.dumps(result)
        else:
            return "tool call error"

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
