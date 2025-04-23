import os
import wave
import pyaudio
import threading
import subprocess
import asyncio
import time
from datetime import datetime
import edge_tts
from pydub import AudioSegment
from pydub.playback import play

class VoiceChatManager:
    def __init__(self):
        # 录音配置
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.is_recording = False
        self.recording_thread = None
        
        # whisper.cpp 配置
        self.whisper_path = "whisper.cpp/main.exe"
        self.whisper_model = "models/ggml-model-whisper-base.bin"
        
        # 创建临时文件夹
        os.makedirs("temp", exist_ok=True)
    
    def start_recording(self):
        """开始录音"""
        if self.is_recording:
            return False
        
        self.is_recording = True
        self.recording_thread = threading.Thread(target=self._record_audio)
        self.recording_thread.start()
        return True
    
    def stop_recording(self):
        """停止录音"""
        if not self.is_recording:
            return None
        
        self.is_recording = False
        self.recording_thread.join()
        
        # 返回录音文件路径
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"temp/recording_{timestamp}.wav"
    
    def _record_audio(self):
        """录音线程函数"""
        p = pyaudio.PyAudio()
        
        stream = p.open(format=self.FORMAT,
                        channels=self.CHANNELS,
                        rate=self.RATE,
                        input=True,
                        frames_per_buffer=self.CHUNK)
        
        print("* 开始录音...")
        
        frames = []
        
        while self.is_recording:
            data = stream.read(self.CHUNK)
            frames.append(data)
        
        print("* 录音结束")
        
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        # 保存录音文件
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"temp/recording_{timestamp}.wav"
        
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(p.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        return filename
    
    def speech_to_text(self, audio_file):
        """使用 whisper.cpp 进行语音识别"""
        try:
            # 调用 whisper.cpp 进行语音识别
            cmd = [
                self.whisper_path,
                "-m", self.whisper_model,
                "-f", audio_file,
                "-l", "zh",  # 设置语言为中文
                "--output-txt"
            ]
            
            print(f"执行命令: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # 检查是否成功
            txt_file = f"{audio_file}.txt"
            if os.path.exists(txt_file):
                with open(txt_file, 'r', encoding='utf-8') as f:
                    text = f.read().strip()
                print(f"从文件读取识别结果: {text}")
                return text
            
            # 如果文件不存在，尝试从输出中提取
            output_lines = result.stdout.strip().split('\n')
            for line in output_lines:
                if line and not line.startswith('[') and not line.startswith('whisper_'):
                    print(f"从输出提取识别结果: {line}")
                    return line.strip()
            
            print(f"语音识别错误: {result.stderr}")
            return None
        
        except Exception as e:
            print(f"语音识别异常: {e}")
            return None
    
    async def _generate_speech(self, text, output_file):
        """使用 edge-tts 生成语音"""
        communicate = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural")
        await communicate.save(output_file)
    
    def text_to_speech(self, text, output_file=None):
        """将文字转为语音"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            output_file = f"temp/speech_{timestamp}.mp3"
        
        # 使用 asyncio 运行异步函数
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._generate_speech(text, output_file))
        finally:
            loop.close()
        
        return output_file
    
    def play_audio(self, audio_file):
        """播放音频文件"""
        try:
            print(f"开始播放音频: {audio_file}")
            
            # 加载并播放音频
            sound = AudioSegment.from_file(audio_file)
            play(sound)
            
            print(f"音频播放完成: {audio_file}")
            return True
        except Exception as e:
            print(f"播放音频时出错: {e}")
            
            # 如果pydub失败，尝试使用系统命令
            try:
                if os.name == 'nt':  # Windows
                    os.system(f'start {audio_file}')
                else:  # Linux/Mac
                    os.system(f'xdg-open {audio_file}')
                return True
            except Exception as e2:
                print(f"使用系统命令播放也失败: {e2}")
                return False 