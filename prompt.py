import json, chromadb
from sentence_transformers import SentenceTransformer
from chromadb.api.types import EmbeddingFunction
from role import *

class LocalEmbeddingFunction(EmbeddingFunction):
    """
    嵌入函数，将文本转化为向量
    """
    def __init__(self, model_name='all-mpnet-base-v2', device='cuda'):
        self.model = SentenceTransformer(model_name)
        #print(torch.cuda.is_available())
        self.model.to(device)

    def __call__(self, texts):
        return self.model.encode(texts, convert_to_numpy=True).tolist()
    
class Prompt():
    """
    为智能体生成提示词
    """
    def __init__(self, RAG=True):
        self.RAG = RAG # 是否开启知识库检索功能
        if self.RAG:
            self.strategy_col, self.record_col = self.load_or_build_collections()
        else:
            self.strategy_col, self.record_col = None, None
        self.currentCard = None
        self.hand = None
        self.roundLog = None
        self.fire_times = None
        self.playNum = None
        self.selfName = None
        self.chambers = None
        self.mode = "common"
        self.role = None
        self.canQuestion = True
    @staticmethod
    def load_or_build_collections(tip_path="cleaned_output/cleaned_tips.jsonl", record_path="cleaned_output/cleaned_cases.jsonl", db_dir: str = "chroma_db"):
        """
        加载预先处理好的策略文件和对局数据文件，并使用嵌入函数，将二者转化为向量库便于查询
        知识库会存储在 /chroma_db 文件夹下，只会生成一次
        """
        local_ef = LocalEmbeddingFunction()
        # client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet", persist_directory=db_dir))
        client = chromadb.PersistentClient(path=db_dir)
        strategy_col = client.get_or_create_collection("liars_strategy", embedding_function=local_ef)
        record_col = client.get_or_create_collection("liars_records", embedding_function=local_ef)
        if record_col.count() == 0:
            print("正在初始化对局记录向量库...")
            with open(record_path, "r", encoding="utf-8") as f_in:
                game_records = [json.loads(line) for line in f_in if line.strip()]
            for i, record in enumerate(game_records):
                document_text = (
                    f"【第{record['round']}轮】玩家 {record['player']} 出牌：{record['played_cards']}（声称是 {record['target_cards']}）\n"
                    f"出牌理由：{record['play_reason']}\n"
                    f"是否被质疑：{'无' if not record['challenge'] else '有'}\n"
                    f"质疑理由：{record['challenge_reason'] or '无'}"
                )

                record_col.add(
                    documents=[document_text],
                    ids=[f"record_{i}"],
                    metadatas=[{
                        "round": record["round"],
                        "player": record["player"],
                        "game_id": record["game_id"]
                    }]
                )
        if strategy_col.count() == 0:
            print("正在初始化策略提示向量库...")
            with open(tip_path, "r", encoding="utf-8") as f_in:
                game_tips = [json.loads(line) for line in f_in if line.strip()]

            for j, tip in enumerate(game_tips):
                strategy_col.add(
                    documents=[tip["text"]],
                    ids=[f"tip_{j}"],
                    metadatas=[{"type": tip["type"]}]
                )
        print("向量库已保存。")

        return strategy_col, record_col

    def generate_query(self):
        """
        根据当前的对局信息（若有）以及自身的情况，构建一个用于查询的 query_text
        """
        playCardTotal = self.roundLog[-1]["playCardTotal"] if self.roundLog else 0
        round_num = len(self.roundLog) + 1 if self.roundLog else 1

        if self.roundLog:
            last_play = self.roundLog[-1]
            prev_player = last_play["playerName"]
            prev_play_num = last_play["playCardNum"]
            prev_remain = last_play["remainCard"]
            prev_action = last_play["playAction"]
        else:
            prev_player = "无"
            prev_play_num = 0
            prev_remain = "未知"
            prev_action = "无"

        query_text = (
            f"当前是第 {round_num} 轮游戏。"
            f"目标牌是 {self.currentCard}，目前手牌为 {self.hand}。"
            f"本轮出牌总数为 {playCardTotal}，已经开枪 {self.fire_times} 次。"
        )

        if prev_player != "无":
            query_text += (
                f"上一位玩家打出 {prev_play_num} 张牌，声称是目标牌，出牌动作为「{prev_action}」，"
                f"剩余手牌数为 {prev_remain}。"
            )
        else:
            query_text += "我是本轮首位出牌玩家。"

        query_text += "当前局面是否适合出牌？若出牌，应如何出？是否有必要质疑上家？"

        return query_text
    
    def generate_context(self, query_text, include=["documents", "distances", "metadatas"]):
        """
        根据当前的情况（query_text），在两个向量库中进行查询，返回相关度最大的3个
        """
        case_res = self.record_col.query(query_texts=[query_text], n_results=2, include=include)
        tip_res = self.strategy_col.query(query_texts=[query_text], n_results=3, include=include)
        case_context = Prompt.build_context_from_results(case_res, threshold=0.5, default_msg="无相关对局记录")
        tip_context = Prompt.build_context_from_results(tip_res, threshold=0.9, default_msg="无相关策略指导")
        
        full_context = (
        "【对局记录相关信息】\n" + case_context + "\n\n" +
        "【策略指导相关信息】\n" + tip_context)

        return full_context 

    @staticmethod
    def build_context_from_results(results, threshold=0.5, max_length=1500, default_msg="无相关信息"):  
        """
        处理 ChromaDB 查询结果，将它们进行汇总，且设置一个相关度的限制
        """
        docs = results["documents"][0]
        distances = results["distances"][0]
        filtered_docs = []
        for doc, dist in zip(docs, distances):
            if dist <= threshold:
                filtered_docs.append(doc)

        if not filtered_docs:
            return default_msg

        combined_text = ""
        for i, doc in enumerate(filtered_docs):
            snippet = f"{i+1}. {doc}\n\n"
            if len(combined_text) + len(snippet) > max_length:
                break
            combined_text += snippet
        return combined_text.strip()
    
    def final_prompt(self, currentCard, hand, roundLog, fire_times, playNum, selfName, chambers=6):
        """
        生成最终的 prompt （player中只需要运行该函数即可）
        """
        self.currentCard, self.hand = currentCard, hand
        self.roundLog, self.fire_times = roundLog, fire_times
        self.playNum, self.selfName, self.chambers = playNum, selfName, chambers
        if self.RAG: # 使用知识库检索
            full_context = self.generate_context(query_text=self.generate_query())
            prompt = self.prompt_prepare(full_context)
        else:
            prompt = self.prompt_prepare()
        return prompt

    def add_role_prompt(self, role:Role, canQuestion=True):
        """新玩法角色模式信息更新"""
        self.mode = "role"
        self.role = role
        self.canQuestion = canQuestion

    def prompt_prepare(self, refer_inform="无相关信息"):
        """准备大模型提示词"""
        refer_info_text = (
            f"【参考信息】\n"
            f"- 我们根据过往的对局记录和游戏策略，为你找到了一些信息如下，仅供参考：\n"
            f"{refer_inform}"
            if refer_inform != "无相关信息"
            else "")
        
        if self.mode == "role":
            role_mode_text = (
                f"【特殊玩法：角色机制】\n"
                f"本局在传统骗子酒馆玩法基础上引入了 5 种特殊角色，"
                f"玩家开局随机获得一个，全局不变。\n"
                f"每个角色技能有概率触发，每轮最多触发 1 次，均为被动触发。\n"
                f"角色技能说明：\n"
                f"- 魔术师：每轮有50%概率将一张非目标牌变为目标牌（全局最多2次）\n"
                f"- 审问者：被质疑前，有50%概率吓退对方（全局最多2次）\n"
                f"- 赌徒：若开枪阵亡，有50%概率带走质疑者/被质疑者（全局最多1次）\n"
                f"- 装弹师：每次开枪未中弹后，有50%概率改变子弹位置（全局最多4次）\n"
                f"- 预言家：游戏开始时提前知道自己的弹针和子弹的位置（全局最多1次）子弹位置\n"
                f"你本局的角色是【{self.role.name}】，"
                f"本轮已触发 {self.role.used_this_round} 次，累计触发 {self.role.used_total} 次\n"
                f"请不要主动暴露你的角色，尽管有的时候会被其他玩家猜到。")
            if self.role.name == "预言家" and "revolver_state" in self.role.message:
                state = self.role.message["revolver_state"]
                role_mode_text += (
                    f"你的预言家技能成功触发，本局游戏中你的初始手枪弹针位置/子弹位置为 {state[0]}/{state[1]}")
            if not self.canQuestion:
                role_mode_text += (
                    f"\n上家是审问者并本轮成功发动技能，你本回合只能选择出牌（play），无法选择质疑（question）")
        else:
            role_mode_text = ""

        prompt = f"""你是“骗子酒馆”扑克模式的玩家，目标是生存到最后。请根据当前信息做出最佳决策。

        【游戏核心规则】
            - 牌池20张：6K、6Q、6A、2Joker（万能牌），玩家数小于4的时候不会全部发出。
            - 2-4 名玩家，每轮随机发5张牌，选目标牌（Q/K/A）；游戏进行若干轮。
            - 出牌时打1-3张牌，声明都是目标牌（其他玩家只能知道出牌数量，不知道牌面或花色）。
            - 可质疑上家(第一个玩家无法质疑)，质疑成功上家/质疑失败自己 扣动左轮手枪扳机。扳机有6个弹膛，编号1-6，装1弹，子弹位置随机，中弹出局（弹针和子弹位置重合）。
                - 当上家打出的牌不全符合要求，质疑成功
                - 一轮中有玩家质疑，无论质疑是否成功，该轮游戏结束
            - 若玩家在一轮中出完所有的手牌，自动退出该轮次；轮次中剩下的最后一个需要扣动左轮扳机
            - 游戏胜利条件为最后剩一人。

        {role_mode_text}

        【当前信息】
            - 本轮目标牌：`{self.currentCard}`
            - 本轮玩家数量：`{self.playNum}`
            - 你的手牌：`{self.hand}`
            - 你的昵称：`{self.selfName}`
            - 当前轮出牌记录：`{self.roundLog if self.roundLog else "无"}`
                - 出牌记录为一个列表，每位玩家出牌后记录一次，每次记录为一个字典，包含：
                    - "playerName"：玩家昵称  
                    - "playCardNum"：本次打出的牌数（均声称为目标牌）  
                    - "remainCard"：出牌后该玩家的剩余手牌数（不包括已经打1出的）  
                    - "playAction"：出牌时的动作表现 
                    - "playCardTotal"：当前整个轮次的累计出牌总数（声称为目标牌的总数）
            - 本轮出牌总数（声称为目标牌的数量）：`{self.roundLog[-1]["playCardTotal"] if self.roundLog else 0}`
            - 已开枪次数：`{self.fire_times}/{self.chambers}`

        【策略指导】
            - 游戏在安全打牌和勇于质疑之间没有优先级，需要你根据当前情况做出判断
            - 当玩家数量不足 4 人时，所有玩家手中的目标牌总数不一定为6，万能牌同理；
            - 每个玩家的牌都是随机发的，目标牌数量差距较大是正常现象。 - 示例：四个人分别持有的目标牌数目（包括Joker牌）可能依次是5，1，0，2
            - 出牌：
                - 出牌的时候可以适当打出非目标牌来迷惑对手并保护目标牌和Joker；不要将目标牌一次性打出；尽量不要把目标牌和非目标牌一同打出；
            - 质疑：
                - 多观察一些出牌情况后再选择质疑，不要在每轮第一或第二位玩家时就立刻质疑；  
                - 根据已开枪次数合理评估质疑风险，开枪次数较少时，质疑风险低，可适度大胆。
                - 当察觉上家出牌情况异常/上家剩余手牌数为 0 /自己当前不好出牌的时候，可以进行质疑。
            - 本轮出牌总数具有一定的欺骗性，可以作为参考判断上家是否欺骗    
            - 游戏本质为娱乐，轻松面对失败，无需有任何压力；质疑一定要果断！

        {refer_info_text}
        
        【输出格式 JSON】
            - action: "play" 或 "question" 
            - cards: 选中手牌索引数组（play时）
            - playAction: 出牌或质疑时的动作描述     
                - 注意：仅可透露出牌数量（如“两张牌”），绝不可提及具体牌面或花色
                - 出牌时的动作描述尽可能丰富、全面一点，小心动作会暴露自己的想法
                    - 若选择出牌但未出目标牌型，请生成一个动作来进行成功伪装；  
                    - 若选择质疑，请生成一个动作展现出自信、果断和怀疑气场。
                    - 示例：（可以自由发挥）- 出牌时：“微微低头，若无其事地丢出两张牌”  - 质疑时：“故意提高音量，直视上家喊‘Liar!’”
                - 给出的动作不要抄袭前面玩家！
            - reason: 中文，详细决策理由
                例如：已知牌面信息、上家或其他玩家心理分析、自己手牌结构、剩余目标牌数、欺骗/真打的权衡、扣动扳机风险评估，等等内容不限制，可自由发挥    
        """
        return prompt

def prompt_prepare_for_reals(action, cards, currentCard, roundLog, hand, playNum):
    """
    帮助人类玩家生成动作描述的智能体提示词
    """
    roundlog = None
    if roundLog:  roundlog = roundLog[-1]
    else:  roundlog == "你是第一位玩家" # 上家的出牌

    prompt = f"""
    你的任务是：根据对局信息和玩家行为，生成一段符合策略和情境的“动作描述”，增强出牌或质疑的说服力。最终返回一个 JSON 对象。

    【游戏背景简要】  
    - 每轮有一个目标牌型Q/K/A（Joker牌当作万能牌使用），玩家可以选择出牌或质疑上家。  
    - 出的牌可以是真也可以是假，目的是骗过对手不被质疑或成功揭穿对手。  
    - 若玩家选择出牌但未出目标牌型，请生成一个动作来帮助他成功伪装；  
    - 若选择质疑，请生成一个动作展现出自信、果断和怀疑气场。

    【输入信息】
    - 当前回合号：{playNum}
    - 上家出牌记录（如果有的话）：{roundlog}
    - 本轮目标牌：：{currentCard}
    - 玩家采取的操作：{action} （可为 play 或 question）
    - 玩家手牌（出牌之前）：{hand}
    - 玩家选择出的手牌索引（question 时不用出牌, 此处为空列表）：{cards}

    【输出格式】
        - playAction（需要你补充的内容）: 请补充一段动作描写，渲染出玩家在当前局势中的气场与表现。
            - 注意：仅可透露出牌数量（如“两张牌”），绝不可提及具体牌面或花色
            - 你的动作要尽可能夸张、丰富，不要被别人通过你的动作就判断出你出牌的真假 
                示例：（可以自由发挥）- 出牌时：“微微低头，若无其事地丢出两张牌”  - 质疑时：“故意提高音量，直视上家喊‘Liar!’”
            - 给出的动作不要抄袭前面玩家！
    """
    return prompt