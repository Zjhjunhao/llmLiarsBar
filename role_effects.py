"""
该文件存放角色和其技能
"""

import random
# 魔术师技能：将一张非目标牌临时变成目标牌
def magician_illusion(game, player):
    if random.random() < player.role.trigger_chance:
        convertible_indexes = [i for i, c in enumerate(player.hand)
                            if c != game.currentCard and c != "Joker"]
        if not convertible_indexes:
            return
        index_to_change = random.choice(convertible_indexes)
        original_card = player.hand[index_to_change]
        player.hand[index_to_change] = game.currentCard
        if game.version == "shell":
            if not game.hasRealPlayer:
                print(f"{player.name} 触发 🎩 魔术师技能：{original_card} 被视为 {game.currentCard}")
        elif game.version == "ui":
            if game.ui.hide_other_info:
                game.ui.log_action(f"[信息已屏蔽]")
            else:
                print(f"{player.name} 触发 🎩 魔术师技能：{original_card} 被视为 {game.currentCard}")
    else:
        if not game.hasRealPlayer:
            if game.version == "shell":
                print(f"{player.name} 尝试触发 🎩 魔术师技能，但没有成功。")
            elif game.version == "ui":
                if not game.ui.hide_other_info:
                    print(f"{player.name} 尝试触发 🎩 魔术师技能，但没有成功。")
                else:
                    game.ui.log_action(f"[信息已屏蔽]")

# 审问者技能：被质疑前，有概率吓退质疑者
def intimidate(game, target_player, challenger_player=None):
    if challenger_player is None:
        name = "他的下家"
    else:
        name = challenger_player.name
    if random.random() < target_player.role.trigger_chance:
        if not game.hasRealPlayer:
            if game.version == "shell":
                print(f"{target_player.name} 触发 😱 审问者技能：吓退了 {name}！")
            elif game.version == "ui":
                if game.ui.hide_other_info:
                    game.ui.log_action(f"[信息已屏蔽]")
                else:
                    print(f"{target_player.name} 触发 😱 审问者技能：吓退了 {name}！")
        return True
    else:
        if not game.hasRealPlayer:
            if game.version == "shell":
                print(f"{target_player.name} 尝试触发 😱 审问者技能，但未能吓退 {name}。")
            elif game.version == "ui":
                if not game.ui.hide_other_info:
                    print(f"{target_player.name} 尝试触发 😱 审问者技能，但未能吓退 {name}。")
                else:
                    game.ui.log_action(f"[信息已屏蔽]")
        return False

# 赌徒技能：被开枪后，有50%概率同归于尽
def gambler_revenge(game, gambler, shooter):
    if random.random() < gambler.role.trigger_chance:
        if not game.hasRealPlayer:
            if game.version == "shell":
                print(f"{gambler.name} 触发 🎲 赌徒技能：同归于尽带走了 {shooter.name}！")
            elif game.version == "ui":
                if game.ui.hide_other_info:
                    game.ui.log_action(f"[信息已屏蔽]")
                else:
                    print(f"{gambler.name} 触发 🎲 赌徒技能：同归于尽带走了 {shooter.name}！")
        return True
    else:
        if not game.hasRealPlayer:
            if game.version == "shell":
                print(f"{gambler.name} 尝试触发 🎲 赌徒技能，但未能带走 {shooter.name}。")
            elif game.version == "ui":
                if not game.ui.hide_other_info:
                    print(f"{gambler.name} 尝试触发 🎲 赌徒技能，但未能带走 {shooter.name}。")
                else:
                    game.ui.log_action(f"[信息已屏蔽]")
        return False

# 装弹师技能：每次未被子弹击中时，有 50% 几率打乱当前子弹顺序。
def loader_reshuffle(game, player):
    if random.random() < player.role.trigger_chance:
        player.revolver.bulletPosition = random.randint(1, 6)
        if not game.hasRealPlayer:
            if game.version == "shell":
                print(f"{player.name} 触发 🔄 装弹师技能：重置了子弹顺序！")
            elif game.version == "ui":
                if game.ui.hide_other_info:
                    game.ui.log_action(f"[信息已屏蔽]")
                else:
                    print(f"{player.name} 触发 🔄 装弹师技能：重置了子弹顺序！")
    else:
        if not game.hasRealPlayer:
            if game.version == "shell":
                print(f"{player.name} 尝试触发 🔄 装弹师技能，但没有成功。")
            elif game.version == "ui":
                if not game.ui.hide_other_info:
                    print(f"{player.name} 尝试触发 🔄 装弹师技能，但没有成功。")
                else:
                    game.ui.log_action(f"[信息已屏蔽]")

# 预言家技能：每轮开始有 40% 概率提前知道当前子弹排列。
def seer_peek_bullet(game, player):
    if random.random() < player.role.trigger_chance:
        player.revolver_state = (player.revolver.currentChamber, player.revolver.bulletPosition)
        player.role.message["revolver_state"] = player.revolver_state
        if not game.hasRealPlayer:
            if game.version == "shell":
                print(f"{player.name} 触发 🔍 预言家技能：知道了弹针位置/子弹位置为{player.revolver_state}")
            elif game.version == "ui":
                if game.ui.hide_other_info:
                    game.ui.log_action(f"[信息已屏蔽]")
                else:
                    print(f"{player.name} 触发 🔍 预言家技能：知道了弹针位置/子弹位置为{player.revolver_state}")
    else:
        if not game.hasRealPlayer:
            if game.version == "shell":
                print(f"{player.name} 尝试触发 🔍 预言家技能，但未能预知弹针与子弹。")
            elif game.version == "ui":
                if not game.ui.hide_other_info:
                    print(f"{player.name} 尝试触发 🔍 预言家技能，但未能预知弹针与子弹。")
                else:
                    game.ui.log_action(f"[信息已屏蔽]")
