import random
from revolver import Revolver
from config import players


class Game:
    def __init__(self, players):
        # 初始化牌组
        self.Cards = ["K"]*6 + ["Q"]*6 + ["A"]*6 + ["Joker"]*2
        self.currentCard = None


        self.gameRound = 0
        self.players = players
        self.playLog = []
        self.roundLog = []
        self.allRoundLog = []

        self.currentIndex = 0
        self.winner = None
        self.gameOver = False
        self.lastLossPlayer = random.randint(1,5)
        self.roundOver = False
        self.palyCardLog = None

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

        self.currentCards = self.Cards.copy()
        random.shuffle(self.currentCards)
        self.currentCard = random.choice(["K", "Q", "A"])
        self.giveCards()
        
        self.roundOver = False
        print(f"\n--- New Round: {self.gameRound} ---")
        print(f"\n--- This Round Card: {self.currentCard} ---")

    def CheckCard(self, player):
        """
        判断是否说谎
        """
        liar = False
        for card in self.allRoundLog[-1]["cards"]:
            hand = self.allRoundLog[-1]["originHand"]
            if hand[card] != self.currentCard and hand[card] != "Jorker":
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
                    action = player.PlayCard(self.roundLog, self.currentCard)
                    print(action)
                    if action["type"] == "question":
                        lastPlayer = self.players[(i + self.lastLossPlayer - 1)%playerNum]
                        if self.CheckCard(lastPlayer):
                            print("---Question success---")
                            if lastPlayer.revolver.fire():
                                print(f"---Fire success, {lastPlayer.name} die---")
                                self.players.pop((i + self.lastLossPlayer - 1)%playerNum)
                            else:
                                print(f"---Fire fial, {lastPlayer.name} still alive---")
                            self.lastLossPlayer = (i + self.lastLossPlayer)%playerNum
                            self.roundOver = True
                        else:
                            print("---Question fail---")
                            if player.revolver.fire():
                                print(f"---Fire success, {player.name} die---")
                                self.players.pop((i + self.lastLossPlayer)%playerNum)
                            else:
                                print(f"---Fire fial, {player.name} still alive---")
                            self.lastLossPlayer = (i + self.lastLossPlayer - 1)%playerNum
                            self.roundOver = True
                    else:
                        self.palyCardLog = {
                        "playerName":player.name,
                        "playCardNum":len(action["cards"]),
                        "playAction":action["playAction"]
                        }
                        self.roundLog.append(self.palyCardLog)
                        self.allRoundLog.append(action)
            if len(self.players) == 1:
                self.winner = self.players[0]
                self.gameOver = True
        print(f"---Game Over---\n ---Winner is {self.winner.name}!---")

if __name__ == "__main__":
    game = Game(players)
    game.GameStart()
                        

              
