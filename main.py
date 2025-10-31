import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import time
import os
import sys

# 解决Windows高DPI显示模糊问题
if sys.platform == 'win32':
    try:
        from ctypes import windll
        # 设置DPI感知，让Windows知道这是一个高DPI感知的应用
        windll.shcore.SetProcessDpiAwareness(1)  # 1 = PROCESS_SYSTEM_DPI_AWARE
    except:
        try:
            # 兼容Windows 8.1及以下版本
            windll.user32.SetProcessDPIAware()
        except:
            pass

class HDDKeepAliveApp:
    def __init__(self, master):
        self.master = master
        self.master.title("硬盘保活工具")
        self.master.geometry("550x520")
        self.master.minsize(500, 480)  # 设置最小窗口尺寸
        self.master.resizable(True, True)  # 允许调整窗口大小
        
        # 设置窗口图标
        self.set_icon()

        # 状态变量
        self.running = False
        self.thread = None

        # 文件路径
        tk.Label(master, text="目标文件路径:").pack(pady=5)
        self.file_entry = tk.Entry(master, width=50)
        self.file_entry.pack(padx=15)
        tk.Button(master, text="选择文件", command=self.choose_file).pack(pady=3)

        # 读取间隔（秒）
        tk.Label(master, text="读取间隔（秒）:").pack(pady=5)
        self.interval_entry = tk.Entry(master, width=10)
        self.interval_entry.insert(0, "60")
        self.interval_entry.pack()

        # 运行时间（分钟）
        tk.Label(master, text="总运行时间（分钟，0为无限）:").pack(pady=5)
        self.duration_entry = tk.Entry(master, width=10)
        self.duration_entry.insert(0, "0")
        self.duration_entry.pack()

        # 启动/停止按钮
        self.start_button = tk.Button(master, text="开始运行", width=15, command=self.start)
        self.start_button.pack(pady=10)
        self.stop_button = tk.Button(master, text="停止运行", width=15, state="disabled", command=self.stop)
        self.stop_button.pack(pady=5)

        # 信息显示区域
        info_frame = tk.Frame(master, relief=tk.SUNKEN, borderwidth=2, padx=15, pady=15)
        info_frame.pack(pady=15, padx=20, fill=tk.BOTH, expand=True)

        # 状态显示
        self.status_label = tk.Label(info_frame, text="状态: 未运行", fg="gray", font=("微软雅黑", 10, "bold"), anchor="w")
        self.status_label.pack(fill=tk.X, pady=3)

        # 读取次数显示
        self.count_label = tk.Label(info_frame, text="读取次数: 0", fg="black", font=("微软雅黑", 9), anchor="w")
        self.count_label.pack(fill=tk.X, pady=3)

        # 运行时间显示
        self.runtime_label = tk.Label(info_frame, text="运行时间: 00:00:00", fg="black", font=("微软雅黑", 9), anchor="w")
        self.runtime_label.pack(fill=tk.X, pady=3)

        # 下次读取倒计时
        self.countdown_label = tk.Label(info_frame, text="下次读取: --", fg="black", font=("微软雅黑", 9), anchor="w")
        self.countdown_label.pack(fill=tk.X, pady=3)

        # 最后读取时间
        self.last_read_label = tk.Label(info_frame, text="最后读取: --", fg="black", font=("微软雅黑", 9), anchor="w")
        self.last_read_label.pack(fill=tk.X, pady=3)

    def choose_file(self):
        path = filedialog.askopenfilename(title="选择硬盘文件")
        if path:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, path)

    def start(self):
        file_path = self.file_entry.get().strip()
        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("错误", "请选择一个有效的文件路径！")
            return

        try:
            interval = int(self.interval_entry.get())
            duration = int(self.duration_entry.get())
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字！")
            return

        self.running = True
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.status_label.config(text="状态: 运行中", fg="green")
        self.count_label.config(text="读取次数: 0")
        self.runtime_label.config(text="运行时间: 00:00:00")
        self.countdown_label.config(text="下次读取: 准备中...")
        self.last_read_label.config(text="最后读取: --")

        self.thread = threading.Thread(target=self.run_task, args=(file_path, interval, duration))
        self.thread.daemon = True
        self.thread.start()

    def run_task(self, file_path, interval, duration):
        start_time = time.time()
        count = 0

        while self.running:
            try:
                # 读取文件
                with open(file_path, "rb") as f:
                    f.read(1)
                count += 1
                
                # 更新读取次数
                self.count_label.config(text=f"读取次数: {count}")
                
                # 更新最后读取时间
                current_time = time.strftime('%H:%M:%S')
                self.last_read_label.config(text=f"最后读取: {current_time}")
                
            except Exception as e:
                self.status_label.config(text=f"状态: 错误", fg="red")
                messagebox.showerror("读取错误", f"读取文件时出错: {e}")
                self.stop()
                return

            # 检查运行时间
            if duration > 0 and (time.time() - start_time) > duration * 60:
                break

            # 倒计时间隔，并显示倒计时
            for i in range(interval, 0, -1):
                if not self.running:
                    break
                
                # 更新运行时间
                elapsed_time = int(time.time() - start_time)
                hours = elapsed_time // 3600
                minutes = (elapsed_time % 3600) // 60
                seconds = elapsed_time % 60
                self.runtime_label.config(text=f"运行时间: {hours:02d}:{minutes:02d}:{seconds:02d}")
                
                # 更新倒计时
                self.countdown_label.config(text=f"下次读取: {i} 秒")
                
                time.sleep(1)

        self.stop()

    def stop(self):
        self.running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.status_label.config(text="状态: 已停止", fg="gray")
        self.countdown_label.config(text="下次读取: --")

    def set_icon(self):
        """设置窗口图标和任务栏图标"""
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
            if os.path.exists(icon_path):
                # Windows下使用.ico文件设置图标
                self.master.iconbitmap(icon_path)
            else:
                # 如果图标文件不存在，尝试使用PNG图标
                png_path = os.path.join(os.path.dirname(__file__), "icon.png")
                if os.path.exists(png_path):
                    from PIL import Image, ImageTk
                    icon_image = Image.open(png_path)
                    icon_photo = ImageTk.PhotoImage(icon_image)
                    self.master.iconphoto(True, icon_photo)
        except Exception as e:
            # 如果图标加载失败，静默处理，使用默认图标
            pass


if __name__ == "__main__":
    root = tk.Tk()
    app = HDDKeepAliveApp(root)
    root.mainloop()
