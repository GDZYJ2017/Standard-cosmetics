"""
标准审查助手 - 系统托盘服务
开机自启，后台常驻，浏览器随时访问 http://localhost:8000
"""
import os
import sys
import threading
import webbrowser
import time
import urllib.request
import logging

# 确保项目路径
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(PROJECT_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)

# 日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(PROJECT_DIR, 'server.log'), encoding='utf-8'),
    ]
)
logger = logging.getLogger(__name__)


def start_server():
    """在后台线程启动 FastAPI 服务"""
    import uvicorn
    from main import app
    uvicorn.run(app, host='0.0.0.0', port=8000, log_level='warning', access_log=False)


def wait_for_server(timeout=20):
    """等待服务器启动就绪"""
    for i in range(timeout):
        time.sleep(1)
        try:
            urllib.request.urlopen('http://localhost:8000/', timeout=2)
            return True
        except Exception:
            pass
    return False


def is_already_running():
    """检测后端服务是否已经在运行"""
    try:
        urllib.request.urlopen('http://localhost:8000/', timeout=2)
        return True
    except Exception:
        return False


def main():
    # 如果服务已经在运行，直接打开浏览器并退出
    if is_already_running():
        logger.info("服务已在运行，打开浏览器...")
        webbrowser.open('http://localhost:8000')
        return

    # 创建数据目录
    for d in ['data/uploads', 'data/standards', 'data/reports']:
        os.makedirs(os.path.join(PROJECT_DIR, d), exist_ok=True)

    logger.info("标准审查助手 - 托盘服务启动中...")

    # 启动服务器线程
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # 等待就绪
    if wait_for_server():
        logger.info("后端服务启动成功 (http://localhost:8000)")
        # 首次启动自动打开浏览器
        webbrowser.open('http://localhost:8000')
    else:
        logger.error("后端服务启动失败")

    # 创建托盘图标
    try:
        from pystray import Icon, Menu, MenuItem
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        logger.error("缺少依赖: pystray 或 pillow，请运行 pip install pystray pillow")
        webbrowser.open('http://localhost:8000')
        input("按回车退出...")
        return

    # 生成托盘图标
    def create_icon():
        img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # 蓝色圆角矩形
        draw.rounded_rectangle([4, 4, 60, 60], radius=14, fill=(26, 86, 219, 255))
        # 白色文字
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 32)
        except Exception:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), "标", font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text(((64 - tw) / 2, (64 - th) / 2 - 2), "标", fill='white', font=font)
        return img

    def on_open(icon, item):
        webbrowser.open('http://localhost:8000')

    def on_quit(icon, item):
        logger.info("托盘服务退出")
        icon.stop()

    menu = Menu(
        MenuItem('打开标准审查助手', on_open, default=True),
        MenuItem('地址: http://localhost:8000', on_open),
        Menu.SEPARATOR,
        MenuItem('退出', on_quit),
    )

    icon = Icon('标准审查助手', create_icon(), '标准审查助手', menu)
    logger.info("系统托盘已就绪")
    icon.run()


if __name__ == '__main__':
    main()
