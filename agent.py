import os

from openai import OpenAI

class HappyAgent:
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com")
        self.max_step = 20
        self.memory = []




