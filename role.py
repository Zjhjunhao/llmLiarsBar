from typing import Callable, Optional
from role_effects import *

class Role:
    def __init__(self,
        name: str,
        description: str,
        timing: str,
        effect: Optional[Callable] = None,  # 所有技能统一成一个 effect 回调
        trigger_chance: float = 0.3,        # 技能触发概率（0.0~1.0）
        max_uses_per_round: int = 1,        # 每轮最多使用次数
        max_uses_total: Optional[int] = 2):  # 总共最多使用次数，可为 None 表示无限
        self.name = name
        self.description = description
        self.timing = timing
        self.effect = effect
        self.trigger_chance = trigger_chance
        self.max_uses_per_round = max_uses_per_round
        self.max_uses_total = max_uses_total

        self.used_this_round = 0
        self.used_total = 0

        self.message = {} # 该角色带来的额外信息

    def reset_round(self):
        self.used_this_round = 0

    def can_trigger(self) -> bool:
        if self.max_uses_total is not None and self.used_total >= self.max_uses_total:
            return False
        if self.used_this_round >= self.max_uses_per_round:
            return False
        return True

    def try_trigger(self, game, player, *args, **kwargs) -> bool:
        """尝试触发技能：满足次数 & 概率则执行"""
        if self.can_trigger() and random.random() < self.trigger_chance:
            if self.effect:
                self.effect(game, player, *args, **kwargs)
            self.used_this_round += 1
            self.used_total += 1
            return True
        return False


def get_defined_roles():
    return [
        Role(
            name="魔术师",
            description="每轮有50%概率将一张非目标牌变为目标牌（全局最多3次）",
            timing="出牌时",
            effect=magician_illusion,
            trigger_chance=0.3,
            max_uses_per_round=2,
        ),
        Role(
            name="审问者",
            description="被质疑前，有50%概率吓退对方",
            timing="被质疑前",
            effect=intimidate,
            trigger_chance=0.3,
            max_uses_per_round=3,
        ),
        Role(
            name="赌徒",
            description="反杀技能：被开枪死亡时有50%概率带走射击者",
            timing="阵亡后",
            effect=gambler_revenge,
            trigger_chance=0.4,
            max_uses_per_round=1,
        ),
        Role(
            name="装弹师",
            description="每次未中弹后，有50%概率改变子弹位置",
            timing="开枪后",
            effect=loader_reshuffle,
            trigger_chance=0.5,
            max_uses_per_round=3,
        ),
        Role(
            name="预言家",
            description="比赛开始时40%概率提前知道自己的子弹位置",
            timing="开始时",
            effect=seer_peek_bullet,
            trigger_chance=0.8,
            max_uses_per_round=1,
        ),
    ]