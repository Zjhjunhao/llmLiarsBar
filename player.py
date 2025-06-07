from revolver import Revolver
from openai import OpenAI
import json
import random

class Player:
    def __init__(self, name, model, client):
        self.name = name        
        self.model = model
        self.hand = []
        self.revolver = Revolver()  
        self.is_out = False
        self.last_play = None
        self.client = client
        # client = OpenAI(
        #     api_key="sk-6da9967819af43fa814f8789fce19d85",
        #     base_url="https://api.deepseek.com",
        # )
    
    def BuildPrompt(self, currentCard, roundLog, hand):
        """构建大模型提示词"""
        #需要解释一下游戏规则
        prompt = f"""你正在参与一个卡牌游戏，当前规则如下：
            1. 本轮需要出的是：{currentCard}牌（Joker可以充当任意牌）
            2. 你的手牌：{hand}
            3. 当前轮次出牌记录：{roundLog if roundLog else "无"}
            4. 上一个玩家的剩余手牌数量：{roundLog[-1]["remainCard"] if roundLog else "你是第一个玩家"}
                    
            请从以下行动中选择：
            A) 出牌：选择1-3张手牌作为{currentCard}打出
            B) 质疑：对上一个玩家的出牌喊"Liar!"（如果你怀疑他们在说谎）
            
            规则：
            1.若你是第一个行动，你只能出牌
            2.若上一个玩家出完了牌,也就说上一个玩家的剩余手牌为0时，你只能质疑
            3.每人人有五张牌，目标牌在牌堆里一共有六张，且不一定都在场上，因此正确牌的数量时非常有限的，你可以估算场上已出的牌的数量判断上家说谎的概率
            4.你可以选择将非目标牌作为目标牌打出，但被质疑就将失败，若没被质疑，那就是你的机会，所以先打出非目标牌，保留自己的目标牌在后续使用也是一种策略，
            5.出多张牌能给对方巨大的心理压力，在合适的时机出更多的牌


            请用JSON格式回答，包含：
            - "action": "play" 或 "question"
            - "cards": [手牌索引]（如果是出牌）
            - "playAction": 出牌的行为，你可以简单描述你出牌的动作，比如随意丢出两张牌,或向下家轻蔑一笑，发挥想象描述你的出牌动作，用于迷惑对手出牌；注意，出牌动作不可透露自己出的牌型，只能透露出的牌的数量。
            - "reason": 你的决策理由，中文说明
        """

        return [
            {"role": "system", "content": "你是一个专业的卡牌游戏玩家，请根据游戏规则做出最佳决策。"},
            {"role": "user", "content": prompt}
        ]

    def PlayCard(self, roundLog, currentCard):
        """
        调用大模型决策行动
        roundLog: 轮次信息
        currentCard: 当前需要出的牌
        """
        try:
            messages = self.BuildPrompt(currentCard, roundLog, self.hand)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False,
                max_tokens=1024,
                response_format={"type": "json_object"}  # 要求返回JSON
            )

            decision = json.loads(response.choices[0].message.content)
            
            if decision["action"] == "question":
                return {"type": "question",
                        "reason": decision.get("reason", "")}
            
            elif decision["action"] == "play":
                # 验证卡牌索引是否有效
                cards = [int(i) for i in decision["cards"]]
                if all(0 <= i < len(self.hand) for i in cards) and 1 <= len(cards) <= 3:
                    originHand = self.hand.copy()
                    for i in sorted(cards, reverse=True):
                        self.hand.pop(i)
                    return {
                        "type": "play",
                        "cards": cards,
                        "originHand": originHand,
                        "playAction":decision.get("playAction", ""),
                        "reason": decision.get("reason", "")
                    }
            
            # 如果响应无效，默认随机出1张牌
            return {
                "type": "play",
                "cards": [random.randint(0, len(self.hand)-1)],
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