
# llmLiarsBar  
大语言模型课程大作业项目

## 📌 项目简介

**llmLiarsBar** 是一个结合了大语言模型（LLM）与“骗子酒馆”博弈玩法的互动式游戏系统，支持智能体和真实玩家共同参与。真实玩家通过自然语言进行参与；智能体玩家由大语言模型驱动，通过调用 OpenAI API 接入大语言模型，使智能体具备参与游戏的语言能力与决策逻辑；同时结合知识库检索（RAG），实现对局势的理解与策略生成。同时配套开发了可视化 UI，帮助用户清晰了解对局状态与流程，形成一个集互动性、策略性与实验性于一体的综合平台。


---

## ⚙️ 环境依赖

项目依赖已根据使用场景拆分为两个不同的依赖文件，方便按需安装：

`light_requirements.txt`：推荐使用。仅包含运行游戏所需的核心依赖，不包括用于数据清洗的额外库，适用于一般用户进行游戏体验与测试。

**安装命令：**
  ```bash
  pip install -r light_requirements.txt
  ```

`requirements.txt`：完整依赖列表（不推荐）
包含项目中所有模块（包括 data_clean.py）所需的全部依赖。适用于需要运行数据处理、分析等完整功能的用户。

**安装命令：**
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

### `game_for_ui.py` & `game_ui.py`
- `Game`：封装核心游戏逻辑（如发牌、回合控制、规则判断等）；
- `GameUI`：使用 tkinter 实现图形用户界面，实时可视化游戏过程。

### `prompt.py`
- `Prompt`：用于为智能体生成提示词；
- `LocalEmbeddingFunction`：使用本地句向量模型进行嵌入计算；
- 支持检索增强生成（RAG）机制，查询两个内置知识库：
  - `record_col`：历史对局记录；
  - `tip_col`：策略建议集合；
  - **注意** ：开启RAG之后，需要导入模型，初始化时间较长（本地没有会自动联网下载）
- `prompt_prepare_for_reals`：为真实玩家的选择补充动作。方便智能体理解

### `revolver.py`
- 实现左轮手枪逻辑，模拟质疑失败后的惩罚（游戏惩罚机制核心）。

### `config.py`
- 存储玩家信息配置（包括真实玩家与智能体）；
- 配置用于调用 LLM 的 OpenAI API 客户端参数。
- 实例化Prompt类，**可以选择是否开启RAG机制（导入模型较为耗时）**

### `role.py`
- 包含Role类，用于存储新玩法中的角色信息，存放在Player类中
- 包含了所有角色的触发函数，且会根据不同的情况的触发，产生不同形式的输出，方便玩家理解场上情况

### `data_clean.py`
- 包含用于处理建立知识库所需的函数
- 函数支持对局记录与策略数据导出为结构化 `jsonl` 格式，且不参与游戏运行。

### `utils.py`
- 包含用于记录终端输出的Logger类，使用方式如下

```bash
sys.stdout = Logger(your_path)
```


---

## 🧠 游戏运行逻辑

1. 运行 `game_ui.py` 启动ui界面版游戏，运行`game.py`启动终端版游戏，我们提供两种模式，一种为普通模式，一种为设置了角色和技能的新模式；

启动普通模式(默认为普通模式)
```
python game_ui.py common
python game.py common
```

启动角色模式（新玩法）
```
python game_ui.py role
python game.py role
```

2. 系统自动读取 `config.py` 中的玩家配置信息，你可以在该文件下修改AI玩家模型，可以选择加入RealPlayer类玩家参与游戏；同时也可以**在初始化Prompt 实例的时候选择是否打开 RAG 机制**，帮助智能体获取更多信息。
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
- 处理前/后的数据分别存放在 `strategy/`文件夹和 `cleaned_output/` 文件夹 
- 内置知识库已提前生成并存放在 `chroma_db/` 文件夹中；
- 智能体使用本地嵌入模型进行检索（支持向量搜索）；
- 知识库中的对局信息内容借鉴了 https://github.com/LYiHub/liars-bar-llm/tree/main 中的部分对局记录
-  策略内容参考的网页网址如下：
   - https://steamcommunity.com/sharedfiles/filedetails/?id=3350619018
   - https://www.reddit.com/r/LiarsBar/comments/1hso16g/liars_bar_strategies_tips_and_tricks/
