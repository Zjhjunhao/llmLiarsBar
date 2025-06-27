
# llmLiarsBar  
大语言模型课程大作业项目

## 📌 项目简介

**llmLiarsBar** 是一个结合了大语言模型（LLM）与“骗子酒馆”博弈玩法的互动式游戏系统，支持智能体和真实玩家共同参与。真实玩家通过自然语言进行参与；智能体玩家由大语言模型驱动，通过调用 OpenAI API 结合知识库检索（RAG），实现对局势的理解与策略生成。该项目集成了图形界面、嵌入式检索、对话提示词构造、游戏流程控制等模块。


---

## ⚙️ 环境依赖

所需依赖及其版本已列于 `requirements.txt` 文件中。请在项目目录下运行以下命令进行安装：

```bash
pip install -r requirements.txt
```

---

## 🗂️ 项目结构与模块说明

### `main.py`
- 游戏主入口，运行后自动启动界面与游戏流程控制。

### `player.py`
- `Player`：由大语言模型控制的智能体玩家；
- `RealPlayer`：真实用户控制的玩家接口。

### `game_new.py` & `game_ui.py`
- `Game`：封装核心游戏逻辑（如发牌、回合控制、规则判断等）；
- `GameUI`：使用 tkinter 实现图形用户界面，实时可视化游戏过程。

### `prompt.py`
- `Prompt`：用于为智能体生成提示词；
- `LocalSentenceTransformerEmbeddingFunction`：使用本地句向量模型进行嵌入计算；
- 支持检索增强生成（RAG）机制，查询两个内置知识库：
  - `record_col`：历史对局记录；
  - `tip_col`：策略建议集合；
- `prompt_prepare_for_reals`：为真实玩家提供行动建议。

### `revolver.py`
- 实现左轮手枪逻辑，模拟质疑失败后的惩罚（游戏惩罚机制核心）。

### `config.py`
- 存储玩家信息配置（包括真实玩家与智能体）；
- 配置用于调用 LLM 的 OpenAI API 客户端参数。

### `data_clean.py`
- 包含工具函数用于清洗游戏过程中的记录与策略数据；
- 支持将数据导出为结构化 `jsonl` 格式；
- 本模块不参与游戏运行，仅用于后期分析。

---

## 🧠 游戏运行逻辑

1. 运行 `game_ui.py` 启动ui界面版游戏，运行`game.py`启动终端版游戏，我们提供两种模式，一种为普通模式，一种为设置了职业和技能的新模式；

启动普通模式(默认为普通模式)
```
python game_ui.py common
python game.py common
```

启动职业模式
```
python game_ui.py role
python game.py common
```

2. 系统自动读取 `config.py` 中的玩家配置信息，你可以在该文件下修改AI玩家模型，可以选择加入RealPlayer类玩家参与游戏；
3. 初始化 UI 界面与游戏控制类；
4. 游戏按轮进行，每轮流程如下：
   - 随机设定一张目标牌，并为每位玩家发放 5 张手牌；
   - 当前轮游戏信息（`roundLog`、`currentCard`、`playNum`）传递给每位玩家；
     - **智能体玩家** 调用知识库与 LLM 生成行动方案（返回 JSON）；
     - **真实玩家** 结合自身策略与智能体辅助提示做出决策（返回 JSON）；
   - 游戏根据玩家行动：
     - `play`：继续该轮游戏；
     - `question`：发起质疑，触发“开枪”流程，判定胜负；
   - 存活玩家进入下一轮；
5. 游戏持续至只剩一位玩家时结束。

---

## 📁 数据与知识库说明
- 内置知识库已提前生成并存放在 `chroma_db/` 文件夹中；
- 智能体使用本地嵌入模型进行检索（支持向量搜索）；
- 知识库中的对局信息内容借鉴了 https://github.com/LYiHub/liars-bar-llm/tree/main 中的部分对局记录
-  策略内容参考的网页网址如下：
   - https://steamcommunity.com/sharedfiles/filedetails/?id=3350619018
   - https://www.reddit.com/r/LiarsBar/comments/1hso16g/liars_bar_strategies_tips_and_tricks/
