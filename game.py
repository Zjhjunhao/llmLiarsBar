import random, os, sys
from revolver import Revolver
from player import *
from config import players
from utils import Logger
from role import *
import datetime


class Game:
    def __init__(self, players, file_name=r"role"):
        self.version = "shell"
        # 玩家
        self.players = players
        # 是否有真人参与
        self.hasRealPlayer = any(isinstance(p, RealPlayer) for p in players)
        # 初始化牌组
        self.Cards = ["K"]*6 + ["Q"]*6 + ["A"]*6 + ["Joker"]*2
        # 游戏日志
        self.playLog = []
        # 轮次计数
        self.gameRound = 0
        # 当前目标牌
        self.currentCard = None
        # 该回合中所有玩家出牌的总数
        self.roundCards = 0  
        # 轮次信息
        self.roundLog = []
        # 所有轮次信息
        self.allRoundLog = []  
        # 该轮参与玩家
        self.playersinround = set()
        # 上一回合失败者
        self.lastLossPlayer = random.randint(0, 3)
        # 胜利者
        self.winner = None
        # 游戏是否结束
        self.gameOver = False
        # 轮次是否结束
        self.roundOver = False
        # 玩家出牌信息
        self.palyCardLog = None
        # 日志记录
        for player in self.players:
            player.revolver = Revolver()
            player.is_out = False

        if file_name is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"game_log_{timestamp}"
        self.log_path = os.path.join(os.path.dirname(__file__), r"Liar's Bar Logs", f"{file_name}.log")
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        sys.stdout = Logger(self.log_path)
        # 初始化玩家
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
        # 确定本轮参与的玩家
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
        if self.allRoundLog:
            last_action = self.allRoundLog[-1]
            for card in last_action["cards"]:
                hand = last_action["originHand"]
                if hand[card] != self.currentCard and hand[card] != "Joker":
                    liar = True
        return liar

    def GameStart(self):
        """
        游戏开始
        """
        while not self.gameOver:
            # 游戏未结束开始下一个轮次
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
                    # 若质疑
                    if action["type"] == "question":
                        prev_index = (i + self.lastLossPlayer - 1) % playerNum
                        while self.players[prev_index].name not in self.playersinround:
                            prev_index = (prev_index - 1) % playerNum
                        lastPlayer = self.players[prev_index]
                        if self.CheckCard(lastPlayer):
                            print("---Question success---")
                            if lastPlayer.revolver.fire():
                                print(f"---Fire success, {lastPlayer.name} die---")
                                # 终端版本，我们直接删除淘汰玩家，在ui界面为保证显示正确，我们并没有这么操作
                                self.players.remove(lastPlayer)
                                self.lastLossPlayer = max(0, (i + self.lastLossPlayer - 1)%playerNum - 1) # index 移动一位
                            else:
                                print(f"---Fire fial, {lastPlayer.name} still alive---")
                                self.lastLossPlayer = prev_index
                            self.roundOver = True
                        else:
                            print("---Question fail---")
                            if player.revolver.fire():
                                print(f"---Fire success, {player.name} die---")
                                self.players.remove(player)
                                self.lastLossPlayer =  max(0, (i + self.lastLossPlayer)%playerNum - 1) 
                            else:
                                print(f"---Fire fial, {player.name} still alive---")
                                self.lastLossPlayer = (i + self.lastLossPlayer) % playerNum
                            self.roundOver = True
                        break
                    else:
                        if len(self.playersinround) == 1: 
                            print(f"---Others has played all cards--")
                            if player.revolver.fire():
                                print(f"---Fire success, {player.name} die---")
                                self.players.remove(player)
                                self.lastLossPlayer = max(0, (i + 1 + self.lastLossPlayer)%playerNum - 1)
                            else:
                                print(f"---Fire fial, {player.name} still alive---") # 开枪的人下一轮先出牌
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
        print(f"---Game Over---\n ---Winner is {self.winner.name}!---")

    def save_logs(self, action):
        """保存对局记录"""
        self.allRoundLog.append(action)

    def remove_player(self, player_name):
        """当玩家在一轮游戏中出完所有的手牌后，退出当前轮次"""
        for player in self.players:
            if player.name == player_name and player.type == "Palyer":
                player.exit_round()
        self.playersinround.remove(player_name)
        return

    def handle_print(self, action:dict):
        """有真实玩家参与时，需要隐藏一些关键信息"""
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
            if player.role.name == "预言家":
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

        self.playersinround = {p.name for p in self.players}

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
                for i in range(playerNum):# 上家
                    prev_index = (i + self.lastLossPlayer - 1) % playerNum
                    while self.players[prev_index].name not in self.playersinround:
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
                                        counter = lastPlayer.role.try_trigger(self, lastPlayer, player)
                                        if counter:
                                            self.players.remove(player)
                                            self.lastLossPlayer = max(0, (i + 1 + self.lastLossPlayer) % playerNum - 2)
                                        else:
                                            self.lastLossPlayer = max(0, (i + self.lastLossPlayer) % playerNum - 1)                                                                     

                                self.players.remove(lastPlayer)
                            else:
                                print(f"---Fire fail, {lastPlayer.name} survives---")

                                # 装弹师技能（fire后）
                                if lastPlayer.role and lastPlayer.role.name == "装弹师":
                                    lastPlayer.role.try_trigger(self, lastPlayer)

                                self.lastLossPlayer = prev_index
                            self.roundOver = True
                        else:
                            print("---Question fail---")
                            if player.revolver.fire():
                                print(f"---Fire success, {player.name} dies---")

                                # 赌徒技能（反杀）
                                if player.role and player.role.name == "赌徒":
                                    if len(self.playersinround) > 1:
                                        counter = player.role.try_trigger(self, player, lastPlayer)
                                        if counter:
                                            self.players.remove(lastPlayer)
                                            self.lastLossPlayer = max(0, (i + 1 + self.lastLossPlayer) % playerNum - 2) # 下家
                                        else:
                                            self.lastLossPlayer = max(0, (i + 1 + self.lastLossPlayer) % playerNum - 2) # 下家
                                self.players.remove(player)
                                
                            else:
                                print(f"---Fire fail, {player.name} survives---")

                                # 装弹师技能（fire后）
                                if player.role and player.role.name == "装弹师":
                                    player.role.try_trigger(self, player)

                                self.lastLossPlayer = (i + self.lastLossPlayer) % playerNum # 上家
                            self.roundOver = True
                        break
                       
                    elif action["type"] == "play":
                        if self.palyCardLog and self.palyCardLog['remainCard'] == 0:
                            self.remove_player(self.palyCardLog['playerName'])
                            
                        if len(self.playersinround) == 1:
                            print(f"---Others have played all cards---")
                            if player.revolver.fire():
                                print(f"---Fire success, {player.name} dies---")
                                self.players.remove(player)
                                self.lastLossPlayer = min(len(players), (i + self.lastLossPlayer) % playerNum)
                            else:
                                print(f"---Fire fail, {player.name} survives---")
                                self.lastLossPlayer = (i + self.lastLossPlayer) % playerNum
                                # 装弹师技能
                                if player.role and player.role.name == "装弹师":
                                    player.role.try_trigger(self, player)

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
            if len(self.players) == 0:
                self.winner = None
                self.gameOver = True
        if self.winner is None:
            print(f"---Game Over---\n ---Everyone perishes together, no one is spared!---")
        else:
            print(f"---Game Over---\n ---Winner is {self.winner.name}!---")

if __name__ == "__main__":
    arg = "common"  
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
    if arg == "role":
        game = GamewithRoles(players)
    else:
        game = Game(players)
    game.GameStart()
                        