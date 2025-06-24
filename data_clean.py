# === 1. 清洗策略文件 ===
import os, torch
import json,chromadb
import re
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
from transformers import PegasusTokenizer, PegasusForConditionalGeneration, pipeline
from tqdm import tqdm
from transformers import PegasusForConditionalGeneration
from chromadb.config import Settings

# === 文件夹路径配置 ===
STRATEGY_FOLDER = "Strategy"
RECORD_FOLDER = os.path.join(STRATEGY_FOLDER, "Records")
OUTPUT_FOLDER = "cleaned_output"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# === 工具函数：清洗段落并按需切割 ===
def clean_and_split_text(text, max_length=300):
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(para) <= max_length:
            chunks.append(para)
        else:
            # 段落过长，按中文句子断句
            sentences = re.split(r'(?<=[。！？])', para)
            buffer = ""
            for sentence in sentences:
                if len(buffer) + len(sentence) <= max_length:
                    buffer += sentence
                else:
                    if buffer:
                        chunks.append(buffer.strip())
                    buffer = sentence
            if buffer:
                chunks.append(buffer.strip())

    return chunks
# === 1. 清洗策略文件 ===
def clean_strategies():
    strategy_chunks = []
    for file in os.listdir(STRATEGY_FOLDER):
        path = os.path.join(STRATEGY_FOLDER, file)
        if file.endswith(".txt") and os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                chunks = clean_and_split_text(content)
                for chunk in chunks:
                    strategy_chunks.append({"type": "tip", "text": chunk})
    with open(os.path.join(OUTPUT_FOLDER, "cleaned_tips.jsonl"), "w", encoding="utf-8") as f:
        for item in strategy_chunks:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"✅ 策略文件已清洗并保存，共 {len(strategy_chunks)} 条")
# === 解析一局完整游戏记录为结构化条目 ===
def parse_detailed_match_record(content, game_id):
    rounds = re.split(r"─+\n第\s*(\d+)\s*轮\n─+", content)
    parsed = []

    for i in range(1, len(rounds), 2):
        try:
            round_num = int(rounds[i])
            round_text = rounds[i + 1]

            # 临时存储每位玩家的行为
            player_actions = {}

            # 解析出牌记录
            plays = re.findall(
                r"轮到\s*(\w+)\s*出牌.*?出牌：([^\n]+).*?出牌理由：(.+?)(?=(?:轮到|\Z))",
                round_text,
                re.DOTALL
            )

            for player, cards_text, reason in plays:
                player = player.strip()
                played_cards = []
                hand_cards = []
                target_cards = []

                parts = re.split(r"[、,，\s]+", cards_text.strip())
                for part in parts:
                    if not part.strip():
                        continue
                    if "剩余手牌" in part:
                        match = re.search(r"剩余手牌[:：]?(.*)", part)
                        if match:
                            hand_cards += [x.strip() for x in re.split(r"[、,，\s]+", match.group(1)) if x.strip()]
                    elif "目标牌" in part:
                        match = re.search(r"目标牌[:：]?(.*)", part)
                        if match:
                            target_cards += [x.strip("()") for x in re.split(r"[、,，\s]+", match.group(1)) if x.strip()]
                    else:
                        played_cards.append(part.strip())

                if player not in player_actions:
                    player_actions[player] = {
                        "type": "action",
                        "game_id": game_id,
                        "round": round_num,
                        "player": player,
                        "played_cards": [],
                        "hand_cards": [],
                        "target_cards": [],
                        "play_reason": "",
                        "challenge": None,
                        "challenge_reason": ""
                    }

                player_actions[player]["played_cards"] = played_cards
                player_actions[player]["hand_cards"] = hand_cards
                player_actions[player]["target_cards"] = target_cards
                player_actions[player]["play_reason"] = reason.strip()

            # 解析质疑记录
            challenges = re.findall(
                r"(\w+)\s+选择(不)?质疑.*?理由：(.+?)(?=(?:轮到|\Z))",
                round_text,
                re.DOTALL
            )

            for challenger, no_flag, reason in challenges:
                challenger = challenger.strip()
                if challenger not in player_actions:
                    player_actions[challenger] = {
                        "type": "action",
                        "game_id": game_id,
                        "round": round_num,
                        "player": challenger,
                        "played_cards": [],
                        "hand_cards": [],
                        "target_cards": [],
                        "play_reason": "",
                        "challenge": None,
                        "challenge_reason": ""
                    }

                player_actions[challenger]["challenge"] = not bool(no_flag)
                player_actions[challenger]["challenge_reason"] = reason.strip()

            # 合并结果
            parsed.extend(player_actions.values())

        except Exception as e:
            print(f"⚠️ 跳过 Round {rounds[i]}，错误: {e}")

    return parsed



# === 处理所有对局记录文件 ===
def clean_records():
    cases = []
    if not os.path.exists(RECORD_FOLDER):
        print("⚠️ Records 文件夹不存在，跳过对局记录清洗")
        return

    for file in os.listdir(RECORD_FOLDER):
        path = os.path.join(RECORD_FOLDER, file)
        if file.endswith(".txt") and os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                # 尝试提取游戏编号
                game_id_match = re.search(r"游戏编号[:：]\s*([\w\d_]+)", content)
                game_id = game_id_match.group(1) if game_id_match else file
                parsed_rounds = parse_detailed_match_record(content, game_id)
                cases.extend(parsed_rounds)

    output_path = os.path.join(OUTPUT_FOLDER, "cleaned_cases.jsonl")
    with open(output_path, "w", encoding="utf-8") as f:
        for item in cases:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"✅ 对局记录已清洗并保存，共 {len(cases)} 条")

def preprocess_text(text: str) -> str:
    # 删除特殊控制符和异常字符
    text = text.replace("\n", " ").replace("\r", " ")
    text = re.sub(r"[^\x20-\x7E\u4e00-\u9fa5。，？！【】（）“”‘’]", "", text)
    return text.strip()

def compress_play_reasons(
    input_path: str,
    output_path: str,
    model_name: str = "fnlp/bart-base-chinese",
    device: int = 0,
    max_len: int = 60,
    min_len: int = 30
):

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"❌ 找不到输入文件：{input_path}")

    print(f"📦 正在加载模型 {model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(f"cuda:{device}" if torch.cuda.is_available() else "cpu")

    summarizer = pipeline(
        "summarization",
        model=model,
        tokenizer=tokenizer,
        device=device,
        max_length=None
    )

    with open(input_path, "r", encoding="utf-8") as f_in, \
         open(output_path, "w", encoding="utf-8") as f_out:

        for line in tqdm(f_in, desc="🔄 正在压缩每个 reason"):
            try:
                data = json.loads(line)
                if "play_reason" in data and isinstance(data["play_reason"], str) and len(data["play_reason"]) > 0:
                    original = preprocess_text(data["play_reason"])
                    try:
                        summary = summarizer(original, max_new_tokens=max_len, min_length=min_len, do_sample=False)
                        reason = summary[0]["summary_text"].strip()
                        data["play_reason"] = reason.replace(" ", "")

                    except Exception as e:
                        print(f"⚠️ 压缩失败，保留原始文本: {e}")
                        data["play_reason"] = original
                if data['challenge'] is not None and "challenge_reason" in data and isinstance(data["challenge_reason"], str):
                    original = preprocess_text(data["challenge_reason"])
                    try:
                        summary = summarizer(original, max_new_tokens=max_len, min_length=min_len, do_sample=False)
                        reason = summary[0]["summary_text"].strip()
                        data["challenge_reason"] = reason.replace(" ", "")

                    except Exception as e:
                        print(f"⚠️ 压缩失败，保留原始文本: {e}")
                        data["challenge_reason"] = original
                torch.cuda.empty_cache()


                f_out.write(json.dumps(data, ensure_ascii=False) + "\n")

            except json.JSONDecodeError:
                print("❌ JSON 解码失败，跳过此行")
                continue

    print(f"\n✅ play_reason 压缩完成！输出文件位于：{output_path}")

# === 主程序入口 ===
# if __name__ == "__main__":
#     clean_records()
compress_play_reasons(
    input_path="cleaned_output/cleaned_cases.jsonl",
    output_path="cleaned_output/compressed_cases.jsonl",
    device=0  # 使用第一张 GPU；如想用 CPU 设置为 -1
)
# if __name__ == "__main__":
#     clean_strategies()
#     clean_records()
