import random

class Revolver:
    """
    左轮手枪类
    """
    def __init__(self, chambers=6):
        self.chambers = chambers
        self.bulletPosition = random.randint(1, chambers)
        self.currentChamber = random.randint(1, chambers)
    
    def fire(self):
        if self.currentChamber == self.bulletPosition:
            return True
        self.rotate()
        return False
    
    def rotate(self):
        self.currentChamber = (self.currentChamber % self.chambers) + 1

    
