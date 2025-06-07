from player import Player
from openai import OpenAI

players = []

deepseek_clinet = OpenAI(
            api_key="sk-6da9967819af43fa814f8789fce19d85",
            base_url="https://api.deepseek.com",
        )
players.append(Player("deepseek1", "deepseek-chat", deepseek_clinet))
players.append(Player("deepseek2", "deepseek-chat", deepseek_clinet))