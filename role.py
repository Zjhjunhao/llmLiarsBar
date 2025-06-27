from typing import Callable, Optional
import random

class Role:
    """存放玩家的角色信息"""
    def __init__(self,
        name: str,
        description: str,
        effect: Optional[Callable] = None,  # 所有技能统一成一个 effect 回调
        trigger_chance: float = 0.3,        # 技能触发概率（0.0~1.0）
        max_uses_per_round: int = 1,        # 每轮最多使用次数
        max_uses_total: Optional[int] = 2):  # 总共最多使用次数，可为 None 表示无限
        self.name = name
        self.description = description
        self.effect = effect
        self.trigger_chance = trigger_chance
        self.max_uses_per_round = max_uses_per_round
        self.max_uses_total = max_uses_total

        self.used_this_round = 0
        self.used_total = 0

        self.message = {} # 该角色带来的额外信息

    def reset_round(self):
        """每轮开始前，充值当前轮次中的使用次数"""
        self.used_this_round = 0

    def can_trigger(self) -> bool:
        """检测使用次数是否符合要求，满足要求方可触发"""
        if self.max_uses_total is not None and self.used_total >= self.max_uses_total:
            return False
        if self.used_this_round >= self.max_uses_per_round:
            return False
        return True

    def try_trigger(self, game, player, *args, **kwargs) -> bool:
        """尝试触发技能：满足次数 & 概率则执行"""
        trigger = False
        if self.can_trigger(): # 确认触发
            if self.effect:
                trigger = self.effect(game, player, *args, **kwargs)
                if trigger:
                    self.used_this_round += 1
                    self.used_total += 1
        return trigger

def magician_illusion(game, player):
    """魔术师技能：每轮中有概率将非目标牌变为目标牌"""
    if random.random() < player.role.trigger_chance:
        convertible_indexes = [i for i, c in enumerate(player.hand) if c != game.currentCard and c != "Joker"]
        if not convertible_indexes:
            return True
        index_to_change = random.choice(convertible_indexes)
        original_card = player.hand[index_to_change]
        player.hand[index_to_change] = game.currentCard
        if game.version == "shell":
            if not game.hasRealPlayer:
                print(f"{player.name} 触发 🎩 魔术师技能：{original_card} 被视为 {game.currentCard}")
        elif game.version == "ui":
            if player.type == 'Player': # 真实玩家
                game.ui.log_action(f"您成功触发魔术师技能：{original_card} 被视为 {game.currentCard}")
            else:
                if not game.ui.hide_other_info:
                    game.ui.log_action(f"{player.name} 触发魔术师技能：{original_card} 被视为 {game.currentCard}")
        return True
    else:
        if game.version == "shell":
            if not game.hasRealPlayer:
                print(f"{player.name} 尝试触发 🎩 魔术师技能，但没有成功。")
        elif game.version == "ui":
            if player.type == 'Player': # 真实玩家
                game.ui.log_action(f"您尝试触发魔术师技能，但没有成功。")
            else:
                if not game.ui.hide_other_info:
                    game.ui.log_action(f"{player.name} 尝试触发魔术师技能，但没有成功。")
        return False

def intimidate(game, player, next_player=None):
    """审问者技能：被质疑前，有概率吓退下家质疑"""
    if next_player is None:
        name = "下家"
    else:
        name = next_player.name
    if random.random() < player.role.trigger_chance:
        if game.version == "shell":
            if not game.hasRealPlayer:
                print(f"{player.name} 触发 😱 审问者技能：吓退了 {name}！")
        elif game.version == "ui":
            if player.type == 'Player': # 真实玩家
                game.ui.log_action(f"您已成功触发审问者技能：吓退了 {name}！")
            else:
                if not game.ui.hide_other_info:
                    game.ui.log_action(f"{player.name} 触发审问者技能：吓退了 {name}！")
        return True
    else:
        if game.version == "shell":
            if not game.hasRealPlayer:
                print(f"{player.name} 尝试触发 😱 审问者技能，但未能吓退 {name}。")
        elif game.version == "ui":
            if player.type == 'Player': # 真实玩家
                game.ui.log_action(f"您尝试触发审问者技能，但未能吓退 {name}。")
            else:
                if not game.ui.hide_other_info:
                    game.ui.log_action(f"{player.name} 尝试触发审问者技能，但未能吓退 {name}。")
        return False

def gambler_revenge(game, player, unlucky):
    """赌徒技能：开枪阵亡后，有概率同归于尽"""
    if random.random() < player.role.trigger_chance:
        if game.version == "shell":
            if not game.hasRealPlayer:
                print(f"{player.name} 触发 🎲 赌徒技能：同归于尽带走了 {unlucky.name}！")
        elif game.version == "ui":
            if player.type == 'Player': # 真实玩家
                game.ui.log_action(f"您成功触发赌徒技能：同归于尽带走了 {unlucky.name}！")
            else:
                if not game.ui.hide_other_info:
                    game.ui.log_action(f"{player.name} 成功触发赌徒技能：同归于尽带走了 {unlucky.name}！")
        return True
    else:
        if game.version == "shell":
            if not game.hasRealPlayer:
                print(f"{player.name} 尝试触发 🎲 赌徒技能，但未能带走 {unlucky.name}。")
        elif game.version == "ui":
            if player.type == 'Player': # 真实玩家
                game.ui.log_action(f"您尝试触发赌徒技能，但未能带走 {unlucky.name}。")
            else:
                if not game.ui.hide_other_info:
                    game.ui.log_action(f"{player.name} 尝试触发赌徒技能，但未能带走 {unlucky.name}。")
        return False

def loader_reshuffle(game, player):
    """装弹师技能：每次未被子弹击中时，有 50% 几率打乱当前子弹顺序。"""
    if random.random() < player.role.trigger_chance:
        player.revolver.bulletPosition = random.randint(1, 6)
        if game.version == "shell":
            if not game.hasRealPlayer:
                print(f"{player.name} 触发 🔄 装弹师技能：重置了子弹顺序！")
        elif game.version == "ui":
            if player.type == 'Player': # 真实玩家
                game.ui.log_action(f"您成功触发装弹师技能：重置了子弹顺序！")
            else:
                if not game.ui.hide_other_info:
                    game.ui.log_action(f"{player.name} 成功触发装弹师技能：重置了子弹顺序！")
        return True
    else:
        if game.version == "shell":
            if not game.hasRealPlayer:
                print(f"{player.name} 尝试触发 🔄 装弹师技能，但没有成功。")
        elif game.version == "ui":
            if player.type == 'Player': # 真实玩家
                game.ui.log_action(f"您尝试触发装弹师技能，但没有成功。")
            else:
                if not game.ui.hide_other_info:
                    game.ui.log_action(f"{player.name} 尝试触发装弹师技能，但没有成功。")
        return False

def seer_peek_bullet(game, player):
    """预言家技能：每轮开始有 40% 概率提前知道当前子弹排列。"""
    if random.random() < player.role.trigger_chance:
        player.revolver_state = (player.revolver.currentChamber, player.revolver.bulletPosition)
        player.role.message["revolver_state"] = player.revolver_state
        if game.version == "shell":
            if not game.hasRealPlayer:
                print(f"{player.name} 触发 🔍 预言家技能：知道了弹针/子弹位置为{player.revolver_state}")
        elif game.version == "ui":
            if player.type == 'Player': # 真实玩家
                game.ui.log_action(f"您成功触发预言家技能：知道了弹针位置/子弹位置为{player.revolver_state}")
            else:
                if not game.ui.hide_other_info:
                    game.ui.log_action(f"{player.name} 成功触发预言家技能：知道了弹针位置/子弹位置为{player.revolver_state}")
        return True
    else:
        if game.version == "shell":
            if not game.hasRealPlayer:
                print(f"{player.name} 尝试触发 🔍 预言家技能，但未能预知弹针与子弹。")
        elif game.version == "ui":
            if player.type == 'Player': # 真实玩家
                game.ui.log_action(f"您尝试触发预言家技能，但未能预知弹针与子弹。")
            else:
                if not game.ui.hide_other_info:
                    game.ui.log_action(f"{player.name} 尝试触发预言家技能，但未能预知弹针与子弹。")
        return False

def get_defined_roles():
    """Game类中调用，返回所有的角色信息"""
    return [
        Role(
            name="魔术师",
            description="每轮有50%概率将一张非目标牌变为目标牌（全局最多2次）",
            effect=magician_illusion,
            trigger_chance=0.4,
            max_uses_per_round=2,
        ),
        Role(
            name="审问者",
            description="被质疑前，有50%概率吓退对方（全局最多2次）",
            effect=intimidate,
            trigger_chance=0.4,
            max_uses_per_round=2,
        ),
        Role(
            name="赌徒",
            description="反杀技能：死亡时有50%概率带走质疑者/被质疑者（全局最多1次）",
            effect=gambler_revenge,
            trigger_chance=0.5,
            max_uses_per_round=1,
        ),
        Role(
            name="装弹师",
            description="每次未中弹后，有50%概率改变子弹位置（全局最多4次）",
            effect=loader_reshuffle,
            trigger_chance=0.5,
            max_uses_per_round=4,
        ),
        Role(
            name="预言家",
            description="游戏开始时提前知道自己的弹针和子弹的位置",
            effect=seer_peek_bullet,
            trigger_chance=1,
            max_uses_per_round=1,
        ),
    ]

