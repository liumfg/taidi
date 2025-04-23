import sys
from PyQt6.QtWidgets import QApplication, QWidget, QSystemTrayIcon, QMenu, QStyle, QLabel
from PyQt6.QtGui import QIcon, QPixmap, QPalette, QBrush, QImage
from PyQt6.QtCore import Qt, QPoint, QTimer, QPropertyAnimation, QEasingCurve, QRect
import os
import random
from chat_window import ChatWindow
import time
from llama_chat_manager import LlamaChatManager

class DesktopPet(QWidget):
    def __init__(self):
        super().__init__()
        self.loadAnimations()
        self.initUI()
        self.dragging = False
        self.offset = QPoint()
        self.setupAnimations()
        self.current_sequence = None
        self.click_count = 0  # 记录点击次数
        self.last_click_time = 0  # 记录上次点击时间
        self.chat_manager = LlamaChatManager()
        
    def loadAnimations(self):
        """加载所有动画帧"""
        self.animations = {
            'idle': self.loadAnimationFrames('01-Idle/01-Idle'),
            'idle_blink': self.loadAnimationFrames('01-Idle/02-Idle_Blink'),
            'walk': self.loadAnimationFrames('03-Walk/01-Walk'),
            'walk_happy': self.loadAnimationFrames('03-Walk/02-Walk_Happy'),
            'run': self.loadAnimationFrames('04-Run'),
            'jump_up': self.loadAnimationFrames('06-Jump/01-Jump_Up'),
            'jump_fall': self.loadAnimationFrames('06-Jump/02-Jump_Fall'),
            'jump_throw': self.loadAnimationFrames('06-Jump/03-Jump_Throw'),
            'hurt': self.loadAnimationFrames('07-Hurt/01-Hurt'),
            'hurt_dizzy': self.loadAnimationFrames('07-Hurt/02-Hurt_Dizzy'),
            'throw': self.loadAnimationFrames('02-Throw'),
            'dead': self.loadAnimationFrames('08-Dead')
        }
        self.current_animation = 'idle'
        self.current_frame = 0
        
    def loadAnimationFrames(self, folder):
        """加载指定文件夹中的所有动画帧"""
        frames = []
        base_path = f'assets/Animation PNG/PANDA/NUDE/{folder}'
        try:
            files = sorted(os.listdir(base_path))
            for file in files:
                if file.endswith('.png'):
                    pixmap = QPixmap(os.path.join(base_path, file))
                    frames.append(pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation))
        except Exception as e:
            print(f"加载动画帧错误 {folder}: {e}")
        return frames

    def playSequence(self, sequence):
        """播放动作序列"""
        self.current_sequence = sequence
        self.playNextInSequence()
    
    def playNextInSequence(self):
        """播放序列中的下一个动作"""
        if not self.current_sequence:
            # 序列播放完毕，恢复到默认动画
            self.current_sequence = None
            self.playAnimation('idle')
            return
        
        # 获取并播放序列中的下一个动作
        next_action = self.current_sequence.pop(0)
        animation_name = next_action[0]
        duration = next_action[1]
        
        self.playAnimation(animation_name, False)
        QTimer.singleShot(duration, self.playNextInSequence)

    def randomAction(self):
        """随机执行一个动作或动作序列"""
        if self.dragging or self.current_sequence:
            return
            
        # 定义动作序列
        sequences = [
            # 基础动作 (30% 概率)
            ([('idle', 1500), ('idle_blink', 1000)], 0.15),
            ([('idle_blink', 1000), ('idle', 1500)], 0.15),
            
            # 走路系列 (25% 概率)
            ([('walk', 800), ('walk_happy', 1000), ('walk', 800)], 0.1),
            ([('walk_happy', 1200), ('idle', 500), ('walk', 800)], 0.1),
            ([('run', 1000), ('walk', 800), ('idle', 500)], 0.05),
            
            # 跳跃系列 (20% 概率)
            ([('jump_up', 400), ('jump_fall', 400)], 0.08),
            ([('jump_up', 400), ('jump_throw', 600), ('jump_fall', 400)], 0.07),
            ([('run', 600), ('jump_up', 400), ('jump_fall', 400)], 0.05),
            
            # 投掷系列 (15% 概率)
            ([('throw', 800), ('idle', 500)], 0.05),
            ([('run', 600), ('throw', 800), ('walk', 600)], 0.05),
            ([('jump_up', 400), ('throw', 800), ('jump_fall', 400)], 0.05),
            
            # 特殊系列 (10% 概率)
            ([('hurt', 600), ('hurt_dizzy', 1000), ('idle', 500)], 0.04),
            ([('run', 800), ('hurt', 600), ('hurt_dizzy', 800), ('idle', 500)], 0.03),
            ([('jump_up', 400), ('hurt', 600), ('dead', 1000), ('idle', 500)], 0.03)
        ]
        
        # 根据权重随机选择一个序列
        sequence = random.choices([s[0] for s in sequences],
                                weights=[s[1] for s in sequences])[0]
        self.playSequence(sequence.copy())

    def playAnimation(self, animation_name, loop=True):
        """播放指定的动画序列"""
        if animation_name in self.animations:
            self.current_animation = animation_name
            self.current_frame = 0
            
            if hasattr(self, 'anim_timer'):
                self.anim_timer.stop()
            
            self.anim_timer = QTimer(self)
            self.anim_timer.timeout.connect(self.nextFrame)
            
            # 不同动画使用不同的帧率
            frame_delays = {
                'idle': 100,
                'idle_blink': 100,
                'walk': 80,
                'walk_happy': 80,
                'run': 60,
                'jump_up': 100,
                'jump_fall': 100,
                'jump_throw': 80,
                'hurt': 100,
                'hurt_dizzy': 120,
                'throw': 80,
                'dead': 150
            }
            self.anim_timer.start(frame_delays.get(animation_name, 100))

    def nextFrame(self):
        """显示动画的下一帧"""
        if self.current_animation in self.animations:
            frames = self.animations[self.current_animation]
            if frames:
                self.current_frame = (self.current_frame + 1) % len(frames)
                self.pet_label.setPixmap(frames[self.current_frame])

    def initUI(self):
        # 设置窗口属性
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setWindowFlag(Qt.WindowType.Tool)  # 不在任务栏显示
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 创建标签来显示图片
        self.pet_label = QLabel(self)
        self.setFixedSize(100, 100)  # 设置固定大小
        self.pet_label.setFixedSize(100, 100)  # 设置标签大小
        self.pet_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # 居中对齐
        
        # 如果有动画帧，显示第一帧
        if self.animations['idle']:
            self.pet_label.setPixmap(self.animations['idle'][0])
        
        # 移动到屏幕右边
        screen = QApplication.primaryScreen().geometry()
        self.screen_rect = screen
        self.move(screen.width() - self.width() - 50,
                 screen.height() // 2 - self.height() // 2)
        
        # 创建系统托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        # 使用第一帧动画作为图标
        if self.animations['idle']:
            self.icon = QIcon(self.animations['idle'][0])
            self.tray_icon.setIcon(self.icon)
            self.setWindowIcon(self.icon)
        
        # 创建托盘菜单
        tray_menu = QMenu()
        chat_action = tray_menu.addAction('开始聊天')
        quit_action = tray_menu.addAction('退出')
        
        # 绑定事件
        chat_action.triggered.connect(self.open_chat)
        quit_action.triggered.connect(QApplication.instance().quit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        self.chat_window = None
        
        # 开始播放默认动画
        self.playAnimation('idle')
        
        # 在 initUI 方法中：
        background = QImage("background/panda_back.jpg")
        palette = self.palette()
        palette.setBrush(QPalette.ColorRole.Window, QBrush(QPixmap.fromImage(background)))
        self.setPalette(palette)
    
    def setupAnimations(self):
        # 设置随机动作定时器
        self.action_timer = QTimer(self)
        self.action_timer.timeout.connect(self.randomAction)
        self.action_timer.start(3000)
        
        # 设置位置检查定时器
        self.position_timer = QTimer(self)
        self.position_timer.timeout.connect(self.checkScreenPosition)
        self.position_timer.start(1000)  # 每秒检查一次位置

    def checkScreenPosition(self):
        """检查并响应屏幕位置"""
        pos = self.pos()
        screen = QApplication.primaryScreen().geometry()
        margin = 50  # 边缘检测范围
        
        # 如果当前没有播放序列，才检查位置
        if not self.current_sequence:
            # 靠近左边缘
            if pos.x() < margin:
                self.playSequence([('walk_happy', 800), ('jump_up', 400), ('jump_fall', 400)])
            # 靠近右边缘
            elif pos.x() > screen.width() - self.width() - margin:
                self.playSequence([('walk_happy', 800), ('jump_up', 400), ('jump_fall', 400)])
            # 靠近顶部
            elif pos.y() < margin:
                self.playSequence([('jump_up', 400), ('jump_throw', 600), ('jump_fall', 400)])
            # 靠近底部
            elif pos.y() > screen.height() - self.height() - margin:
                self.playSequence([('jump_up', 400), ('jump_fall', 400)])

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            current_time = time.time()
            
            # 记录拖动相关的信息
            self.click_pos = event.pos()
            self.dragging = False
            self.offset = event.pos()
            
            # 处理左键点击动作
            if not self.current_sequence:
                # 根据点击次数和时间间隔决定动作
                if current_time - self.last_click_time < 0.5:  # 快速点击
                    self.click_count += 1
                    if self.click_count >= 3:  # 连续快速点击3次
                        self.playSequence([('hurt', 600), ('hurt_dizzy', 1000), ('idle', 500)])
                        self.click_count = 0
                else:  # 普通点击
                    self.click_count = 1
                    # 随机选择一个点击反应动作
                    reactions = [
                        [('jump_up', 400), ('jump_fall', 400)],
                        [('throw', 800), ('idle', 500)],
                        [('walk_happy', 800), ('idle', 500)],
                    ]
                    self.playSequence(random.choice(reactions))
            
            self.last_click_time = current_time
        
        elif event.button() == Qt.MouseButton.RightButton:
            # 右键点击打开聊天窗口
            self.open_chat()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
    
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            # 如果鼠标移动距离超过阈值，则认为是拖动
            if not self.dragging and (event.pos() - self.click_pos).manhattanLength() > 3:
                self.dragging = True
            
            if self.dragging:
                new_pos = event.globalPosition().toPoint() - self.offset
                self.move(new_pos)
                # 检查新位置是否靠近屏幕边缘
                self.checkScreenPosition()

    def open_chat(self):
        if not self.chat_window:
            self.chat_window = ChatWindow()
        self.chat_window.show()

    def chat_response(self, user_input):
        """处理用户输入并生成回应"""
        response = self.chat_manager.process_input(user_input)
        
        # 根据回应类型触发相应动作
        if response.type == 'comfort':
            self.playSequence([('walk_happy', 800), ('idle_blink', 500)])
        elif response.type == 'encourage':
            self.playSequence([('jump_up', 400), ('jump_fall', 400)])
        elif response.type == 'cheer_up':
            self.playSequence([('throw', 800), ('walk_happy', 800)])

if __name__ == '__main__':
    app = QApplication(sys.argv)
    pet = DesktopPet()
    pet.show()
    sys.exit(app.exec()) 