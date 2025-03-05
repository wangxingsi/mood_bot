import toml
import math
import logging

# 配置日志
with open("environment.toml") as f:
    env = toml.load(f)

logging.basicConfig(
    level=logging.INFO if env["debug"].get("enable_log", False) else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("debug.log", mode='a'),
        logging.StreamHandler()
    ]
)

def calculate_distance(current, preset):
    """计算PAD三维空间距离"""
    try:
        p = float(current.get("P", 0))
        a = float(current.get("A", 0))
        d = float(current.get("D", 0))
        
        return math.sqrt(
            (p - preset["P"])**2 +
            (a - preset["A"])**2 +
            (d - preset["D"])**2
        )
    except Exception as e:
        logging.error(f"距离计算错误：{str(e)}")
        return float("inf")

def main():
    """主分析函数"""
    try:
        # 读取当前情绪
        with open("mood/current_mood.toml") as f:
            current = toml.load(f)
        
        # 读取预设情绪
        with open("mood/preset.toml") as f:
            presets = toml.load(f)
        
        # 计算最近情绪
        min_distance = float("inf")
        closest_mood = "default"
        
        for mood, values in presets.items():
            dist = calculate_distance(current, values)
            logging.info(f"与【{mood}】的距离：{round(dist, 4)}")  # 调试日志
            
            if dist < min_distance:
                min_distance = dist
                closest_mood = mood
        
        print(closest_mood)
    
    except FileNotFoundError as e:
        logging.error(f"文件未找到：{str(e)}")
    except Exception as e:
        logging.error(f"PAD系统错误：{str(e)}")

if __name__ == "__main__":
    main()
