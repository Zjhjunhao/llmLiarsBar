from revolver import Revolver
from openai import OpenAI, Client
import json
import random
from prompt import prompt_prepare

class Player:
    def __init__(self, name, model, client:OpenAI):
        self.name = name        
        self.model = model
        self.hand = []
        self.revolver = Revolver()  
        self.is_out = False
        self.last_play = None
        self.client:OpenAI = client
        # client = OpenAI(
        #     api_key="sk-6da9967819af43fa814f8789fce19d85",
        #     base_url="https://api.deepseek.com",
        # )
    
    def BuildPrompt(self, currentCard, roundLog, hand, playNum):
        """构建大模型提示词"""
        #需要解释一下游戏规则
        prompt = prompt_prepare(currentCard, roundLog, hand, self.revolver.fire_times, playNum, self.name)
        return [
            {"role": "system", "content": "你是一个专业的卡牌游戏玩家，请根据游戏规则做出最佳决策。"},
            {"role": "user", "content": prompt}
        ]

    def PlayCard(self, roundLog, currentCard, playNum):
        """
        调用大模型决策行动
        roundLog: 轮次信息
        currentCard: 当前需要出的牌
        """
        try:
            messages = self.BuildPrompt(currentCard, roundLog, self.hand, playNum)
            response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=False,
                    max_tokens=4096,
                    response_format={"type": "json_object"})  # 要求返回JSON

            decision = json.loads(response.choices[0].message.content)
            originHand = self.hand.copy()
            
            if decision["action"] == "question":
                return {"type": "question",
                        "originHand": originHand,
                        "playAction":decision.get("playAction", ""),
                        "reason": decision.get("reason", "")}
            
            elif decision["action"] == "play":
                # 验证卡牌索引是否有效
                cards = [int(i) for i in decision["cards"]]
                if all(0 <= i < len(self.hand) for i in cards) and 1 <= len(cards) <= 3:
                    for i in sorted(cards, reverse=True):
                        self.hand.pop(i)
                    return {
                        "type": "play",
                        "cards": cards,
                        "originHand": originHand,
                        "playAction":decision.get("playAction", ""),
                        "reason": decision.get("reason", "")}
            
            # 如果响应无效，默认随机出1张牌
            return {
                "type": "play",
                "cards": [random.randint(0, len(self.hand)-1)],
                "originHand": originHand,
                "reason": "Fallback due to invalid response"
            }
            
        except Exception as e:
            print(f"AI决策错误: {e}")
            if random.random() < 0.5 and roundLog:
                return {"type": "question"}
            else:
                return {
                    "type": "play",
                    "cards": random.sample(range(len(self.hand)), min(3, len(self.hand))),
                    "reason": "Fallback due to error"
                }

if __name__ == "__main__":
    client = OpenAI(
            api_key="sk-6da9967819af43fa814f8789fce19d85",
            base_url="https://api.deepseek.com",
        )
    player = Player("deepseek", "deepseek-chat", client)

    #测试信息
    player.hand = ["Q", "K", "A", "A", "Q"]
    roundLog = None
    print(player.PlayCard(roundLog, "Q"))