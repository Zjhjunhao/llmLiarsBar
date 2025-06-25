from revolver import Revolver
from openai import OpenAI, Client
import json
import random
import chromadb
from prompt import *

class Player:
    def __init__(self, name, model, client:OpenAI, prompt:Prompt, type="Agent"):
        self.type = type
        self.name = name        
        self.model = model
        self.hand = []
        self.revolver = Revolver()  
        self.is_out = False
        self.last_play = None
        self.client:OpenAI = client
        self.prompt = prompt
        self.role, self.role_usage_left = None, 0
    
    def BuildPrompt(self, currentCard, roundLog, hand, playNum):
        """构建大模型提示词"""
        #需要解释一下游戏规则
        prompt = self.prompt.final_prompt(currentCard, hand, roundLog, self.revolver.fire_times, playNum, self.name)
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

    def exit_round(self,):
        print("您已经成功出完牌且无人质疑，自动退出本轮，进入观战状态，本轮内不会开枪---")

class RealPlayer(Player):
    def __init__(self, name, model, client, prompt, type='Player'):
        # 这里的 client 和 prompt 是辅助生成完整 json的 
        super().__init__(name, model, client, prompt, type)
    
    def PlayCard(self, roundLog, currentCard, playNum):
        return {
            "type": "",
            "cards": [],
            "originHand": self.hand.copy(),
            "playAction": "",
            "reason": ""
        }
        print(f"\n---- 玩家 {self.name} 的回合 ----")
        print(f"当前需要出的牌: {currentCard}")
        print(f"你的手牌为:")
        for idx, card in enumerate(self.hand):
            print(f"{idx}: {card}")
        if roundLog: print(f"你的上家: {roundLog[-1]}")
        else: print("你是第一位玩家")
        print(f"你已经开枪次数：{self.revolver.fire_times}")
        while True:
            if roundLog: 
                raw_input_value = input("请选择操作（出牌/play/p/1 或 质疑/question/q/2）：")
            else:
                raw_input_value = input("请选择操作（出牌/play/p/1）：")
            action = self.parse_action_input(raw_input_value)
            if action:
                break
            print("无效输入，请重新输入。")
        cards = []
        if action == "play":
            while True:
                try:
                    card_indexes = input("请输入要打出的牌的索引（空格分隔，最多3张）: ").strip()
                    cards = [int(i) for i in card_indexes.split()]
                    if all(0 <= i < len(self.hand) for i in cards) and 1 <= len(cards) <= 3:
                        originHand = self.hand.copy()
                        for i in sorted(cards, reverse=True):
                            self.hand.pop(i)
                        break
                    else:
                        print("输入的索引无效，请重新输入。")
                except Exception as e:
                    print(f"输入错误: {e}")
        playaction = self.action_explaination(roundLog, currentCard, playNum, action, cards)
        if action == "question":
            return {
                "type": "question",
                "originHand": self.hand.copy(),
                "playAction": playaction, 
                "reason": "玩家主动质疑"}
        elif action == "play":
            return {
                "type": "play",
                "cards": cards,
                "originHand": originHand,
                "playAction": playaction, 
                "reason": "玩家主动出牌"}
        
    def parse_action_input(self, user_input: str) -> str:
        """
        根据玩家输入判断动作 play or question
        """
        user_input = user_input.strip().lower()

        play_set = {'p', 'play', '出', '出牌', '1'}
        question_set = {'q', 'question', '质疑', '问', '2'}

        if user_input in play_set:
            return 'play'
        elif user_input in question_set:
            return 'question'
        else:
            return None  # 表示无效输入
    
    def action_explaination(self, roundLog, currentCard, playNum, action, cards):
        """
        利用智能体生成对应的动作描述
        """
        try:
            prompt_text = prompt_prepare_for_reals(action, cards, currentCard, roundLog, self.hand, playNum)
            message = [{"role": "system", "content": "你是一个聪明的卡牌游戏助手，正在协助人类玩家进行一场名为「骗子酒馆」的扑克牌博弈。"}, 
                    {"role": "user", "content": prompt_text}]
            response = self.client.chat.completions.create(
                model=self.model,
                messages=message,
                stream=False,
                max_tokens=4096,
                response_format={"type": "json_object"})
            playaction = json.loads(response.choices[0].message.content)
            
            return playaction.get("playAction", "")
        except Exception as e:
            print(f"生成动作失败: {e}")
            if action == "play":
                fallback = "我咧嘴一笑，慢条斯理地推了几张牌出去。"
            elif action == "question":
                fallback = "我猛地一拍桌子，盯着上家喝道：“你骗人！”"
            return fallback
        
if __name__ == "__main__":
    prompt = Prompt()

    client = OpenAI(
            api_key="sk-6da9967819af43fa814f8789fce19d85",
            base_url="https://api.deepseek.com",
        )
    player = RealPlayer("deepseek", "deepseek-chat", client, prompt)

    #测试信息
    player.hand = ["Q", "K", "A", "A", "Q"]
    roundLog = None
    print(player.PlayCard(roundLog, "Q", 1))