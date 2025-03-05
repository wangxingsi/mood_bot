import toml
import subprocess
import logging
import time
import signal
import sys
from pathlib import Path

def initialize_system():
    """系统初始化"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("debug.log", mode='a')
        ]
    )
    
    # 确保情绪文件存在
    mood_file = Path("./mood/current_mood.toml")
    if not mood_file.exists():
        logging.info("初始化情绪文件")
        mood_file.parent.mkdir(exist_ok=True)  # 确保目录存在
        mood_file.write_text(toml.dumps({"P": 0.0, "A": 0.0, "D": 0.0}))

def emotion_analysis():
    """执行情绪分析"""
    result = subprocess.run(
        ["python", "pad_system.py"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        logging.error(f"情绪分析失败: {result.stderr}")
        return None
    
    return result.stdout.strip()

def get_reply_config(mood_label):
    """获取对应的回复库配置"""
    with open("mood/config.toml") as f:
        config = toml.load(f)
    
    default = config["default"]["reply_lib"]
    reply_config = config.get(mood_label, config["default"])
    reply_lib = reply_config["reply_lib"]
    
    if not Path(reply_lib).exists():
        logging.warning(f"配置文件 {reply_lib} 不存在，使用默认库")
        return default
    return reply_lib

def main_loop():
    """主循环控制器"""
    def handler(signum, frame):
        logging.info("收到终止信号，安全关闭...")
        sys.exit(0)
        
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

    while True:
        try:
            # 情绪分析
            mood_label = emotion_analysis()
            if not mood_label:
                time.sleep(1)
                continue
            
            logging.info(f"当前情绪状态: {mood_label}")
            
            # 获取回复库路径
            reply_lib = get_reply_config(mood_label)
            logging.info(f"使用回复库: {reply_lib}")
            
            # 启动交互会话（传递情绪标签）
            process = subprocess.Popen(
                ["python", "-u", "mood_bot.py", reply_lib, mood_label],
                stdin=sys.stdin,
                stdout=sys.stdout,
                stderr=sys.stderr,
                bufsize=1,
                universal_newlines=True
            )
            
            # 等待进程结束
            exit_code = process.wait()
            
            # 处理退出代码
            if exit_code == 100:
                logging.info("准备新一轮交互...")
                time.sleep(0.5)
            elif exit_code == 0:
                logging.info("用户主动终止会话")
                break
            else:
                logging.warning(f"异常退出码: {exit_code}")
                time.sleep(1)

        except KeyboardInterrupt:
            logging.info("系统安全关闭")
            break
        except Exception as e:
            logging.error(f"系统异常: {str(e)}")
            time.sleep(1)

if __name__ == "__main__":
    initialize_system()
    main_loop()
