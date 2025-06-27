from player import *
from role import *

class Game:
    """
    ui版本对应的游戏类
    """
    def __init__(self, players, ui, file_name=None):
        self.version = "ui"
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
        # 当前回合玩家
        self.currentIndex = random.randint(0, 3)
        # 胜利者
        self.winner = None
        # 游戏是否结束
        self.gameOver = False
        # 轮次是否结束
        self.roundOver = False
        # 玩家出牌信息
        self.palyCardLog = None
        # 初始化玩家
        for player in self.players:
            player.revolver = Revolver()
            player.is_out = False
        # ui界面
        self.ui = ui  

    def giveCards(self):
        """
        发牌
        """
        for player in self.players:
            player.hand = []
        for _ in range(5):
            for player in self.players:
                if self.currentCards:
                    player.hand.append(self.currentCards.pop())
        
        # 更新玩家手牌显示
        self.ui.update_player_cards()  

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
        self.ui.log_action(f"\n--- 新轮次: {self.gameRound} ---")
        self.ui.log_action(f"--- 目前幸存玩家：" + " | ".join(self.playersinround) + " ---")
        self.ui.log_action(f"--- 本轮目标牌: {self.currentCard} ---")

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

    def process_action(self, action):
        """
        处理玩家动作
        """
        playerNum = len(self.players)
        i = self.currentIndex
        player = self.players[i]
        
        if action["type"] == "question":
            prev_index = (i - 1) % playerNum
            while self.players[prev_index].is_out or self.players[prev_index].name not in self.playersinround:
                prev_index = (prev_index - 1) % playerNum
            lastPlayer = self.players[prev_index]
            
            self.ui.log_action(f"--- {player.name} 质疑 {lastPlayer.name} ---")
            is_lying = self.CheckCard(lastPlayer)
            
            if is_lying:
                self.ui.log_action("--- 质疑成功 ---")
                self.currentIndex = i % len(self.players)
                self.lastLossPlayer = i % len(self.players)
                if lastPlayer.revolver.fire():
                    self.ui.log_action(f"--- {lastPlayer.name} 中弹出局 ---")
                    lastPlayer.is_out = True
                else:
                    self.ui.log_action(f"--- {lastPlayer.name} 未中弹 ---")

            else:
                self.ui.log_action("--- 质疑失败 ---")
                self.currentIndex = prev_index
                self.lastLossPlayer = prev_index
                if player.revolver.fire():
                    self.ui.log_action(f"--- {player.name} 中弹出局 ---")
                    player.is_out = True
                else:
                    self.ui.log_action(f"--- {player.name} 未中弹 ---")
            
            self.palyCardLog = {
                "playerName": player.name,
                "action":"question",
                "playAction": action["playAction"],
                "remainCard": len(player.hand),
            }

            self.ui.update_play_log(self.palyCardLog)  
            self.roundOver = True
            self.ui.update_player_status()  # 更新玩家状态
        elif action["type"] == "play":
            # 正常出牌逻辑
            if self.palyCardLog is not None and self.palyCardLog['remainCard'] == 0:
                self.remove_player(self.palyCardLog['playerName']) # 上一位玩家退出游戏
            if len(self.playersinround) == 1:
                self.ui.log_action(f"--- 其他玩家已经全部出完牌 ---")
                if player.revolver.fire():
                    self.ui.log_action(f"--- {player.name} 中弹出局 ---")
                    player.is_out = True
                    pro_index = (i+1) % playerNum  # 找下家
                    while self.players[pro_index].is_out:
                        pro_index = (pro_index + 1) % playerNum
                    self.currentIndex = pro_index
                    self.lastLossPlayer = pro_index
                else:
                    self.ui.log_action(f"--- {player.name} 未中弹 ---")
                    self.currentIndex = i % len(self.players)
                    self.lastLossPlayer = i % len(self.players)
                self.roundOver = True
                self.ui.update_player_status()
                return 
            

            cards_played = len(action["cards"])
            self.roundCards += cards_played
            
            # 更新日志信息
            self.palyCardLog = {
                "playerName": player.name,
                "action":"play",
                "playCardNum": cards_played,
                "playCardTotal": self.roundCards,
                "playAction": action["playAction"],
                "remainCard": len(player.hand),
            }
            
            self.roundLog.append(self.palyCardLog)
            self.save_logs(action)
            self.ui.update_play_log(self.palyCardLog)  # 更新出牌日志
        
        # 检查游戏是否结束
        remaining_players = [p for p in self.players if not p.is_out]
        if len(remaining_players) == 1:
            self.winner = remaining_players[0]
            self.gameOver = True
            self.ui.log_action(f"--- 游戏结束，获胜者是 {self.winner.name} ---")
            return
        
        # 检查轮次是否结束
        if len(self.playersinround) <= 1 or self.roundOver:
            self.roundOver = True
            self.ui.log_action("--- 轮次结束 ---")
            # 重置轮次相关状态
            self.currentIndex = self.lastLossPlayer  # 下一轮从lastLossPlayer开始
            return
        
        # 自动切换到下一个玩家
        self.currentIndex = (self.currentIndex + 1) % len(self.players)
        while self.players[self.currentIndex].is_out:
            self.currentIndex = (self.currentIndex + 1) % len(self.players)
            
    def GameStart(self):
        """
        游戏开始
        """
        self.ui.log_action("--- 游戏开始 ---")
        #self.RoundStart()  
        self.ui.root.update()  # 强制UI更新

    def remove_player(self, player_name):
        for player in self.players:
            if player.name == player_name and player.type == "Palyer":
                player.exit_round()
        self.playersinround.remove(player_name)
        return

    def save_logs(self, action):
        self.allRoundLog.append(action)


class GamewithRole(Game):
    def __init__(self, players, ui, file_name=None):
        super().__init__(players, ui, file_name)
        self.roles_pool = get_defined_roles()
        self.assign_roles_once()

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
                player.role.reset_round()
        
        self.currentCards = self.Cards.copy()
        random.shuffle(self.currentCards)
        self.currentCard = random.choice(["K", "Q", "A"])
        self.giveCards()
        
        self.roundOver = False
        self.ui.log_action(f"\n--- 新轮次: {self.gameRound} ---")
        self.ui.log_action(f"--- 目前幸存玩家：" + " | ".join(self.playersinround) + " ---")
        self.ui.log_action(f"--- 本轮目标牌: {self.currentCard} ---")

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
            if self.ui.hide_other_info or self.hasRealPlayer:
                self.ui.log_action(f"[信息已屏蔽]")
            else:
                self.ui.log_action(f"[角色分配] {player.name} → {role.name}")
            if player.role.name == "预言家":
                player.role.try_trigger(self, player)

    def process_action(self, action):
        """
        处理玩家动作
        """
        playerNum = len(self.players)
        i = self.currentIndex
        player = self.players[i]
        
        if action["type"] == "question":
            prev_index = (i - 1) % playerNum
            while self.players[prev_index].is_out or self.players[prev_index].name not in self.playersinround:
                prev_index = (prev_index - 1) % playerNum
            lastPlayer = self.players[prev_index]
            
            self.ui.log_action(f"--- {player.name} 质疑 {lastPlayer.name} ---")
            is_lying = self.CheckCard(lastPlayer)
            
            if is_lying:
                self.ui.log_action("--- 质疑成功 ---")
                self.currentIndex = prev_index
                self.lastLossPlayer = prev_index
                if lastPlayer.revolver.fire():
                    self.ui.log_action(f"--- {lastPlayer.name} 中弹出局 ---")
                    lastPlayer.is_out = True
                    # 赌徒技能（反杀）
                    if lastPlayer.role and lastPlayer.role.name == "赌徒":
                        if len(self.playersinround) > 1:
                            counter = lastPlayer.role.try_trigger(self, lastPlayer, player)
                            if counter: 
                                player.is_out = True
                                if len([pl for pl in self.players if not pl.is_out]) > 1:
                                    pro_index = (i+1) % playerNum
                                    while self.players[pro_index].is_out: # 将要进入下一轮游戏
                                        pro_index = (pro_index + 1) % playerNum
                                    self.currentIndex = pro_index
                                    self.lastLossPlayer = pro_index
                else:
                    self.ui.log_action(f"--- {lastPlayer.name} 未中弹 ---")
                    # 装弹师技能（fire后）
                    if lastPlayer.role and lastPlayer.role.name == "装弹师":
                        lastPlayer.role.try_trigger(self, lastPlayer)
            else:
                self.ui.log_action("--- 质疑失败 ---")
                self.currentIndex = i
                self.lastLossPlayer = i
                if player.revolver.fire():
                    self.ui.log_action(f"--- {player.name} 中弹出局 ---")
                    player.is_out = True
                    # 赌徒技能（反杀）
                    if player.role and player.role.name == "赌徒":
                        if len(self.playersinround) > 1:
                            counter = player.role.try_trigger(self, player, lastPlayer)
                            if counter:
                                lastPlayer.is_out = True
                                if len([pl for pl in self.players if not pl.is_out]) > 1:
                                    pro_index = (i+1) % playerNum
                                    while self.players[pro_index].is_out:
                                        pro_index = (pro_index + 1) % playerNum
                                    self.currentIndex = pro_index
                                    self.lastLossPlayer = pro_index
                                
                else:
                    self.ui.log_action(f"--- {player.name} 未中弹 ---")
                    # 装弹师技能（fire后）
                    if player.role and player.role.name == "装弹师":
                        player.role.try_trigger(self, player)
            
            self.palyCardLog = {
                "playerName": player.name,
                "action":"question",
                "playAction": action["playAction"],
                "remainCard": len(player.hand),
            }

            self.ui.update_play_log(self.palyCardLog)  
            self.roundOver = True
            self.ui.update_player_status()  # 更新玩家状态

        elif action["type"] == "play":
            # 正常出牌逻辑
            if self.palyCardLog is not None and self.palyCardLog['remainCard'] == 0:
                self.remove_player(self.palyCardLog['playerName']) # 上一位玩家退出游戏

            if len(self.playersinround) == 1:
                self.ui.log_action(f"--- 其他玩家已经全部出完牌 ---")
                if player.revolver.fire():
                    self.ui.log_action(f"--- {player.name} 中弹出局 ---")
                    player.is_out = True
                    pro_index = (i+1) % playerNum  # 找下家
                    while self.players[pro_index].is_out:
                        pro_index = (pro_index + 1) % playerNum
                    self.currentIndex = pro_index
                    self.lastLossPlayer = pro_index
                else:
                    self.ui.log_action(f"--- {player.name} 未中弹 ---")
                    self.currentIndex = i % len(self.players)
                    self.lastLossPlayer = i % len(self.players)
                self.roundOver = True
                self.ui.update_player_status()
                return 
            
            cards_played = len(action["cards"])
            self.roundCards += cards_played

            # 更新日志信息
            self.palyCardLog = {
                "playerName": player.name,
                "action":"play",
                "playCardNum": cards_played,
                "playCardTotal": self.roundCards,
                "playAction": action["playAction"],
                "remainCard": len(player.hand),
            }
            
            self.roundLog.append(self.palyCardLog)
            self.save_logs(action)
            self.ui.update_play_log(self.palyCardLog)  # 更新出牌日志
        
        # 检查游戏是否结束
        remaining_players = [p for p in self.players if not p.is_out]

        if len(remaining_players) == 0:
            self.winner = None
            self.gameOver = True
            self.ui.log_action(f"--- 游戏结束，所有玩家都已阵亡，没有获胜者 ---")

        if len(remaining_players) == 1:
            self.winner = remaining_players[0]
            self.gameOver = True
            self.ui.log_action(f"--- 游戏结束，获胜者是 {self.winner.name} ---")
            return
        
        # 检查轮次是否结束
        if len(self.playersinround) <= 1 or self.roundOver:
            self.roundOver = True
            self.ui.log_action("--- 轮次结束 ---")
            # 重置轮次相关状态
            self.currentIndex = self.lastLossPlayer  # 下一轮从lastLossPlayer开始
            return
    
        # 自动切换到下一个玩家
        self.currentIndex = (self.currentIndex + 1) % len(self.players)
        while self.players[self.currentIndex].is_out:
            self.currentIndex = (self.currentIndex + 1) % len(self.players)
        return