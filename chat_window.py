from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, 
                           QHBoxLayout, QLabel, QComboBox, QScrollArea, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QFont, QPalette, QColor, QTextCursor, QBrush, QImage, QPixmap
from llama_chat_manager import LlamaChatManager
from voice_chat_manager import VoiceChatManager
import os
from pydub import AudioSegment
from pydub.playback import play

class MessageBubble(QFrame):
    def __init__(self, text, is_user=True, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        
        # 设置气泡样式
        if is_user:
            style = """
                QFrame {
                    background-color: #DCF8C6;
                    border-radius: 10px;
                    padding: 8px;
                }
                QLabel {
                    background-color: transparent;
                    color: #000000;
                }
            """
        else:
            style = """
                QFrame {
                    background-color: #E8E8E8;
                    border-radius: 10px;
                    padding: 8px;
                }
                QLabel {
                    background-color: transparent;
                    color: #000000;
                }
            """
        self.setStyleSheet(style)
        
        # 创建布局
        layout = QHBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)  # 减小内边距
        layout.setSpacing(0)
        
        # 创建消息文本
        message = QLabel(text)
        message.setWordWrap(True)
        message.setFont(QFont("微软雅黑", 10))
        
        # 设置标签的大小策略
        message.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Minimum
        )
        
        # 设置最大宽度
        message.setMaximumWidth(300)  # 减小最大宽度
        
        # 根据发送者调整对齐方式
        if is_user:
            message.setAlignment(Qt.AlignmentFlag.AlignRight)  # 文本右对齐
            layout.addWidget(message)
        else:
            message.setAlignment(Qt.AlignmentFlag.AlignLeft)  # 文本左对齐
            layout.addWidget(message)
            
        self.setLayout(layout)
        
        # 设置气泡的大小策略
        self.setSizePolicy(
            QSizePolicy.Policy.Fixed,  # 改为 Fixed
            QSizePolicy.Policy.Minimum
        )

class CustomChatHistory(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #F0F0F0;
                border: 1px solid #CCCCCC;
                border-radius: 15px;
                padding: 10px;
            }
        """)

class ChatWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.chat_manager = LlamaChatManager()
        self.voice_manager = VoiceChatManager()
        self.is_recording = False
        self.current_music = None  # 当前播放的音乐
        self.music_list = []  # 音乐列表
        self.is_playing = False  # 音乐播放状态
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('智能宠物聊天')
        self.setGeometry(400, 400, 600, 800)
        
        # 设置背景图片
        background_image = QImage("background/panda_back.jpg")
        palette = self.palette()
        palette.setBrush(QPalette.ColorRole.Window, 
                        QBrush(background_image.scaled(
                            self.size(),
                            Qt.AspectRatioMode.IgnoreAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )))
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        
        # 设置样式
        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(76, 175, 80, 0.9);
                color: white;
                border-radius: 15px;
                padding: 8px 15px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(69, 160, 73, 0.9);
            }
            QPushButton:pressed {
                background-color: rgba(61, 139, 64, 0.9);
            }
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.9);
                border: 2px solid rgba(204, 204, 204, 0.9);
                border-radius: 15px;
                padding: 8px 15px;
                font-size: 14px;
            }
            QComboBox {
                background-color: rgba(255, 255, 255, 0.9);
                border: 2px solid rgba(204, 204, 204, 0.9);
                border-radius: 15px;
                padding: 5px 15px;
                min-width: 100px;
            }
            QLabel {
                color: #333333;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题区域
        # title_container = QWidget()
        # title_container.setStyleSheet("""
        #     QWidget {
        #         background-color: rgba(255, 255, 255, 0.7);
        #         border-radius: 15px;
        #         padding: 10px;
        #     }
        # """)
        # title_layout = QHBoxLayout(title_container)
        # title = QLabel("智能宠物聊天")
        # title.setFont(QFont("微软雅黑", 16, QFont.Weight.Bold))
        # title_layout.addWidget(title)
        # title_layout.addStretch()
        # layout.addWidget(title_container)
        
        # 聊天模式选择区域
        mode_container = QWidget()
        mode_container.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.7);
                border-radius: 15px;
                padding: 10px;
            }
        """)
        mode_layout = QHBoxLayout(mode_container)
        
        # 左侧聊天模式
        chat_mode_widget = QWidget()
        chat_mode_layout = QHBoxLayout(chat_mode_widget)
        mode_label = QLabel("聊天模式:")
        mode_label.setFont(QFont("微软雅黑", 10))
        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["文字聊天", "语音聊天"])
        self.mode_selector.currentIndexChanged.connect(self.change_chat_mode)
        chat_mode_layout.addWidget(mode_label)
        chat_mode_layout.addWidget(self.mode_selector)
        
        # 右侧音乐播放器
        music_widget = QWidget()
        music_layout = QHBoxLayout(music_widget)
        music_layout.setContentsMargins(5, 0, 5, 0)  # 调整边距
        
        # 音乐标签
        music_label = QLabel("脑波音乐:")
        music_label.setFont(QFont("微软雅黑", 10))
        music_layout.addWidget(music_label)
        
        # 音乐选择下拉框
        self.music_selector = QComboBox()
        self.music_selector.setStyleSheet("""
            QComboBox {
                min-width: 150px;
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        self.load_music_list()  # 加载音乐列表
        
        # 播放/暂停按钮
        self.play_button = QPushButton('▶')
        self.play_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(76, 175, 80, 0.9);
                color: white;
                border-radius: 15px;
                min-width: 30px;
                min-height: 30px;
                font-size: 16px;
                font-weight: bold;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: rgba(69, 160, 73, 0.9);
            }
        """)
        self.play_button.clicked.connect(self.toggle_music)
        
        music_layout.addWidget(self.music_selector)
        music_layout.addWidget(self.play_button)
        
        # 将两个部分添加到mode_layout
        mode_layout.addWidget(chat_mode_widget)
        mode_layout.addStretch(1)
        mode_layout.addWidget(music_widget)
        
        layout.addWidget(mode_container)
        
        # 聊天记录显示区域
        self.messages_area = QWidget()
        self.messages_area.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.0);  /* 修改为半透明 */
                border-radius: 15px;
            }
        """)
        self.messages_layout = QVBoxLayout(self.messages_area)
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.messages_layout.setSpacing(8)
        self.messages_layout.setContentsMargins(10, 10, 10, 10)
        
        scroll = QScrollArea()
        scroll.setWidget(self.messages_area)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
                border-radius: 15px;
            }
            QScrollArea > QWidget {
                background: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
            QScrollBar:vertical {
                background-color: rgba(240, 240, 240, 0.3);
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(204, 204, 204, 0.5);
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        layout.addWidget(scroll)
        
        # 输入区域容器
        input_container = QFrame()
        input_container.setObjectName("input_container")
        input_layout = QVBoxLayout(input_container)
        
        # 文字输入区域
        self.text_input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入消息...")
        self.input_field.returnPressed.connect(self.send_text_message)
        self.send_button = QPushButton('发送')
        self.send_button.clicked.connect(self.send_text_message)
        self.text_input_layout.addWidget(self.input_field)
        self.text_input_layout.addWidget(self.send_button)
        input_layout.addLayout(self.text_input_layout)
        
        # 语音输入区域
        self.voice_input_layout = QHBoxLayout()
        self.record_button = QPushButton('按住说话')
        self.record_button.setCheckable(True)
        self.record_button.pressed.connect(self.start_recording)
        self.record_button.released.connect(self.stop_recording)
        self.voice_status = QLabel("准备就绪")
        self.voice_status.setStyleSheet("color: #666666;")
        self.voice_input_layout.addWidget(self.record_button)
        self.voice_input_layout.addWidget(self.voice_status)
        input_layout.addLayout(self.voice_input_layout)
        
        layout.addWidget(input_container)
        
        # 默认隐藏语音输入
        self.toggle_input_mode(0)
        
        self.setLayout(layout)

    def add_message(self, text, is_user=True):
        """添加新消息气泡"""
        bubble = MessageBubble(text, is_user)
        
        # 创建容器来控制气泡的对齐
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        if is_user:
            container_layout.addStretch(1)  # 添加弹性空间
            container_layout.addWidget(bubble)
            container_layout.setContentsMargins(60, 0, 10, 0)  # 调整右边距
        else:
            container_layout.addWidget(bubble)
            container_layout.addStretch(1)  # 添加弹性空间
            container_layout.setContentsMargins(10, 0, 60, 0)  # 调整左边距
        
        self.messages_layout.addWidget(container)
        
        # 滚动到底部
        QTimer.singleShot(100, lambda: self.scroll_to_bottom())

    def scroll_to_bottom(self):
        """滚动到最新消息"""
        scrollbar = self.findChild(QScrollArea).verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def change_chat_mode(self, index):
        """切换聊天模式"""
        self.toggle_input_mode(index)
    
    def toggle_input_mode(self, mode_index):
        """切换输入模式的UI"""
        if mode_index == 0:  # 文字模式
            for i in range(self.text_input_layout.count()):
                item = self.text_input_layout.itemAt(i).widget()
                if item:
                    item.show()
            
            for i in range(self.voice_input_layout.count()):
                item = self.voice_input_layout.itemAt(i).widget()
                if item:
                    item.hide()
        else:  # 语音模式
            for i in range(self.text_input_layout.count()):
                item = self.text_input_layout.itemAt(i).widget()
                if item:
                    item.hide()
            
            for i in range(self.voice_input_layout.count()):
                item = self.voice_input_layout.itemAt(i).widget()
                if item:
                    item.show()
    
    def send_text_message(self):
        """发送文字消息"""
        try:
            message = self.input_field.text().strip()
            if message:
                # 显示用户消息
                self.add_message(message, True)
                
                # 获取模型回应
                response = self.chat_manager.get_response(message)
                if response:  # 确保有响应
                    self.add_message(response, False)
                else:
                    self.add_message("抱歉，我现在无法回应。", False)
                
                self.input_field.clear()
        except Exception as e:
            print(f"发送消息时出错: {str(e)}")
            self.add_message("消息发送失败，请重试。", False)
    
    def start_recording(self):
        """开始录音"""
        if self.voice_manager.start_recording():
            self.is_recording = True
            self.voice_status.setText("正在录音...")
            self.record_button.setText("松开结束")
    
    def stop_recording(self):
        """停止录音并处理语音"""
        if self.is_recording:
            self.is_recording = False
            self.voice_status.setText("处理中...")
            self.record_button.setText("按住说话")
            
            # 停止录音并获取录音文件
            audio_file = self.voice_manager.stop_recording()
            if audio_file and os.path.exists(audio_file):
                # 语音转文字
                text = self.voice_manager.speech_to_text(audio_file)
                if text:
                    # 显示用户消息
                    self.add_message(text, True)
                    
                    # 获取模型回应
                    response = self.chat_manager.get_response(text)
                    self.add_message(response, False)
                    
                    # 文字转语音并播放
                    speech_file = self.voice_manager.text_to_speech(response)
                    if speech_file:
                        QTimer.singleShot(100, lambda: self.voice_manager.play_audio(speech_file))
                    
                    self.voice_status.setText("准备就绪")
                else:
                    self.voice_status.setText("未能识别语音")
                    QTimer.singleShot(2000, lambda: self.voice_status.setText("准备就绪"))
            else:
                self.voice_status.setText("录音失败")
                QTimer.singleShot(2000, lambda: self.voice_status.setText("准备就绪"))
    
    def get_ai_response(self, message):
        # 简单的关键词匹配回复系统
        responses = {
            "你好": "你好呀！我是你的桌面小伙伴~",
            "再见": "下次再聊哦~",
            "名字": "我是你的桌面小宠物，你可以给我起个名字~",
            "天气": "今天天气不错呢！适合出去玩~",
            "心情": "和你聊天让我很开心！",
            "无聊": "要不我们来玩个游戏？",
            "困": "需要我给你讲个故事吗？",
            "忙": "工作要记得休息哦，我会一直陪着你~"
        }
        
        for key, response in responses.items():
            if key in message:
                return response
            
        return "我在听呢，继续说~"

    def resizeEvent(self, event):
        """窗口大小改变时重新设置背景图片"""
        super().resizeEvent(event)
        background_image = QImage("background/panda_back.jpg")
        palette = self.palette()
        palette.setBrush(QPalette.ColorRole.Window,
                        QBrush(background_image.scaled(
                            self.size(),
                            Qt.AspectRatioMode.IgnoreAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )))
        self.setPalette(palette)

    def load_music_list(self):
        """加载音乐列表"""
        music_dir = "music"  # 音乐文件夹
        
        # 如果音乐文件夹不存在，创建它
        if not os.path.exists(music_dir):
            os.makedirs(music_dir)
            print(f"创建音乐文件夹: {music_dir}")
            print("请将MP3文件放入music文件夹中")
            self.music_selector.addItem("未找到音乐文件")
            return
        
        # 获取所有MP3文件
        music_files = [f for f in os.listdir(music_dir) if f.endswith('.mp3')]
        
        if not music_files:
            print("music文件夹中没有找到MP3文件")
            self.music_selector.addItem("未找到音乐文件")
            return
        
        # 添加音乐文件到选择器
        self.music_list = music_files
        self.music_selector.addItems(self.music_list)
        print(f"已加载 {len(self.music_list)} 个音乐文件")

    def toggle_music(self):
        """切换音乐播放状态"""
        if not self.is_playing:
            self.play_music()
        else:
            self.stop_music()

    def play_music(self):
        """播放音乐"""
        try:
            if not self.current_music:
                music_file = os.path.join("music", self.music_selector.currentText())
                if os.path.exists(music_file):
                    self.current_music = AudioSegment.from_mp3(music_file)
                    play(self.current_music)
                    self.is_playing = True
                    self.play_button.setText('⏸')
        except Exception as e:
            print(f"播放音乐时出错: {str(e)}")

    def stop_music(self):
        """停止音乐"""
        try:
            if self.current_music:
                # 这里需要实现停止播放的逻辑
                self.current_music = None
                self.is_playing = False
                self.play_button.setText('▶')
        except Exception as e:
            print(f"停止音乐时出错: {str(e)}") 