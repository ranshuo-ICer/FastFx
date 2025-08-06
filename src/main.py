import json
import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox
import keyboard
import pystray
from PIL import Image, ImageDraw, ImageFont
import winreg
import logging
from monitorcontrol import get_monitors
# ========== 初始化日志 ==========
logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(format='[%(asctime)s: %(levelname)s]: %(message)s')
logging.info("FastFx started")

# ========== 配置路径 ==========
# 获取程序所在目录
if getattr(sys, 'frozen', False):
    # 运行在打包后的环境
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # 运行在开发环境
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "keymap.json")
fn_pressed = True
icon = None


# ========== 加载配置 ==========
def load_config():
    if not os.path.exists(CONFIG_PATH):
        logging.info("创建默认配置文件")
        default_config = {
            "f1": "volume mute",
            "f2": "volume down",
            "f3": "volume up",
            "f4": "play/pause",
            "f5": "next track",
            "f6": "previous track",
            "f7": "",
            "f8": "",
            "f9": "",
            "f10": "",
            "f11": "brightness down",
            "f12": "brightness up"
        }
        with open(CONFIG_PATH, "w") as f:
            json.dump(default_config, f, indent=4)
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


keymap = load_config()

def change_brightness(direction):
    try:
        monitors = get_monitors()
        for monitor in monitors:
            with monitor:
                current = monitor.get_luminance()
                if direction == "up":
                    monitor.set_luminance(min(current + 10, 100))
                elif direction == "down":
                    monitor.set_luminance(max(current - 10, 0))
                logging.info(f"Brightness changed to {monitor.get_luminance()}")
    except Exception as e:
        logging.error(f"Failed to change brightness: {e}")

# ========== 模式切换 ==========
def toggle_fn_mode():
    global fn_pressed
    fn_pressed = not fn_pressed
    logging.info(f"[状态切换] Fn 模式: {fn_pressed}")
    update_icon(fn_pressed)


def set_fn(state):
    global fn_pressed
    fn_pressed = state
    update_icon(state)


# ========== 拦截并处理按键 ==========
def handle_key(key, prtsc_held):
    try:
        logging.info(f"[按键] key={key}, Fn模式={fn_pressed}, PrtSc按下={prtsc_held}")
        if prtsc_held:
            keyboard.send(key)
        elif fn_pressed:
            command = keymap.get(key)
            if command:
                logging.info(f"执行命令: {command}")
                if command.startswith("lunch"):
                    subprocess.Popen(command[6:])
                elif command == "brightness up":
                    change_brightness("up")
                elif command == "brightness down":
                    change_brightness("down")
                else:
                    keyboard.send(command)
            else:
                keyboard.send(key)
        else:
            keyboard.send(key)
    except Exception as e:
        logging.error(e)


def register_keys():
    for key in keymap.keys():
        keyboard.add_hotkey(key, lambda k=key: handle_key(k, False), suppress=True)
        keyboard.add_hotkey("print_screen+" + key, lambda k=key: handle_key(k, True), suppress=True)


# ========== 托盘图标相关 ==========
def update_icon(fn_mode):
    if icon:
        icon.icon = create_icon("M" if fn_mode else "Fn")


def create_icon(text="M"):
    try:
        # 从文件夹中加载图像
        # 获取资源路径
        if getattr(sys, 'frozen', False):
            # 运行在打包后的环境
            script_dir = sys._MEIPASS
        else:
            # 运行在开发环境
            script_dir = os.path.dirname(os.path.abspath(__file__))
        bg_path = os.path.join(script_dir, "background.png")
        bg = Image.open(bg_path)
        bg = bg.resize((64, 64))
    except Exception as e:
        logging.error(f"加载图标失败: {e}")
        # 若加载失败，使用默认的创建方式
        bg = Image.new('RGB', (64, 64), "white")
    d = ImageDraw.Draw(bg)
    d.rectangle([(0, 0), (63, 63)])
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except IOError:
        font = ImageFont.load_default()
    # d.text((), text, fill="white", font=font, align="center")
    # 计算文本的位置
    # 使用getbbox替代textsize获取文本尺寸
    bbox = font.getbbox(text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (64 - text_width) // 2
    text_y = (64 - text_height - 10) // 2
    # 将字母绘制到背景上
    d.text((text_x, text_y), text, fill="white", font=font, align="center")
    return bg


# ========== 配置 GUI ==========
def show_gui():
    def save_and_exit():
        new_config = {}
        for i, key in enumerate(keymap.keys()):
            val = entries[i].get()
            new_config[key] = val
        with open(CONFIG_PATH, "w") as f:
            json.dump(new_config, f, indent=4)
        messagebox.showinfo("保存成功", "配置已保存，重启程序生效")
        window.destroy()

    window = tk.Tk()
    window.title("功能键配置")
    entries = []
    for i, (key, val) in enumerate(keymap.items()):
        tk.Label(window, text=key.upper()).grid(row=i, column=0, padx=5, pady=5)
        entry = tk.Entry(window, width=30)
        entry.insert(0, val)
        entry.grid(row=i, column=1, padx=5, pady=5)
        entries.append(entry)
    tk.Button(window, text="保存配置", command=save_and_exit).grid(row=len(keymap), column=0, columnspan=2, pady=10)
    window.mainloop()


# ========== 开机启动相关 ==========

def is_in_startup():
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_READ
        )
        value, _ = winreg.QueryValueEx(key, "FastFx")
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False
    except Exception as e:
        logging.error(f"检查启动项失败: {e}")
        return False

def add_to_startup():
    exe_path = sys.executable
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        # 设置启动项名称为FastFx
        winreg.SetValueEx(key, "FastFx", 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)
        logging.info("添加开机启动成功")
    except Exception as e:
        logging.error(f"添加启动项失败: {e}")

def remove_from_startup():
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_ALL_ACCESS
        )
        winreg.DeleteValue(key, "FastFx")
        winreg.CloseKey(key)
        logging.info("移除开机启动成功")
    except Exception as e:
        logging.error(f"移除启动项失败: {e}")


# ========== 托盘菜单 ==========
def on_quit(icon, item):
    icon.stop()


def on_open(icon, item):
    threading.Thread(target=show_gui).start()


def on_toggle(icon, item):
    toggle_fn_mode()

def on_startup_toggle(icon, item):
    if is_in_startup():
        remove_from_startup()
    else:
        add_to_startup()
    # 更新菜单项状态
    icon.menu = create_menu()


def create_menu():
    startup_status = "开启" if is_in_startup() else "关闭"
    return pystray.Menu(
        pystray.MenuItem("打开配置", on_open),
        pystray.MenuItem("切换Fn模式", on_toggle),
        pystray.MenuItem(f"开机自启动: {startup_status}", on_startup_toggle),
        pystray.MenuItem("退出", on_quit)
    )

def run_tray():
    global icon
    icon = pystray.Icon("FastFx")
    icon.icon = create_icon("M" if fn_pressed else "Fn")
    icon.menu = create_menu()
    icon.run()


# ========== 主程序入口 ==========
if __name__ == "__main__":
    keyboard.block_key("print_screen")  # 阻止系统截图
    keyboard.add_hotkey("print_screen+esc", toggle_fn_mode, suppress=True)
    threading.Thread(target=register_keys, daemon=True).start()
    run_tray()
