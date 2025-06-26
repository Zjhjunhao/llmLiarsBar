import random, os, sys
from revolver import Revolver
from player import *
from config import players
from utils import Logger
from role_effects import *
from role import *


class Game:
    def __init__(self, players, file_name=r"role"):
        # 初始化牌组
        self.Cards = ["K"]*6 + ["Q"]*6 + ["A"]*6 + ["Joker"]*2
        self.currentCard = None

        self.gameRound = 0
        self.players = players
        self.hasRealPlayer = any(isinstance(p, RealPlayer) for p in players)
        self.playLog = []
        self.roundCards = 0 # 该回合中所有玩家出牌的总数
        self.roundLog = []
        self.allRoundLog = [] # 存放所有action
        self.playersinround = set()

        self.currentIndex = 0
        self.winner = None
        self.gameOver = False
        self.lastLossPlayer = random.randint(1,4)
        self.roundOver = False
        self.palyCardLog = None

        self.log_path = os.path.join(os.path.dirname(__file__), r"Liar's Bar Logs", f"{file_name}.log")
        sys.stdout = Logger(self.log_path)

        for player in self.players:
            player.revolver = Revolver()
            player.is_out = False

    def giveCards(self):
        """
        发牌
        """
        for player in self.players:
            player.hand = []
        for _ in range(5):
            for player in self.players:
                if self.Cards:
                    player.hand.append(self.currentCards.pop())

    def RoundStart(self):
        """
        轮次开始
        """
        self.gameRound += 1
        self.playLog.append(self.roundLog)
        self.roundLog = []
        self.roundCards = 0
        self.palyCardLog = None
        
        self.playersinround = set()
        for player in self.players:
            if not player.is_out:
                self.playersinround.add(player.name)

        self.currentCards = self.Cards.copy()
        random.shuffle(self.currentCards)
        self.currentCard = random.choice(["K", "Q", "A"])
        self.giveCards()
        
        self.roundOver = False
        print(f"\n--- New Round: {self.gameRound} ---")
        print(f"--- Survived Players: " + " | ".join(self.playersinround) +"---")
        print(f"--- This Round Card: {self.currentCard} ---")

    def CheckCard(self, player):
        """
        判断是否说谎
        """
        liar = False
        for card in self.allRoundLog[-1]["cards"]:
            hand = self.allRoundLog[-1]["originHand"]
            if hand[card] != self.currentCard and hand[card] != "Joker":
                liar = True
        return liar

    def GameStart(self):
        """
        游戏开始
        """
        while not self.gameOver:
            self.RoundStart()
            while not self.roundOver:
                playerNum = len(self.players)
                for i in range(playerNum):
                    player = self.players[(i + self.lastLossPlayer)%playerNum]
                    if player.name not in self.playersinround:
                        continue
                    print(f"--- {player.name}'s turn ---")
                    action = player.PlayCard(self.roundLog, self.currentCard, playerNum)
                    self.handle_print(action)
                    if action["type"] == "question":
                        prev_index = (i + self.lastLossPlayer - 1) % playerNum
                        while self.players[prev_index].name not in self.playersinround:
                            prev_index = (prev_index - 1) % playerNum
                        lastPlayer = self.players[prev_index]
                        if self.CheckCard(lastPlayer):
                            print("---Question success---")
                            if lastPlayer.revolver.fire():
                                print(f"---Fire success, {lastPlayer.name} die---")
                                self.players.pop((i + self.lastLossPlayer - 1)%playerNum)
                                self.lastLossPlayer = max(0, (i + self.lastLossPlayer)%playerNum-1) # index 移动一位
                            else:
                                print(f"---Fire fial, {lastPlayer.name} still alive---")
                                self.lastLossPlayer = (i + self.lastLossPlayer)%playerNum
                            self.roundOver = True
                        else:
                            print("---Question fail---")
                            if player.revolver.fire():
                                print(f"---Fire success, {player.name} die---")
                                self.players.pop((i + self.lastLossPlayer)%playerNum)
                                self.lastLossPlayer = min(playerNum-2, (i + self.lastLossPlayer)%playerNum-1)
                            else:
                                print(f"---Fire fial, {player.name} still alive---")
                                self.lastLossPlayer = (i + self.lastLossPlayer - 1)%playerNum
                            self.roundOver = True
                        break
                    else:
                        if len(self.playersinround) == 1: 
                            print(f"---Others has played all cards--")
                            if player.revolver.fire():
                                print(f"---Fire success, {player.name} die---")
                                self.players.pop((i + self.lastLossPlayer)%playerNum)
                            else:
                                print(f"---Fire fial, {player.name} still alive---")
                            self.lastLossPlayer = (i + self.lastLossPlayer)%playerNum
                            self.roundOver = True
                            break
                        if self.palyCardLog is not None and self.palyCardLog['remainCard'] == 0:
                            self.remove_player(self.palyCardLog['playerName'])  # 上家牌出完且没有人质疑，上家从该轮次中退出
                        remainCard = len(player.hand)
                        self.roundCards += len(action["cards"])
                        self.palyCardLog = {
                        "playerName":player.name,
                        "playCardNum":len(action["cards"]),
                        "playCardTotal":self.roundCards, 
                        "playAction":action["playAction"],
                        "remainCard":remainCard,
                        }
                        self.roundLog.append(self.palyCardLog)
                        self.save_logs(action)

            if len(self.players) == 1:
                self.winner = self.players[0]
                self.gameOver = True
            if len(self.players) == 0:
                self.winner = None
                self.gameOver = True
        if self.winner is None:
            print(f"---Game Over---\n ---Everyone perishes together, no one is spared!---")
        else:
            print(f"---Game Over---\n ---Winner is {self.winner.name}!---")

    def save_logs(self, action):
        self.allRoundLog.append(action)

    def remove_player(self, player_name):
        for player in self.players:
            if player.name == player_name and player.type == "Palyer":
                player.exit_round()
        self.playersinround.remove(player_name)
        return

    def handle_print(self, action:dict):
        action = action.copy()
        if self.hasRealPlayer: # 有真实玩家
            if "originHand" in action:
                del action["originHand"]
            if "cards" in action:
                action['cards'] = len(action["cards"])
            if "reason" in action:
                del action["reason"]
        print(action)

    
class GamewithRoles(Game):
    def __init__(self, players, file_name=r"role"):
        super().__init__(players, file_name)
        self.roles_pool = get_defined_roles()
        self.assign_roles_once()
    
    def assign_roles_once(self):
        """
        游戏开始前固定分配角色，角色在整局游戏中不变
        """
        if len(self.players) > len(self.roles_pool):
            raise ValueError("玩家数不能超过可用角色数")
        assigned_roles = random.sample(self.roles_pool, len(self.players))  # 乱序 + 不重复
        for player, role in zip(self.players, assigned_roles):
            player.mode = "role"
            player.role = role
            print(f"[角色分配] {player.name} → {role.name}")
            if player.role.timing == "开始时":
                player.role.try_trigger(self, player)

    def RoundStart(self,):
        """
        每轮开始时：仅重置角色技能使用次数，不重新分配角色
        """
        self.gameRound += 1
        self.playLog.append(self.roundLog)
        self.roundLog = []
        self.roundCards = 0
        self.palyCardLog = None

        self.playersinround = {p.name for p in self.players if not p.is_out}

        self.currentCards = self.Cards.copy()
        random.shuffle(self.currentCards)
        self.currentCard = random.choice(["K", "Q", "A"])
        self.giveCards()

        for player in self.players:
            if player.role:
                player.role.reset_round()
        self.roundOver = False
        print(f"\n--- New Round: {self.gameRound} ---")
        print(f"--- Survived Players: " + " | ".join(self.playersinround) + " ---")
        print(f"--- This Round Card: {self.currentCard} ---")

    def GameStart(self):
        """
        覆盖 GameStart，在出牌、质疑、开枪后等环节插入角色被动技能调用
        """
        while not self.gameOver:
            self.RoundStart()
            # 重置本轮结束标志
            self.roundOver = False
            
            while not self.roundOver:
                playerNum = len(self.players)
                for i in range(playerNum):
                    prev_index = (i + self.lastLossPlayer - 1) % playerNum
                    while self.players[prev_index].is_out or self.players[prev_index].name not in self.playersinround:
                        prev_index = (prev_index - 1) % playerNum
                    lastPlayer = self.players[prev_index]
                    player = self.players[(i + self.lastLossPlayer) % playerNum]
                    if player.name not in self.playersinround:
                        continue
                    print(f"--- {player.name}'s turn ---")

                    # 魔术师技能（出牌前）
                    if player.role and player.role.name == "魔术师":
                        player.role.try_trigger(self, player)
                    can_question = True
                    if lastPlayer.role and lastPlayer.role.name == "审问者":
                        # 尝试触发吓退效果（在这里就触发，而不是在被质疑时）
                        can_question = not lastPlayer.role.try_trigger(self, lastPlayer, player)
                    # 调用 PlayCard (不需修改签名)
                    action = player.PlayCard(self.roundLog, self.currentCard, playerNum, can_question)
                    self.handle_print(action)

                    if action["type"] == "question":
                        if self.CheckCard(lastPlayer):
                            print("---Question success---")
                            if lastPlayer.revolver.fire():
                                print(f"---Fire success, {lastPlayer.name} dies---")

                                # 赌徒技能（反杀）
                                if lastPlayer.role and lastPlayer.role.name == "赌徒":
                                    if len(self.playersinround) > 1:
                                        lastPlayer.role.try_trigger(self, lastPlayer, player)

                                self.players.pop(prev_index)
                                self.lastLossPlayer = max(0, (i + self.lastLossPlayer) % playerNum - 1)
                            else:
                                print(f"---Fire fail, {lastPlayer.name} survives---")

                                # 装弹师技能（fire后）
                                if lastPlayer.role and lastPlayer.role.name == "装弹师":
                                    lastPlayer.role.try_trigger(self, lastPlayer)

                                self.lastLossPlayer = (i + self.lastLossPlayer) % playerNum
                            self.roundOver = True
                        else:
                            print("---Question fail---")
                            if player.revolver.fire():
                                print(f"---Fire success, {player.name} dies---")

                                # 赌徒技能（反杀）
                                if player.role and player.role.name == "赌徒":
                                    if len(self.playersinround) > 1:
                                        player.role.try_trigger(self, player, lastPlayer)

                                self.players.pop((i + self.lastLossPlayer) % playerNum)
                                self.lastLossPlayer = min(playerNum - 2, (i + self.lastLossPlayer) % playerNum - 1)
                            else:
                                print(f"---Fire fail, {player.name} survives---")

                                # 装弹师技能（fire后）
                                if player.role and player.role.name == "装弹师":
                                    player.role.try_trigger(self, player)

                                self.lastLossPlayer = (i + self.lastLossPlayer - 1) % playerNum
                            self.roundOver = True
                        break
                       
                    elif action["type"] == "play":
                        if self.palyCardLog and self.palyCardLog['remainCard'] == 0:
                            self.remove_player(self.palyCardLog['playerName'])
                            
                        if len(self.playersinround) == 1:
                            print(f"---Others have played all cards---")
                            if player.revolver.fire():
                                print(f"---Fire success, {player.name} dies---")
                                self.players.pop((i + self.lastLossPlayer) % playerNum)
                            else:
                                print(f"---Fire fail, {player.name} survives---")

                                # 装弹师技能
                                if player.role and player.role.name == "装弹师":
                                    player.role.try_trigger(self, player)

                            self.lastLossPlayer = (i + self.lastLossPlayer) % playerNum
                            self.roundOver = True
                            break

                        remainCard = len(player.hand)
                        self.roundCards += len(action["cards"])
                        self.palyCardLog = {
                            "playerName": player.name,
                            "playCardNum": len(action["cards"]),
                            "playCardTotal": self.roundCards,
                            "playAction": action["playAction"],
                            "remainCard": remainCard,
                        }
                        self.roundLog.append(self.palyCardLog)
                        self.save_logs(action)

            if len(self.players) == 1:
                self.winner = self.players[0]
                self.gameOver = True
        print(f"---Game Over---\n ---Winner is {self.winner.name}!---")

if __name__ == "__main__":
    game = GamewithRoles(players)
    game.GameStart()
                        

              
