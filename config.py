from player import *
from openai import OpenAI
from prompt import Prompt

players = []

deepseek_clinet = OpenAI(
            api_key="sk-6da9967819af43fa814f8789fce19d85",
            base_url="https://api.deepseek.com",
        )

qwen_client = OpenAI(
    api_key = "sk-317751e97e304e2abbb8f3c8368b7d16",
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
)

doubao_client = OpenAI(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key= "a874d8e5-5d4d-4ac5-9487-1c2222e7720c",   # 取值范围：enabled， disabled，auto
)

prompt = Prompt()

players.append(Player("deepseek1", "deepseek-chat", deepseek_clinet, prompt))
players.append(Player("deepseek2", "deepseek-chat", deepseek_clinet, prompt))
players.append(Player("deepseek3", "deepseek-chat", deepseek_clinet, prompt))
players.append(RealPlayer("Player1", "deepseek-chat", deepseek_clinet, prompt))
# players.append(Player("doubao1", "ep-20250612202125-pkq7n", doubao_client, prompt))
# players.append(Player("qwen1", "qwen-plus", qwen_client))
# players.append(Player("qwen2", "qwen-plus", qwen_client))
# players.append(Player("qwen3", "qwen-plus", qwen_client))
# players.append(Player("qwen4", "qwen-plus", qwen_client))
