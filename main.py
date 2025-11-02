import sys
import os
import time
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QFileDialog, QMessageBox, QFrame, QSystemTrayIcon, 
                             QMenu, QAction, QGroupBox)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor

# 解决Windows高DPI显示问题
if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)


class WorkerSignals(QObject):
    """工作线程信号"""
    update_count = pyqtSignal(int)
    update_last_read = pyqtSignal(str)
    update_runtime = pyqtSignal(str)
    update_countdown = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal()


class HDDKeepAliveApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("硬盘保活工具")
        self.setMinimumSize(480, 600)
        self.resize(480, 600)
        
        # 设置窗口图标
        self.set_icon()
        
        # 状态变量
        self.running = False
        self.thread = None
        self.signals = WorkerSignals()
        
        # 连接信号
        self.signals.update_count.connect(self.on_update_count)
        self.signals.update_last_read.connect(self.on_update_last_read)
        self.signals.update_runtime.connect(self.on_update_runtime)
        self.signals.update_countdown.connect(self.on_update_countdown)
        self.signals.error.connect(self.on_error)
        self.signals.finished.connect(self.on_finished)
        
        # 初始化UI
        self.init_ui()
        
        # 加载样式表
        self.load_stylesheet()
        
        # 初始化系统托盘
        self.init_tray()

    def init_ui(self):
        """初始化用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = QLabel("硬盘保活工具")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("Microsoft YaHei UI", 16, QFont.Bold)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # 文件选择区域
        file_group = QGroupBox("文件设置")
        file_group.setObjectName("groupBox")
        file_layout = QVBoxLayout()
        file_layout.setSpacing(8)
        file_layout.setContentsMargins(0, 0, 0, 0)
        
        file_label = QLabel("目标文件路径:")
        file_label.setObjectName("label")
        file_layout.addWidget(file_label)
        
        file_input_layout = QHBoxLayout()
        self.file_entry = QLineEdit()
        self.file_entry.setObjectName("lineEdit")
        self.file_entry.setPlaceholderText("请选择要保活的硬盘文件...")
        file_input_layout.addWidget(self.file_entry)
        
        self.choose_button = QPushButton("浏览")
        self.choose_button.setObjectName("browseButton")
        self.choose_button.setFixedWidth(100)
        self.choose_button.clicked.connect(self.choose_file)
        file_input_layout.addWidget(self.choose_button)
        
        file_layout.addLayout(file_input_layout)
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # 参数设置区域
        params_group = QGroupBox("运行参数")
        params_group.setObjectName("groupBox")
        params_layout = QVBoxLayout()
        params_layout.setSpacing(8)
        params_layout.setContentsMargins(0, 0, 0, 0)
        
        # 读取间隔
        interval_layout = QHBoxLayout()
        interval_label = QLabel("读取间隔（秒）:")
        interval_label.setObjectName("label")
        interval_label.setFixedWidth(130)
        interval_layout.addWidget(interval_label)
        
        self.interval_entry = QLineEdit("60")
        self.interval_entry.setObjectName("lineEdit")
        self.interval_entry.setFixedWidth(120)
        interval_layout.addWidget(self.interval_entry)
        interval_layout.addStretch()
        params_layout.addLayout(interval_layout)
        
        # 运行时间
        duration_layout = QHBoxLayout()
        duration_label = QLabel("总运行时间（分钟）:")
        duration_label.setObjectName("label")
        duration_label.setFixedWidth(130)
        duration_layout.addWidget(duration_label)
        
        self.duration_entry = QLineEdit("0")
        self.duration_entry.setObjectName("lineEdit")
        self.duration_entry.setFixedWidth(120)
        duration_layout.addWidget(self.duration_entry)
        
        duration_hint = QLabel("(0为无限)")
        duration_hint.setObjectName("hint")
        duration_layout.addWidget(duration_hint)
        duration_layout.addStretch()
        params_layout.addLayout(duration_layout)
        
        params_group.setLayout(params_layout)
        main_layout.addWidget(params_group)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        self.start_button = QPushButton("开始运行")
        self.start_button.setObjectName("startButton")
        self.start_button.setFixedSize(200, 40)
        self.start_button.clicked.connect(self.start)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("停止运行")
        self.stop_button.setObjectName("stopButton")
        self.stop_button.setFixedSize(200, 40)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop)
        button_layout.addWidget(self.stop_button)
        
        main_layout.addLayout(button_layout)
        
        # 状态显示区域
        status_group = QGroupBox("运行状态")
        status_group.setObjectName("statusGroup")
        status_layout = QVBoxLayout()
        status_layout.setSpacing(10)
        status_layout.setContentsMargins(0, 0, 0, 0)
        
        # 状态指示器
        status_indicator_layout = QHBoxLayout()
        self.status_dot = QLabel("●")
        self.status_dot.setObjectName("statusDot")
        self.status_dot.setStyleSheet("color: #b2bec3; font-size: 16px;")
        status_indicator_layout.addWidget(self.status_dot)
        
        self.status_label = QLabel("未运行")
        self.status_label.setObjectName("statusText")
        status_indicator_layout.addWidget(self.status_label)
        status_indicator_layout.addStretch()
        status_layout.addLayout(status_indicator_layout)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        status_layout.addWidget(line)
        
        # 详细信息
        self.count_label = QLabel("读取次数: 0")
        self.count_label.setObjectName("infoLabel")
        status_layout.addWidget(self.count_label)
        
        self.runtime_label = QLabel("运行时间: 00:00:00")
        self.runtime_label.setObjectName("infoLabel")
        status_layout.addWidget(self.runtime_label)
        
        self.countdown_label = QLabel("下次读取: --")
        self.countdown_label.setObjectName("infoLabel")
        status_layout.addWidget(self.countdown_label)
        
        self.last_read_label = QLabel("最后读取: --")
        self.last_read_label.setObjectName("infoLabel")
        status_layout.addWidget(self.last_read_label)
        
        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)
        
        main_layout.addStretch()

    def load_stylesheet(self):
        """加载样式表"""
        qss_path = os.path.join(os.path.dirname(__file__), "styles.qss")
        if os.path.exists(qss_path):
            with open(qss_path, 'r', encoding='utf-8') as f:
                self.setStyleSheet(f.read())
        else:
            # 使用内置样式
            self.setStyleSheet(self.get_default_stylesheet())

    def get_default_stylesheet(self):
        """获取默认样式表"""
        return """
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #f8f9fa, stop:1 #e9ecef);
            }
            
            QWidget {
                font-family: "Microsoft YaHei UI", "Segoe UI", "微软雅黑", sans-serif;
            }
            
            #title {
                color: #1a1a2e;
                padding: 8px;
                font-weight: 600;
            }
            
            QGroupBox {
                font-size: 12px;
                font-weight: 600;
                color: #2c3e50;
                border: 1px solid #dfe4ea;
                border-radius: 8px;
                margin-top: 0px;
                padding: 25px 15px 15px 15px;
                background-color: white;
            }
            
            QGroupBox::title {
                subcontrol-origin: padding;
                subcontrol-position: top left;
                left: 10px;
                top: 8px;
                padding: 0;
                background-color: transparent;
            }
            
            #statusGroup {
                background-color: white;
                border: 1px solid #74b9ff;
                padding: 25px 15px 18px 15px;
            }
            
            #label {
                color: #2c3e50;
                font-size: 12px;
                font-weight: 600;
                padding: 3px 0;
            }
            
            #hint {
                color: #636e72;
                font-size: 10px;
                font-style: italic;
            }
            
            #infoLabel {
                color: #2d3436;
                font-size: 12px;
                padding: 6px 8px;
                line-height: 1.5;
                min-height: 24px;
            }
            
            QLineEdit {
                border: 1px solid #dfe6e9;
                border-radius: 5px;
                padding: 8px 10px;
                font-size: 12px;
                background-color: white;
                color: #2d3436;
            }
            
            QLineEdit:hover {
                border: 1px solid #b2bec3;
            }
            
            QLineEdit:focus {
                border: 1px solid #0984e3;
            }
            
            QLineEdit:disabled {
                background-color: #f1f3f5;
                color: #868e96;
                border: 1px solid #dfe6e9;
            }
            
            QPushButton {
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 600;
            }
            
            #browseButton {
                background-color: #0984e3;
                color: white;
                min-height: 32px;
            }
            
            #browseButton:hover {
                background-color: #0770c4;
            }
            
            #browseButton:disabled {
                background-color: #b2bec3;
                color: #dfe6e9;
            }
            
            #startButton {
                background-color: #00b894;
                color: white;
                font-size: 13px;
            }
            
            #startButton:hover {
                background-color: #00a383;
            }
            
            #startButton:disabled {
                background-color: #b2bec3;
                color: #dfe6e9;
            }
            
            #stopButton {
                background-color: #d63031;
                color: white;
                font-size: 13px;
            }
            
            #stopButton:hover {
                background-color: #c0282a;
            }
            
            #stopButton:disabled {
                background-color: #b2bec3;
                color: #dfe6e9;
            }
            
            #statusText {
                color: #2c3e50;
                font-size: 13px;
                font-weight: 600;
                min-height: 24px;
                line-height: 1.5;
            }
        """

    def init_tray(self):
        """初始化系统托盘"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)
            
            # 设置托盘图标
            icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
            if os.path.exists(icon_path):
                self.tray_icon.setIcon(QIcon(icon_path))
            else:
                self.tray_icon.setIcon(self.style().standardIcon(self.style().SP_DriveHDIcon))
            
            # 创建托盘菜单
            tray_menu = QMenu()
            
            show_action = QAction("显示主窗口", self)
            show_action.triggered.connect(self.show_normal)
            tray_menu.addAction(show_action)
            
            tray_menu.addSeparator()
            
            quit_action = QAction("退出", self)
            quit_action.triggered.connect(self.quit_application)
            tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self.on_tray_activated)
            self.tray_icon.show()
            
            self.tray_icon.setToolTip("硬盘保活工具")

    def on_tray_activated(self, reason):
        """托盘图标点击事件"""
        if reason == QSystemTrayIcon.Trigger:
            self.show_normal()

    def show_normal(self):
        """显示并激活窗口"""
        self.show()
        self.activateWindow()

    def choose_file(self):
        """选择文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择硬盘文件", 
            "", 
            "所有文件 (*.*)"
        )
        if file_path:
            self.file_entry.setText(file_path)

    def start(self):
        """开始运行"""
        file_path = self.file_entry.text().strip()
        if not file_path or not os.path.exists(file_path):
            QMessageBox.critical(self, "错误", "请选择一个有效的文件路径！")
            return

        try:
            interval = int(self.interval_entry.text())
            duration = int(self.duration_entry.text())
            if interval <= 0:
                raise ValueError("间隔必须大于0")
        except ValueError as e:
            QMessageBox.critical(self, "错误", "请输入有效的数字！\n间隔必须大于0秒。")
            return

        self.running = True
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.file_entry.setEnabled(False)
        self.interval_entry.setEnabled(False)
        self.duration_entry.setEnabled(False)
        self.choose_button.setEnabled(False)
        
        # 更新状态显示
        self.status_label.setText("运行中")
        self.status_dot.setStyleSheet("color: #00b894; font-size: 16px;")
        self.count_label.setText("读取次数: 0")
        self.runtime_label.setText("运行时间: 00:00:00")
        self.countdown_label.setText("下次读取: 准备中...")
        self.last_read_label.setText("最后读取: --")
        
        # 更新托盘提示
        if hasattr(self, 'tray_icon'):
            self.tray_icon.setToolTip("硬盘保活工具 - 运行中")

        # 启动工作线程
        self.thread = threading.Thread(
            target=self.run_task, 
            args=(file_path, interval, duration)
        )
        self.thread.daemon = True
        self.thread.start()

    def run_task(self, file_path, interval, duration):
        """运行任务（在独立线程中）"""
        start_time = time.time()
        count = 0

        while self.running:
            try:
                # 读取文件
                with open(file_path, "rb") as f:
                    f.read(1)
                count += 1
                
                # 更新读取次数
                self.signals.update_count.emit(count)
                
                # 更新最后读取时间
                current_time = time.strftime('%H:%M:%S')
                self.signals.update_last_read.emit(current_time)
                
            except Exception as e:
                self.signals.error.emit(str(e))
                return

            # 检查运行时间
            if duration > 0 and (time.time() - start_time) > duration * 60:
                break

            # 倒计时间隔
            for i in range(interval, 0, -1):
                if not self.running:
                    break
                
                # 更新运行时间
                elapsed_time = int(time.time() - start_time)
                hours = elapsed_time // 3600
                minutes = (elapsed_time % 3600) // 60
                seconds = elapsed_time % 60
                self.signals.update_runtime.emit(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
                
                # 更新倒计时
                self.signals.update_countdown.emit(f"{i} 秒")
                
                time.sleep(1)

        self.signals.finished.emit()

    def stop(self):
        """停止运行"""
        self.running = False

    def on_update_count(self, count):
        """更新读取次数"""
        self.count_label.setText(f"读取次数: {count}")

    def on_update_last_read(self, time_str):
        """更新最后读取时间"""
        self.last_read_label.setText(f"最后读取: {time_str}")

    def on_update_runtime(self, time_str):
        """更新运行时间"""
        self.runtime_label.setText(f"运行时间: {time_str}")

    def on_update_countdown(self, countdown_str):
        """更新倒计时"""
        self.countdown_label.setText(f"下次读取: {countdown_str}")

    def on_error(self, error_msg):
        """处理错误"""
        self.status_label.setText("错误")
        self.status_dot.setStyleSheet("color: #d63031; font-size: 16px;")
        QMessageBox.critical(self, "读取错误", f"读取文件时出错:\n{error_msg}")
        self.on_finished()

    def on_finished(self):
        """任务完成"""
        self.running = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.file_entry.setEnabled(True)
        self.interval_entry.setEnabled(True)
        self.duration_entry.setEnabled(True)
        self.choose_button.setEnabled(True)
        
        self.status_label.setText("已停止")
        self.status_dot.setStyleSheet("color: #b2bec3; font-size: 16px;")
        self.countdown_label.setText("下次读取: --")
        
        # 更新托盘提示
        if hasattr(self, 'tray_icon'):
            self.tray_icon.setToolTip("硬盘保活工具 - 已停止")

    def set_icon(self):
        """设置窗口图标"""
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
            else:
                # 使用PNG图标
                png_path = os.path.join(os.path.dirname(__file__), "icon.png")
                if os.path.exists(png_path):
                    self.setWindowIcon(QIcon(png_path))
        except Exception:
            pass

    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.running:
            reply = QMessageBox.question(
                self,
                '确认退出',
                '任务正在运行中，确定要退出吗？\n点击"最小化到托盘"可以最小化到系统托盘继续运行。',
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Yes:
                self.quit_application()
            elif reply == QMessageBox.No:
                event.ignore()
                self.hide()
            else:
                event.ignore()
        else:
            event.accept()

    def quit_application(self):
        """退出应用程序"""
        if self.running:
            self.stop()
            time.sleep(0.5)  # 等待线程结束
        
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
        
        QApplication.quit()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("硬盘保活工具")
    app.setStyle("Fusion")  # 使用Fusion风格获得更现代的外观
    
    window = HDDKeepAliveApp()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
