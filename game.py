import random
from revolver import Revolver
import config

class Game:
    def __init__(self, config):
        # 初始化牌组
        self.Cards = ["K"]*6 + ["Q"]*6 + ["A"]*6 + ["Joker"]*2
        self.currentCard = None


        self.gameRound = 0
        self.players = config.players
        self.playLog = []
        self.roundLog = []

        self.currentIndex = 0
        self.winner = None
        self.gameOver = False
        self.LastLossPlayer = random.randint(1,5)
        self.roundOver = False

        for player in self.players:
            player.revolver = Revolver()
            player.is_out = False

    def giveCards(self):
        """
        发牌
        """
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

        self.currentCards = self.full_deck.copy()
        random.shuffle(self.currentCards)
        self.currentCard = random.choice(["K", "Q", "A"])
        self.giveCards()
        
        self.roundOver = False
        print(f"\n--- New Roud: {self.gameRound} ---")

    def CheckCard(self, player):
        """
        判断是否说谎
        """
        liar = False
        for card in player.roundCard:
            if card != self.currentCard and card != "Jorker":
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
                    player = self.players[(i + self.LastLossPlayer)%playerNum]
                    player.PlayCard(self.roundLog)
                    if player.isQuestion:
                        if self.CheckCard(player):
                            if self.players[(i + self.LastLossPlayer - 1)%playerNum].revolver.fire():
                                self.players.pop((i + self.LastLossPlayer - 1)%playerNum)
                            self.LastLossPlayer = (i + self.LastLossPlayer)%playerNum
                            self.roundOver = True
                        else:
                            if player.revolver.fire():
                                self.players.pop((i + self.LastLossPlayer)%playerNum)
                            self.LastLossPlayer = (i + self.LastLossPlayer - 1)%playerNum
                            self.roundOver = True
                    else:
                        self.roundLog.append(player.PalyCardLog())
            if len(self.players) == 1:
                self.winner = self.players[0]
                self.gameOver = True
        print(f"---Game Over---\n ---Winner is {self.winner.name}!---")

if __name__ == "__main__":
    game = Game(config)
    game.GameStart()
                        

              
