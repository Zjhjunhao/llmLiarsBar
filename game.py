import random, os, sys
from revolver import Revolver
from config import players
from utils import Logger


class Game:
    def __init__(self, players, file_name=r"Demo_doubao"):
        # 初始化牌组
        self.Cards = ["K"]*6 + ["Q"]*6 + ["A"]*6 + ["Joker"]*2
        self.currentCard = None

        self.gameRound = 0
        self.players = players
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
        self.playersinround = [player.name for player in self.players]

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
                    print(action)
                    if action["type"] == "question":
                        lastPlayer = self.players[(i + self.lastLossPlayer - 1)%playerNum]
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
                            self.playersinround.remove(self.palyCardLog['playerName']) # 上家牌出完且没有质疑，上家从该轮次中退出
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
        self.allRoundLog.append(action)


if __name__ == "__main__":
    game = Game(players)
    game.GameStart()
                        

              
