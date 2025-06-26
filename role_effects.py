"""
该文件存放角色和其技能
"""

import random

# 魔术师技能：将一张非目标牌临时变成目标牌
def magician_illusion(game, player):
    # 筛选可被转换的牌
    if random.random() < player.role.trigger_chance:
        convertible_indexes = [i for i, c in enumerate(player.hand)
                            if c != game.currentCard and c != "Joker"]
        if not convertible_indexes:
            return
        index_to_change = random.choice(convertible_indexes)
        original_card = player.hand[index_to_change]
        player.hand[index_to_change] = game.currentCard
        if not game.hasRealPlayer:
            print(f"🎩 魔术师戏法：{original_card} 被视为 {game.currentCard}")

# 审问者技能：被质疑前，有概率吓退质疑者
def intimidate(game, target_player, challenger_player, posibility=0.3):
    if random.random() < target_player.role.trigger_chance:
        if not game.hasRealPlayer:
            print(f"😱 审问者 {target_player.name} 吓退了 {challenger_player.name}！")
        return True  # 表示质疑取消
    return False

# 赌徒技能：被开枪后，有50%概率同归于尽
def gambler_revenge(game, gambler, shooter,):
    if random.random() < gambler.role.trigger_chance:
        if not game.hasRealPlayer:
            print(f"🎲 赌徒 {gambler.name} 同归于尽带走了 {shooter.name}！")
        game.players.remove(shooter)

# 装弹师技能：每次未被子弹击中时，有 50% 几率打乱当前子弹顺序。
def loader_reshuffle(game, player):
    if random.random() < player.role.trigger_chance:
        player.revolver.bulletPosition = random.randint(1, 6)
        if not game.hasRealPlayer:
            print(f"🔄 装弹师技能触发：{player.name} 重置了子弹顺序")
    
# 预言家技能：每轮开始有 40% 概率提前知道当前子弹排列。
def seer_peek_bullet(game, player):
    if random.random() < player.role.trigger_chance:
        player.revolver_state = (player.revolver.currentChamber, player.revolver.bulletPosition)
        player.role.message["revolver_state"] = (player.revolver.currentChamber, player.revolver.bulletPosition)
        if not game.hasRealPlayer:
            print(f"🔍 预言家技能触发：{player.name} 弹针位置/子弹位置为{player.revolver_state}")