import tkinter as tk
from tkinter import messagebox
import random
import threading
from revolver import Revolver
from config import players
from game_for_ui import *
from utils import Logger
from player import *
import sys

ROLE = True

class GameUI:
    def __init__(self, root):
        self.root = root
        self.root.title("骗子酒馆AI大战")
        self.root.geometry("800x800")  # 设置窗口大小
        
        # 游戏状态标志
        self.game_running = False
        self.round_ended = True
        self.is_processing = False  
        self.hide_other_info = False
        
        # 游戏实例
        self.game = Game(players, self)

        if self.game.hasRealPlayer:
            self.hide_other_info = True
        
        # 创建界面组件
        self.create_widgets()
        
        # 初始化游戏
        self.init_game()

    def create_widgets(self):
        """
        创建游戏界面组件（优化布局结构）
        """
        # 配置主窗口的网格权重
        self.root.grid_rowconfigure(0, weight=0)  # 顶部信息区
        self.root.grid_rowconfigure(1, weight=0)  # 选项区
        self.root.grid_rowconfigure(2, weight=1)  # 中央游戏区
        self.root.grid_rowconfigure(3, weight=6)  # 日志区
        self.root.grid_rowconfigure(4, weight=0)  # 按钮区
        self.root.grid_rowconfigure(5, weight=0)  # 状态提示
        self.root.grid_rowconfigure(6, weight=0)  # 加载提示
        self.root.grid_rowconfigure(7, weight=0)  # 输入区
        self.root.grid_columnconfigure(0, weight=1)
        
        # 顶部信息区域（独立框架）
        top_info_frame = tk.Frame(self.root, bg="#f0f0f0", relief=tk.RAISED, bd=2)
        top_info_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        top_info_frame.grid_columnconfigure(0, weight=1)
        top_info_frame.grid_columnconfigure(1, weight=1)
        top_info_frame.grid_columnconfigure(2, weight=1)
        
        self.round_label = tk.Label(top_info_frame, text="当前轮次: 0", font=("Arial", 12, "bold"), bg="#f0f0f0")
        self.round_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        self.survived_label = tk.Label(top_info_frame, text="存活玩家: ", font=("Arial", 12), bg="#f0f0f0")
        self.survived_label.grid(row=0, column=1, sticky="n", pady=5)
        
        self.target_card_label = tk.Label(top_info_frame, text="当前目标牌: None", font=("Arial", 12), bg="#f0f0f0")
        self.target_card_label.grid(row=0, column=2, sticky="e", padx=10, pady=5)
        
        # 选项区域（独立框架，位于顶部信息区下方）
        option_frame = tk.Frame(self.root, bg="#f0f0f0", relief=tk.RAISED, bd=2)
        option_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=2)
        option_frame.grid_columnconfigure(0, weight=1)
        
        if self.game.hasRealPlayer: self.hide_info_var = tk.BooleanVar(value=True)# 有真实玩家，默认设置为打开
        else: self.hide_info_var = tk.BooleanVar(value=False)        
        self.hide_info_check = tk.Checkbutton(
            option_frame, text="屏蔽玩家信息", variable=self.hide_info_var,
            font=("Arial", 10), bg="#f0f0f0", command=self.toggle_hide_info)
        self.hide_info_check.grid(row=0, column=0, sticky="w", padx=10, pady=2)
        
        # 中央游戏区域
        center_frame = tk.Frame(self.root)
        center_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        
        # 设置中央区域网格权重
        center_frame.grid_rowconfigure(0, weight=1)
        center_frame.grid_rowconfigure(1, weight=3)
        center_frame.grid_rowconfigure(2, weight=1)
        center_frame.grid_columnconfigure(0, weight=1)
        center_frame.grid_columnconfigure(1, weight=3)
        center_frame.grid_columnconfigure(2, weight=1)
        
        # 上方玩家
        top_player_frame = tk.Frame(center_frame, bd=2, relief=tk.SOLID, bg="#e0e0e0")
        top_player_frame.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.top_player_label = tk.Label(top_player_frame, text="玩家1: []", font=("Arial", 10), bg="#e0e0e0", width=25, height=3)
        self.top_player_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左侧玩家
        left_player_frame = tk.Frame(center_frame, bd=2, relief=tk.SOLID, bg="#e0e0e0")
        left_player_frame.grid(row=1, column=0, sticky="ns", padx=5, pady=5)
        self.left_player_label = tk.Label(left_player_frame, text="玩家2: []", font=("Arial", 10), bg="#e0e0e0", width=25, height=4)
        self.left_player_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 右侧玩家
        right_player_frame = tk.Frame(center_frame, bd=2, relief=tk.SOLID, bg="#e0e0e0")
        right_player_frame.grid(row=1, column=2, sticky="ns", padx=5, pady=5)
        self.right_player_label = tk.Label(right_player_frame, text="玩家3: []", font=("Arial", 10), bg="#e0e0e0", width=25, height=4)
        self.right_player_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 下方玩家
        bottom_player_frame = tk.Frame(center_frame, bd=2, relief=tk.SOLID, bg="#e0e0e0")
        bottom_player_frame.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        self.bottom_player_label = tk.Label(bottom_player_frame, text="玩家4: []", font=("Arial", 10), bg="#e0e0e0", width=25, height=3)
        self.bottom_player_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 中央出牌区域
        play_area = tk.Frame(center_frame, bd=2, relief=tk.SOLID, bg="#f8f8f8")
        play_area.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        self.play_log_label = tk.Label(play_area, text="当前出牌: 无", font=("Arial", 12, "bold"), bg="#f8f8f8", wraplength=300, height=4, width=40)
        self.play_log_label.pack(fill=tk.BOTH, expand=True, pady=20)

        # 游戏日志区域
        log_frame = tk.Frame(self.root, bd=2, relief=tk.SOLID)
        log_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
        
        log_title = tk.Label(log_frame, text="游戏日志", font=("Arial", 12, "bold"), bg="#f0f0f0",)
        log_title.pack(anchor=tk.W, fill=tk.X, pady=5, padx=5)
        
        # 增加height参数并确保日志区域可以扩展
        self.round_log_text = tk.Text(log_frame, height=25, width=80, font=("Arial", 10))
        self.round_log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = tk.Scrollbar(self.round_log_text, command=self.round_log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.round_log_text.config(yscrollcommand=scrollbar.set)
        
        # 操作按钮
        button_frame = tk.Frame(self.root, bg="#f0f0f0")
        button_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=10)
        
        self.next_round_button = tk.Button(
            button_frame, text="开始下一轮", command=self.start_next_round,
            font=("Arial", 12), bg="#4CAF50", fg="white", relief=tk.RAISED, bd=2,
            padx=20, pady=5)
        self.next_round_button.pack(expand=True)
        
        # 状态提示
        self.status_label = tk.Label(self.root, text="等待开始...", font=("Arial", 11, "italic"), bg="#f0f0f0")
        self.status_label.grid(row=5, column=0, sticky="ew", pady=5)
        
        # 加载提示
        self.loading_label = tk.Label(self.root, text="", font=("Arial", 10), fg="red")
        self.loading_label.grid(row=6, column=0, sticky="s", pady=5)
        
        # 输入框区域
        input_frame = tk.Frame(self.root, bg="#f0f0f0", relief=tk.SUNKEN, bd=1)
        input_frame.grid(row=7, column=0, sticky="ew", padx=10, pady=5)
        
        self.input_entry = tk.Entry(input_frame, font=("Arial", 12))
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        self.input_entry.bind("<Return>", self.on_input_submit)  # 绑定回车键提交
        
        self.submit_button = tk.Button(
            input_frame, text="提交", command=self.on_input_submit,
            font=("Arial", 12), bg="#4CAF50", fg="white", state=tk.DISABLED
        )
        self.submit_button.pack(side=tk.RIGHT, padx=5, pady=5)

    def toggle_hide_info(self):
        """
        切换信息屏蔽状态
        """
        self.hide_other_info = self.hide_info_var.get()
        status_text = "已启用" if self.hide_other_info else "已禁用"
        self.status_label.config(text=f"屏蔽玩家信息: {status_text}")
        self.update_player_cards()  # 立即更新玩家信息显示
    
    def init_game(self):
        """
        初始化游戏
        """
        self.status_label.config(text="游戏初始化中...")
        self.root.after(500, self.start_game)  # 延迟初始化，确保UI加载

    def start_game(self):
        """
        开始游戏
        """
        self.game_running = True
        self.game.GameStart()  # 启动游戏
        self.status_label.config(text="游戏准备就绪，点击开始下一轮")
        self.next_round_button.config(state=tk.NORMAL)

    def start_next_round(self):
        """
        开始下一轮
        """
        if not self.game_running or self.game.gameOver or self.is_processing:
            return
        self.round_ended = False 
        self.is_processing = True  
        self.next_round_button.config(state=tk.DISABLED)  # 禁用按钮
        self.status_label.config(text="轮次进行中...")
        self.loading_label.config(text="加载中...")
        
        # 在新线程中开始新轮次
        threading.Thread(target=self.run_round_in_thread, daemon=True).start()

    def run_round_in_thread(self):
        """
        在新线程中运行轮次,避免页面卡顿
        """
        try:
            # 开始新轮次
            self.game.RoundStart()
            self.root.after(0, self.update_round_info)  # 主线程更新UI
            
            # 运行当前轮次
            self.run_current_round()
        except Exception as e:
            print(f"Error: {e}")
            self.root.after(0, lambda: messagebox.showerror("错误", f"运行轮次时出错: {str(e)}"))
        finally:
            self.is_processing = False
            self.root.after(0, lambda: self.loading_label.config(text=""))

    def run_current_round(self):
        """
        进行当前轮次
        """
        if self.game.roundOver or self.game.gameOver:
            self.root.after(0, self.on_round_complete)
            return
                
        playerNum = len(self.game.players)
        alive_players = [p for p in self.game.players if not p.is_out and p.name in self.game.playersinround]
        
        # 如果没有活跃玩家，结束轮次
        if not alive_players:
            self.game.roundOver = True
            self.root.after(0, self.on_round_complete)
            return
        
        # 获取当前玩家
        current_player = self.game.players[self.game.currentIndex]
        
        # 如果当前玩家已淘汰，找到下一个存活玩家
        if current_player.is_out or current_player.name not in self.game.playersinround:
            self.game.currentIndex = (self.game.currentIndex + 1) % playerNum
            while self.game.players[self.game.currentIndex].is_out or self.game.players[self.game.currentIndex].name not in self.game.playersinround:
                self.game.currentIndex = (self.game.currentIndex + 1) % playerNum
            current_player = self.game.players[self.game.currentIndex]
        
        # 处理玩家行动
        #self.process_player_turn_in_thread(current_player)
        # 真实玩家
        if isinstance(current_player, RealPlayer):  
            self.real_player_turn = True
            self.enable_input(current_player)
        # AI玩家
        else:  
            self.process_player_turn_in_thread(current_player)

    def process_player_turn_in_thread(self, player):
        """
        在新线程中处理玩家回合
        """
        threading.Thread(target=lambda: self.auto_process_player_turn(player), daemon=True).start()

    def auto_process_player_turn(self, player):
        """
        处理玩家回合
        """
        self.root.after(0, lambda: self.loading_label.config(text=f"{player.name} 思考中..."))
        
        try:
            self.log_action(f"--- {player.name}的回合---")
            
            # 记录玩家当前手牌（在主线程中更新）
            current_hand = player.hand.copy()
            self.root.after(0, lambda: self.log_action(f"--- {player.name}的手牌: {current_hand} ---"))
            
            # 玩家出牌
            action = player.PlayCard(self.game.roundLog, self.game.currentCard, len(self.game.players))
            
            # 记录出牌（在主线程中更新）
            self.root.after(0, lambda: self.log_action(f"--- {player.name} 出牌: {action} ---"))
            
            # 处理玩家动作
            self.game.process_action(action)
            
            # 更新UI（在主线程中更新）
            self.root.after(0, self.update_player_cards)
            self.root.after(0, lambda: self.update_play_log(self.game.palyCardLog))
            self.root.after(0, self.root.update)  # 强制更新UI
            
        except Exception as e:
            print(f"Player turn error: {e}")
            self.root.after(0, lambda: messagebox.showerror("错误", f"处理玩家回合时出错: {str(e)}"))
        finally:
            self.root.after(0, lambda: self.loading_label.config(text=""))
            
            # 检查轮次是否结束
            if self.game.roundOver or self.game.gameOver:
                self.root.after(0, self.on_round_complete)
                return
                
            # 继续下一个玩家（在主线程中调度）
            self.root.after(1000, self.run_current_round)  # 延迟1秒，便于观察

    def enable_input(self, player):
        """
        启用输入功能
        """
        self.log_action(f"你的回合，请输入操作")
        self.input_enabled = True
        self.input_entry.config(state=tk.NORMAL)
        self.submit_button.config(state=tk.NORMAL)

        self.input_entry.unbind("<Return>")  # 清除之前绑定
        self.input_entry.delete(0, tk.END)
        self.input_entry.bind("<Return>", self.on_input_submit)
        self.submit_button.config(command=self.on_input_submit)
        
        # 显示手牌提示
        hand_display = "你的手牌: " + ", ".join([f"{i}:{card}" for i, card in enumerate(player.hand)])
        self.log_action(hand_display)
        
        if self.game.roundLog:
            self.log_action("请输入操作（出牌/play/p/1 或 质疑/question/q/2）：")
        else:
            self.log_action("请输入操作（出牌/play/p/1）：")

    def disable_input(self):
        """
        禁用输入功能
        """
        self.input_enabled = False
        self.input_entry.config(state=tk.DISABLED)
        self.submit_button.config(state=tk.DISABLED)
        self.input_entry.delete(0, tk.END)

    def on_input_submit(self, event=None):
        """
        处理输入提交
        """
        if not self.input_enabled:
            return
            
        user_input = self.input_entry.get().strip().lower()
        self.input_entry.delete(0, tk.END)  # 清空输入框      
        
        current_player = self.game.players[self.game.currentIndex]
        action = current_player.parse_action_input(user_input)  
        
        if action is None or (action == "question" and  not self.game.roundLog):
            self.log_action("无效输入，请重新输入。")
            return
        
        self.log_action(f"玩家输入: {user_input}")  

        # 处理出牌操作
        if action == "play":
            self.handle_play_action(current_player)
        # 处理质疑操作
        elif action == "question":
            self.handle_question_action(current_player)
    
    def handle_play_action(self, player):
        """
        处理出牌操作
        """
        self.log_action("请输入要打出的牌的索引（空格分隔，最多3张）:")

        self.input_entry.unbind("<Return>")  # 清除之前绑定
        self.input_entry.delete(0, tk.END)
        self.input_entry.bind("<Return>", self.on_play_cards_submit)
        self.submit_button.config(command=self.on_play_cards_submit)

        self.current_action = "play"
        self.current_player = player

    def on_play_cards_submit(self, event):
        """
        处理出牌索引输入
        """
        card_indexes = self.input_entry.get().strip()
        self.input_entry.delete(0, tk.END)  # 清空输入框
        try:
            cards = [int(i) for i in card_indexes.split()]

            # print(f"输入的索引: {cards}")
            # print(f"当前玩家手牌: {self.current_player.hand}")
            
            # 检查索引有效性
            if not all(0 <= i < len(self.current_player.hand) for i in cards):
                self.log_action("错误：输入的索引超出范围")
                self.handle_play_action(self.current_player)
                return
                
            # 检查卡牌数量
            if not (1 <= len(cards) <= 3):
                self.log_action("错误：请选择1-3张牌")
                self.handle_play_action(self.current_player)
                return
                
            # 检查是否有重复索引
            if len(cards) != len(set(cards)):
                self.log_action("错误：不能选择重复的牌")
                self.handle_play_action(self.current_player)
                return

            self.log_action(f"玩家输入索引: {cards}") 
            self.log_action(f"对应{[self.current_player.hand[card] for card in cards]}")
                
            # 调用RealPlayer的PlayCard方法
            action = self.current_player.PlayCard(self.game.roundLog, self.game.currentCard, len(self.game.players))
            
            # 确保action包含必要的键
            if "cards" not in action:
                action["cards"] = []
            if "type" not in action:
                action["type"] = "play"
            action["cards"] = cards
            action["type"] = "play"

            self.current_action = action
            self.selected_cards = cards  # 保存选中的卡牌索引

            #action["playAction"] = self.current_player.action_explaination(self.game.roundLog, self.current_player.hand, len(self.game.players), action, cards)
            threading.Thread(
                target=self.generate_action_description_in_thread,
                args=(self.game.roundLog, self.current_player.hand, len(self.game.players), cards),
                daemon=True
            ).start()

        except ValueError:
            self.log_action("错误：请输入有效的数字索引")
            self.handle_play_action(self.current_player)
    
    def generate_action_description_in_thread(self, roundLog, hand, playNum, cards):
        """
        在后台线程中生成动作描述
        """
        try:
            # 调用action_explaination生成动作描述
            playaction = self.current_player.action_explaination(roundLog, hand, playNum, self.current_action, cards)
            
            # 在主线程中设置动作描述
            self.root.after(0, lambda p=playaction: self.set_play_action(p))
        except Exception as e:
            print(f"生成动作描述错误: {e}")
            # 在主线程中设置默认动作描述
            self.root.after(0, lambda: self.set_play_action("玩家选择出牌"))
        finally:
            self.is_generating_action = False

    def set_play_action(self, playaction):
        """
        设置动作描述并继续游戏
        """
        if not hasattr(self, 'current_action'):
            return
            
        # 设置动作描述
        self.current_action["playAction"] = playaction
        
        # 处理玩家动作
        self.game.process_action(self.current_action)
        
        # 从手牌中移除已选卡牌
        for i in sorted(self.selected_cards, reverse=True):
            if i < len(self.current_player.hand):
                self.current_player.hand.pop(i)
        
        self.log_action(f"--- {self.current_player.name} 出牌: {self.current_action}---")
        self.update_player_cards()
        self.disable_input()
        self.real_player_turn = False
        self.loading_label.config(text="")
        self.root.after(1000, self.run_current_round)

    def handle_question_action(self, player):
        """
        处理质疑操作
        """
        # 调用RealPlayer的PlayCard方法
        action = player.PlayCard(self.game.roundLog, self.game.currentCard, len(self.game.players))
        #action["playAction"] = self.current_player.action_explaination(self.game.roundLog, self.current_player.hand, len(self.game.players), action, [])
        action["type"] = "question"
        self.current_action = action
        self.current_player = player
        self.selected_cards = []
        threading.Thread(
                target=self.generate_action_description_in_thread,
                args=(self.game.roundLog, player.hand, len(self.game.players), []),
                daemon=True
        ).start()

    def on_round_complete(self):
        """
        轮次完成后的处理
        """
        self.round_ended = True
        self.update_player_status()
        
        if self.game.gameOver:
            if self.game.winner is None:
                self.status_label.config(text=f"--- 游戏结束，所有玩家都已阵亡，没有获胜者 ---")
            else:
                self.status_label.config(text=f"游戏结束，获胜者是 {self.game.winner.name}!")
            self.next_round_button.config(state=tk.DISABLED)
        else:
            self.status_label.config(text="轮次结束，点击开始下一轮")
            self.next_round_button.config(state=tk.NORMAL)  # 启用按钮

    def update_round_info(self):
        """
        更新轮次和目标牌信息
        """
        self.round_label.config(text=f"当前轮次: {self.game.gameRound}")
        self.target_card_label.config(text=f"当前目标牌: {self.game.currentCard}")
        survived = [p.name for p in self.game.players if not p.is_out]
        self.survived_label.config(text=f"存活玩家: {' | '.join(survived)}")

    def update_player_cards(self):
        """
        更新玩家手牌显示
        """
        all_time = self.game.players[0].revolver.chambers
        
        # 找到真实玩家
        real_player = None
        for player in self.game.players:
            if isinstance(player, RealPlayer):
                real_player = player
                break
                
        for i, player in enumerate(self.game.players):
            time = self.game.players[i].revolver.fire_times
            fire_message = f"{time}/{all_time}"
            
            # 构建玩家显示文本
            if player == real_player or not self.hide_other_info:
                if player.is_out:
                    display_text = f"{player.name}({fire_message}): 已出局"
                else:
                    display_text = f"{player.name}({fire_message})\n手牌：{player.hand}"
            else:
                # 启用屏蔽时隐藏其他玩家信息
                if player.is_out:
                    display_text = f"{player.name}({fire_message}): 已出局"
                else:
                    display_text = f"{player.name}({fire_message})\n"
            
            # 更新显示
            if i == 0:
                self.top_player_label.config(text=display_text)
            elif i == 1:
                self.left_player_label.config(text=display_text)
            elif i == 2:
                self.bottom_player_label.config(text=display_text)
            elif i == 3:
                self.right_player_label.config(text=display_text)

    def update_player_status(self):
        """
        更新玩家状态
        """
        self.update_player_cards()
        survived = [p.name for p in self.game.players if not p.is_out]
        self.survived_label.config(text=f"存活玩家: {' | '.join(survived)}")

    def update_play_log(self, play_log):
        """
        更新当前出牌日志
        """
        if play_log:
            if play_log['action'] == 'play':
                play_text = f"{play_log['playerName']} 出牌 \n {play_log['playAction']}"
            else:
                play_text = f"{play_log['playerName']} 质疑 \n {play_log['playAction']}"
        else:
            play_text = "当前出牌: 无"
        self.play_log_label.config(text=play_text, wraplength=self.play_log_label.winfo_width())
    
    def log_action(self, action_text):
        """
        记录游戏动作到日志
        """
        if self.hide_other_info:
            if "reason" in action_text or "手牌" in action_text:
                action_text = "[信息已屏蔽]"
        self.round_log_text.insert(tk.END, f"{action_text}\n")
        self.round_log_text.see(tk.END)  # 滚动到最新日志

class GameUIwithRole(GameUI):
    def __init__(self, root):
        super().__init__(root)
        self.game = GamewithRole(players, self)
        if self.game.hasRealPlayer:
            self.hide_other_info = True
        self.canQuestion = True
    
    def update_player_cards(self):
        """
        更新玩家角色、手牌显示
        """
        all_time = self.game.players[0].revolver.chambers
        
        # 找到真实玩家
        real_player = None
        for player in self.game.players:
            if isinstance(player, RealPlayer):
                real_player = player
                break
                
        for i, player in enumerate(self.game.players):
            time = self.game.players[i].revolver.fire_times
            fire_message = f"{time}/{all_time}"
            
            # 构建玩家显示文本
            if player == real_player or not self.hide_other_info:
                if player.is_out:
                    display_text = f"{player.name}({fire_message}): 已出局\n角色：{player.role.name}"
                else:
                    display_text = f"{player.name}({fire_message})\n角色：{player.role.name}\n手牌：{player.hand}"
            else:
                # 启用屏蔽时隐藏其他玩家信息
                if player.is_out:
                    display_text = f"{player.name}({fire_message}): 已出局"
                else:
                    display_text = f"{player.name}({fire_message})\n"
            
            # 更新显示
            if i == 0:
                self.top_player_label.config(text=display_text)
            elif i == 1:
                self.left_player_label.config(text=display_text)
            elif i == 2:
                self.bottom_player_label.config(text=display_text)
            elif i == 3:
                self.right_player_label.config(text=display_text)

    def auto_process_player_turn(self, player):
        """
        处理玩家回合
        """
        self.root.after(0, lambda: self.loading_label.config(text=f"{player.name} 思考中..."))
        
        try:
            self.log_action(f"--- {player.name}的回合---")

            if player.role and player.role.name == "魔术师":
                player.role.try_trigger(self.game, player)
            
            # 记录玩家当前手牌（在主线程中更新）
            current_hand = player.hand.copy()
            self.root.after(0, lambda: self.log_action(f"--- {player.name}的手牌: {current_hand} ---"))
            
            # 玩家出牌
            action = player.PlayCard(self.game.roundLog, self.game.currentCard, len(self.game.players), canQuestion=self.canQuestion)
            
            # 记录出牌（在主线程中更新）
            self.root.after(0, lambda: self.log_action(f"--- {player.name} 出牌: {action} ---"))
            
            # 处理玩家动作
            self.game.process_action(action)

            if player.role and player.role.name == "审问者":  # 审问者技能触发
                can_question = not player.role.try_trigger(self.game, player)
                self.canQuestion = can_question
            else: 
                self.canQuestion = True
            
            # 更新UI（在主线程中更新）
            self.root.after(0, self.update_player_cards)
            self.root.after(0, lambda: self.update_play_log(self.game.palyCardLog))
            self.root.after(0, self.root.update)  # 强制更新UI
            
        except Exception as e:
            print(f"Player turn error: {e}")
            self.root.after(0, lambda: messagebox.showerror("错误", f"处理玩家回合时出错: {str(e)}"))
        finally:
            self.root.after(0, lambda: self.loading_label.config(text=""))
            
            # 检查轮次是否结束
            if self.game.roundOver or self.game.gameOver:
                self.root.after(0, self.on_round_complete)
                return
                
            # 继续下一个玩家（在主线程中调度）
            self.root.after(1000, self.run_current_round)  # 延迟1秒，便于观察

    def enable_input(self, player):
        """
        启用输入功能
        """
        self.log_action(f"你的回合，请输入操作")
        self.input_enabled = True
        self.input_entry.config(state=tk.NORMAL)
        self.submit_button.config(state=tk.NORMAL)

        self.input_entry.unbind("<Return>")  # 清除之前绑定
        self.input_entry.delete(0, tk.END)
        self.input_entry.bind("<Return>", self.on_input_submit)
        self.submit_button.config(command=self.on_input_submit)

        # 魔术师技能触发
        if player.role and player.role.name == "魔术师":
            player.role.try_trigger(self.game, player)

        self.log_action(f"本次游戏模式为 Role")
        self.log_action(f"你本局的角色是【{player.role.name}】\n"
                        f"本轮已触发 {player.role.used_this_round} 次，累计触发 {player.role.used_total} 次\n")
        if player.role.name == "预言家" and "revolver_state" in player.role.message:
            state = player.role.message["revolver_state"]
            self.log_action(f"你的预言家技能成功触发，本局游戏中你的初始手枪弹针位置/子弹位置为 {state[0]}/{state[1]}")
        
        # 显示手牌提示
        hand_display = "你的手牌: " + ", ".join([f"{i}:{card}" for i, card in enumerate(player.hand)])
        self.log_action(hand_display)
        
        if self.game.roundLog and self.canQuestion:
            self.log_action("请输入操作（出牌/play/p/1 或 质疑/question/q/2）：")
        else:
            if not self.canQuestion:
                self.log_action("你的上家是审问者并在本轮成功发动技能，因此你本回合只能选择出牌，无法选择质疑")
            self.log_action("请输入操作（出牌/play/p/1）：")

    def on_input_submit(self, event=None):
        """
        处理输入提交
        """
        if not self.input_enabled:
            return
            
        user_input = self.input_entry.get().strip().lower()
        self.input_entry.delete(0, tk.END)  # 清空输入框      
        
        current_player = self.game.players[self.game.currentIndex]
        action = current_player.parse_action_input(user_input)  
        
        if action is None or (action == "question" and  not self.game.roundLog) or (action == "question" and  not self.game.roundLog):
            self.log_action("无效输入，请重新输入。")
            return
        
        self.log_action(f"玩家输入: {user_input}")  

        # 处理出牌操作
        if action == "play":
            self.handle_play_action(current_player)
        # 处理质疑操作
        elif action == "question":
            self.handle_question_action(current_player)

    def set_play_action(self, playaction):
        """设置动作描述并继续游戏"""
        if not hasattr(self, 'current_action'):
            return
            
        # 设置动作描述
        self.current_action["playAction"] = playaction
        
        # 处理玩家动作
        self.game.process_action(self.current_action)

        # 审问者技能触发
        if self.current_player.role and self.current_player.role.name == "审问者":  
            can_question = not self.current_player.role.try_trigger(self.game, self.current_player)
            self.canQuestion = can_question
        else: 
            self.canQuestion = True

        # 从手牌中移除已选卡牌
        for i in sorted(self.selected_cards, reverse=True):
            if i < len(self.current_player.hand):
                self.current_player.hand.pop(i)
        
        self.log_action(f"--- {self.current_player.name} 出牌: {self.current_action}---")
        self.update_player_cards()
        self.disable_input()
        self.real_player_turn = False
        self.loading_label.config(text="")
        self.root.after(1000, self.run_current_round)


if __name__ == "__main__":
    root = tk.Tk()

    default_font = ("SimSun", 10)  # 微软雅黑
    root.option_add("*Font", default_font)

    arg = "common"  
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
    

    if arg == "role":
        ui = GameUIwithRole(root)
    else: 
        ui = GameUI(root)
    root.mainloop()