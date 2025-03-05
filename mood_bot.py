import toml
import re
import random
import logging
import sys

def configure_logging():
    """隐藏控制台日志的配置"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        file_handler = logging.FileHandler("debug.log", mode='a')
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

configure_logging()

# 核心功能函数
def load_foundation():
    """加载基础配置"""
    with open("keyword/foundation.toml") as f:
        return toml.load(f)

def get_current_mood():
    """读取当前情绪值"""
    with open("./mood/current_mood.toml") as f:
        return toml.load(f)

def update_mood(keyword_values):
    """更新情绪值并持久化"""
    current_mood = get_current_mood()
    for _, values in keyword_values.items():
        for dim in ["P", "A", "D"]:
            current_mood[dim] = round(current_mood.get(dim, 0.0) + values.get(dim, 0.0), 4)
    with open("./mood/current_mood.toml", "w") as f:
        toml.dump(current_mood, f)

# 主交互逻辑
def main(reply_lib, mood_label):  # 新增 mood_label 参数
    """单次交互流程"""
    foundation = load_foundation()
    
    try:
        # 加载回复库
        with open(reply_lib) as f:
            replies = toml.load(f)
    except FileNotFoundError:
        logging.error(f"回复库文件缺失: {reply_lib}")
        return 2  # 错误退出码

    # 加载并过滤关键词
    with open("keyword/keyword.toml") as f:
        all_keywords = toml.load(f)["keywords"]
    
    # 根据情绪状态过滤关键词
    filtered_keywords = {
        pattern: data 
        for pattern, data in all_keywords.items()
        if data.get("mood", "default") in [mood_label, "any", "default"]
    }

    try:
        # 用户输入处理
        user_input = input("你：").strip()
        
        # 退出指令处理
        if user_input.lower() in ["exit", "退出", "bye"]:
            print(f"{foundation['assistant_name']}：{random.choice(replies['farewell'])}", flush=True)
            return 0  # 正常退出码

        # 关键词匹配（带情绪权重加成）
        weight = 1.5 if "最" in user_input else 1.2 if any(c in user_input for c in ["特别", "极其"]) else 1.0
        matched = {}
        
        for pattern, data in filtered_keywords.items():
            try:
                if re.search(pattern, user_input, re.IGNORECASE):
                    impact = {k: float(v)*weight for k, v in data["impact"].items()}
                    matched[pattern] = {
                        "replies": data["replies"],
                        "impact": impact
                    }
            except Exception as e:
                logging.error(f"关键词处理错误：{pattern} - {str(e)}")

        # 生成回复（优先当前情绪关键词）
        if matched:
            # 按影响值排序
            sorted_keys = sorted(
                matched.keys(),
                key=lambda k: sum(abs(v) for v in matched[k]["impact"].values()),
                reverse=True
            )
            max_key = sorted_keys[0]
            reply = random.choice(matched[max_key]["replies"])
            logging.info(f"匹配到关键词：{max_key} 权重：{weight}")
        else:
            reply = random.choice(replies["greetings"])
            logging.info("未匹配到关键词")

        print(f"{foundation['assistant_name']}：{reply.format(**foundation)}", flush=True)

        # 更新情绪值
        if matched:
            update_mood({k: v["impact"] for k, v in matched.items()})
            logging.info(f"更新后的情绪值：{get_current_mood()}")

        return 100  # 重启指令码

    except Exception as e:
        logging.error(f"对话异常：{str(e)}")
        return 1  # 异常退出码

# 入口点
if __name__ == "__main__":
    if len(sys.argv) < 3:  # 修改参数检查
        print("错误：参数不足，需要回复库路径和情绪标签", flush=True)
        sys.exit(1)
    
    exit_code = main(sys.argv[1], sys.argv[2])  # 接收第二个参数
    sys.exit(exit_code)
